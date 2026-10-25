import hashlib
import json
import html
from fastapi import FastAPI, HTTPException
from curl_cffi import requests
from parsel import Selector

app = FastAPI()


# -----------------------------
# HELPERS
# -----------------------------
def clean_price(price):
    try:
        if price:
            return float(str(price).replace("$", "").strip())
        return "N/A"
    except:
        return "N/A"


def clean_html_proper(raw_html):
    if not raw_html:
        return "N/A"
    try:
        from lxml import html as lxml_html
        raw_html = html.unescape(raw_html)
        tree = lxml_html.fromstring(raw_html)
        texts = tree.xpath('//p//text() | //li//text()')
        if not texts:
            texts = tree.xpath('//text()')
        return " | ".join(t.strip() for t in texts if t.strip())
    except:
        return "N/A"


def extract_category(base_product, sel):

    # 1️⃣ powerReviews
    try:
        cat = base_product.get("powerReviewsComponents", {}) \
                          .get("product", {}) \
                          .get("category_name", "")
        if cat:
            return cat.replace(" > ", "/")
    except:
        pass

    # 2️⃣ API path
    try:
        path = base_product.get("primaryCategoryPath", [])
        if path:
            return " / ".join(path)
    except:
        pass

    # 3️⃣ JSON-LD breadcrumb
    scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
    for script in scripts:
        try:
            data = json.loads(script)

            if isinstance(data, list):
                for d in data:
                    if d.get('@type') == 'BreadcrumbList':
                        items = d.get('itemListElement', [])
                        names = [i['item']['name'] for i in items if 'item' in i]
                        if names:
                            return " / ".join(names)

            elif data.get('@type') == 'BreadcrumbList':
                items = data.get('itemListElement', [])
                names = [i['item']['name'] for i in items if 'item' in i]
                if names:
                    return " / ".join(names)
        except:
            continue

    # 4️⃣ HTML fallback
    try:
        crumbs = sel.xpath('//nav[contains(@class,"breadcrumb")]//a/text()').getall()
        crumbs = [c.strip() for c in crumbs if c.strip()]
        if crumbs:
            return " / ".join(crumbs)
    except:
        pass

    return "N/A"


# -----------------------------
# CORE SCRAPER
# -----------------------------
def scrape_product(url):
    API_URL = "https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Product-updateSubscription"

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    }

    session = requests.Session()

    # LOAD PDP
    res = session.get(url, headers=headers, impersonate="chrome110")
    sel = Selector(text=res.text)

    raw = sel.xpath('//div[@class="pr-pdp-components"]/@data-pr-pdp-components').get()
    if not raw:
        raise Exception("No product data found")

    data = json.loads(html.unescape(raw))
    product_block = data.get("product", {})

    # ✅ FIXED PID
    base_pid = product_block.get("id") or product_block.get("productID")

    first_variant = product_block.get("variants", [])[0]
    base_sku = first_variant.get("page_id_variant")

    # CALL API FOR BASE PRODUCT
    base_res = session.post(API_URL, headers=headers, data={"pid": base_sku}, impersonate="chrome110")
    base_product = base_res.json().get("product", {})

    # fallback PID
    if not base_pid:
        base_pid = base_product.get("masterProduct", {}).get("ID")

    # -----------------------------
    # BASIC DATA
    # -----------------------------
    name = base_product.get("productName", "N/A")
    brand = base_product.get("brand", "N/A")

    # PRICE
    price_block = base_product.get("price") or {}
    sales = (price_block.get("sales") or {}).get("value")
    list_p = (price_block.get("list") or {}).get("value")

    sale_price = clean_price(sales)
    mrp = clean_price(list_p) if list_p else clean_price(sales)
    final_price = sale_price if sale_price != "N/A" else mrp

    # IMAGES
    images = [
        img.get("url") for img in base_product.get("images", {}).get("large", [])
        if img.get("url") and "missing" not in img.get("url").lower()
    ]

    # STOCK
    stock = base_product.get("availability", {}).get("inStock")
    if stock is None:
        messages = base_product.get("availability", {}).get("messages", [])
        stock = any("In Stock" in m for m in messages)

    # DESCRIPTION
    description = clean_html_proper(
        base_product.get("longDescription") or base_product.get("shortDescription")
    )

    # CATEGORY
    category = extract_category(base_product, sel)

    # RATINGS
    avg_rating = base_product.get("customRating", {}).get("bvAverageRating") or "N/A"
    num_rating = base_product.get("customRating", {}).get("bvReviewCount") or "N/A"
    num_rating = int(num_rating)
    avg_rating = float(avg_rating)
    if num_rating == 0:
        num_rating = "N/A"
    if avg_rating == 0.0:
        avg_rating = "N/A"

    # -----------------------------
    # VARIANTS
    # -----------------------------
    variant_ids = [v.get("page_id_variant") for v in product_block.get("variants", [])]

    variant_list = []

    for vid in variant_ids:
        api_res = session.post(API_URL, headers=headers, data={"pid": vid}, impersonate="chrome110")

        if api_res.status_code != 200:
            continue

        vdata = api_res.json().get("product", {})

        price_block = vdata.get("price") or {}
        sales = (price_block.get("sales") or {}).get("value")
        list_p = (price_block.get("list") or {}).get("value")

        v_sale = clean_price(sales)
        v_mrp = clean_price(list_p) if list_p else v_sale
        v_final = v_sale if v_sale != "N/A" else v_mrp

        # SIZE
        size = "N/A"
        if vdata.get("variationAttributes"):
            size = vdata["variationAttributes"][0].get("displayValue", "N/A")

        # STOCK
        v_stock = vdata.get("availability", {}).get("inStock")
        if v_stock is None:
            messages = vdata.get("availability", {}).get("messages", [])
            v_stock = any("In Stock" in m for m in messages)

        variant_list.append({
            "available": v_stock,
            "Price": v_final,
            "Mrp": v_mrp if v_mrp != "N/A" else "N/A",
            "size": size if size else "N/A",
            # "colour": "N/A",
            "sku": vid
        })

    # base_size = variant_list[0]["size"] if variant_list else "N/A"
    # collect all sizes
    all_sizes = [v.get("size") for v in variant_list if v.get("size") and v.get("size") != "N/A"]

    # remove duplicates while keeping order
    seen = set()
    unique_sizes = []
    for s in all_sizes:
        if s not in seen:
            seen.add(s)
            unique_sizes.append(s)

    # final size string
    base_size = " | ".join(unique_sizes) if unique_sizes else "N/A"

    # variant_price_str = " | ".join(
    #     [f"{v['size']} - {v['Price']}" for v in variant_list]
    # )

    variant_price_str = " | ".join(
        [
            f"{v['Price']}" if v['size'] == "N/A" else f"{v['size']} - {v['Price']}"
            for v in variant_list
        ]
    )

    # -----------------------------
    # FINAL RESPONSE
    # -----------------------------
    import time
    from datetime import datetime

    start_time = time.time()
    end_time = time.time()
    return {
        "request_log": {
            "requestUrl": url,
            "productId": url,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "requestId": hashlib.sha256(url.encode()).hexdigest(),
            "endpoint": "/pdp",
            "responseTimeInSec": end_time - start_time
        },
        "results": {
            "Name": name,
            "Image URL": images[0] if images else "N/A",
            "SKU": base_sku,
            "PID": base_pid,
            "IsInStock": str(stock),
            "Price Currency": "USD",
            "Sale Price": str(sale_price),
            "Final Price": str(final_price),
            # "Mrp": int(round(float(mrp))) if mrp != "N/A" else "N/A",
            "Mrp": mrp if mrp != "N/A" else "N/A",
            "Discount": "N/A",
            "Manufacturer": "N/A",
            "Brand": brand,
            "Colour": "N/A",
            "Num Ratings": num_rating,
            "Average Ratings": avg_rating,
            "Gender": "N/A",
            "Alternate Image URLs": " | ".join(images[1:]) if len(images) > 1 else "N/A",
            "Link URL": url,
            "Category": category,
            "Description": description,
            "Size": base_size,
            "Varint_Price": variant_price_str,
            "Variant_data": variant_list,
            "policy": [],
            "Other": "N/A"
        }
    }


# -----------------------------
# API ENDPOINT
# -----------------------------
@app.get("/pdp")
def scrape(url: str):
    try:
        return scrape_product(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# RUN LIKE NORMAL SCRIPT
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pet_supermarket:app", host="***HIDDEN***", port=5254, reload=True)