import json
import time
import os
import html
import re
from curl_cffi import requests
from parsel import Selector
import orjson
import db_config_1 as db
from lxml import html as lxml_html



# ============================================================
# CONFIGURATION
# ============================================================

API_URL="https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Product-updateSubscription"
REQUEST_TIMEOUT = 60
SLEEP_BETWEEN_VARIANTS = 0.5

# ============================================================
# HELPERS
# ============================================================
def normalize_size(value):
    if not value:
        return ""
    return value.replace(" ", "").lower()

def clean_html_proper(raw_html):
    if not raw_html:
        return "N/A"
    try:
        raw_html = html.unescape(raw_html)
        tree = lxml_html.fromstring(raw_html)
        texts = tree.xpath("//p//text() | //li//text()")
        if not texts:
            texts = tree.xpath("//text()")
        return " | ".join(text.strip() for text in texts if text.strip())
    except Exception:
        return "N/A"

def extract_promotions(product):
    promotion_banner_html = product.get("promotionBannerHtml", "")
    if not promotion_banner_html:
        return None
    try:
        # Parse HTML stored inside JSON
        promo_sel = Selector(text=html.unescape(promotion_banner_html))
        promotions = []
        for promo in promo_sel.xpath('//div[contains(@class, "promo-message-with-tooltip")]'):
            title = promo.xpath('.//span[contains(@class, "promo-callout-msg")]//text()').getall()
            description = promo.xpath('.//div[contains(@class, "tooltiptext")]//text()').getall()
            title = " ".join(x.strip() for x in title if x.strip()) or None
            description = " ".join(x.strip() for x in description if x.strip()) or None
            if title or description:
                promotions.append({
                    "title": title,
                    "description": description,
                    "coupon_code": None,
                    "offer_type": None,
                    "applicable_scope": None,
                    "discount_kind": None,
                    "discount_value": None,
                    "currency": None,
                    "min_spend": None,
                    "valid_from": None,
                    "valid_to": None,
                    "stackable": None,
                    "card_network": None,
                    "card_issuer": None,
                    "terms": None
                })
        return promotions or None
    except Exception as e:
        print("❌ Promotion extraction error:", e)
        return None
# ============================================================
# UPDATE STATUS
# ============================================================
def update_status_done(cursor, link_id):
    cursor.execute(f""" UPDATE {db.link_table} SET status = 'done' WHERE id = %s""",(link_id,))

# ============================================================
# FETCH PDP
# ============================================================
def fetch_pdp(url, headers):
    print("Fetching PDP...")
    try:
        response = requests.get("https://api.scrape.do/",
            params={
                "token": db.proxy_token,
                "url": url,
            },
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        print("PDP Status:", response.status_code)
        if response.status_code != 200:
            print("❌ PDP failed:", response.status_code)
            return None
        return response
    except Exception as e:
        print("❌ PDP request error:", e)
        return None

# ============================================================
# EXTRACT VARIANTS FROM PDP
# ============================================================
def get_variants_from_pdp(pdp_html):
    sel = Selector(text=pdp_html)
    variants_data = []
    scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
    for script in scripts:
        try:
            data = orjson.loads(script)
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "Product":
                        data = item
                        break
            if not isinstance(data, dict):
                continue
            if data.get("@type") != "Product":
                continue
            offers = data.get("offers", {})
            if isinstance(offers, dict):
                offer_list = offers.get("offers")
                if isinstance(offer_list, list):
                    for offer in offer_list:
                        pid = offer.get("sku")
                        referer = offer.get("url")
                        if pid and referer:
                            variants_data.append({
                                "pid": pid,
                                "referer": referer
                            })
                else:
                    pid = offers.get("sku")
                    referer = offers.get("url")
                    if pid and referer:
                        variants_data.append({
                            "pid": pid,
                            "referer": referer
                        })
            if variants_data:
                break
        except Exception:
            continue
    # FALLBACK
    if not variants_data:
        print("⚠️ No JSON-LD offers → using fallback")
        raw = sel.xpath('//div[@class="pr-pdp-components"]/@data-pr-pdp-components').get()
        if raw:
            try:
                decoded = html.unescape(raw)
                data = orjson.loads(decoded)
                product = data.get("product", {})
                referer = product.get("url", "")
                for variant in product.get("variants", []):
                    pid = variant.get("page_id_variant")
                    if pid:
                        variants_data.append({
                            "pid": pid,
                            "referer": referer
                        })
            except Exception as e:
                print("❌ Variant extraction error:", e)
    return variants_data

# ============================================================
# EXTRACT MPN FROM PDP
# ============================================================
def extract_mpn(sel):
    mpn = "N/A"
    p_url = "N/A"
    scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
    for script in scripts:
        try:
            data = orjson.loads(script)
            if isinstance(data, list):
                for item in data:
                    if item.get("@type") == "Product":
                        data = item
                        break
            if not isinstance(data, dict):
                continue
            if data.get("@type") != "Product":
                continue
            mpn = data.get("mpn", "N/A")
            offers = data.get("offers", {})
            # Nested offers
            if isinstance(offers, dict):
                inner = offers.get("offers")
                if isinstance(inner, list) and inner:
                    p_url = (inner[0].get("url") or "N/A")
                # Direct offer URL
                if p_url == "N/A":
                    p_url = ( offers.get("url") or "N/A")

            # Product URL fallback
            if p_url == "N/A":
                p_url = (data.get("url") or data.get("@id") or "N/A")
            break
        except Exception:
            continue
    return mpn, p_url

# ============================================================
# FETCH VARIANT API
# ============================================================

def fetch_variant(pid, headers):
    payload = {
        "pid": pid,
        "options": [],
        "isAutoShipSelected": "false",
        "shipment": "DTC"
    }
    try:
        # response = requests.post(
        #     API_URL,
        #     headers=headers,
        #     cookies=cookies,
        #     data=payload,
        #     verify=False
        # )
        response = requests.post(
            "https://api.scrape.do/",
            params={
                "token": db.proxy_token,
                "url": API_URL,
            },
            headers=headers,
            data=payload,
            timeout=REQUEST_TIMEOUT,
        )
        print(f"Variant {pid} status:", response.status_code)
        return response
    except Exception as e:
        print(f"❌ Variant {pid} error:", e)
        return None

# ============================================================
# EXTRACT ONE VARIANT
# ============================================================

def extract_variant_data(product,variant_id,hash_key,product_url,p_url,html_sizes_clean,mpn):
    # Verify variant
    if product.get("id") != variant_id:
        return None
    # offers & coupons
    promotions = extract_promotions(product)
    # print(f"Promotion for {variant_id}: {promotions}")
    # Convert promotion list/dict to JSON string for MySQL LONGTEXT
    coupons_and_offers = (orjson.dumps(promotions).decode("utf-8") if promotions else None)
    print(f"Promotion for {variant_id}: {coupons_and_offers}")
    # SIZE
    json_size = ""
    variation_attributes = (product.get("variationAttributes") or [])
    if variation_attributes:
        json_size = (variation_attributes[0].get("displayValue", ""))
    json_size_clean = normalize_size(json_size)
    # Only accept sizes available in PDP HTML
    if (html_sizes_clean and json_size_clean not in html_sizes_clean):
        print(f"❌ Skipping {variant_id} Size: {json_size}")
        return None
    pid = (product.get("masterProduct", {}).get("ID", ""))
    name = product.get("productName","")
    brand = product.get("brand","N/A")
    # PRICE
    price_block = product.get("price",{})
    sales_price = (price_block.get("sales") or {}).get("value")
    list_price = (price_block.get("list") or {}).get("value")
    final_price = sales_price or 0
    price = (list_price or sales_price or 0)
    sale_price = sales_price or 0
    if list_price and sales_price:
        discount = round(list_price - sales_price, 2)
    else:
        discount = "N/A"
    currency = (price_block.get("sales") or {}).get("currency", "")
    # STOCK
    messages = (product.get("availability", {}).get("messages", []))
    is_in_stock = ("TRUE" if any("In Stock" in message for message in messages) else "FALSE")
    # DESCRIPTION
    description = clean_html_proper(product.get("shortDescription",""))
    # CATEGORY
    category = (product.get("powerReviewsComponents", {}).get("product", {}).get("category_name", ""))
    category = category.replace(" > ", "/")
    # IMAGES
    images = (product.get("images", {}).get("large", []))
    valid_images = [image.get("url") for image in images if image.get("url") and "missing" not in
                    image.get("url","").lower()]
    main_image = (valid_images[0] if valid_images else "N/A")
    alt_images = (" | ".join(valid_images[1:]) if len(valid_images) > 1 else "N/A")
    # UPC
    upc = "N/A"
    pr_variants = (product.get("powerReviewsComponents", {}).get("product", {}).get("variants", []))
    for variant in pr_variants:
        if str(variant.get("page_id_variant")) == str(product.get("id")):
            upc = (variant.get("upc") or "N/A")
            break
    # RATINGS
    custom_rating = product.get("customRating",{})
    avg_rating = (custom_rating.get("bvAverageRating") or "N/A")
    num_rating = (custom_rating.get("bvReviewCount") or "N/A")
    # SKU
    sku = product.get("id")
    # LINK URL
    if sku and p_url != "N/A":
        new_link = re.sub(r"/[A-Z0-9]+\.html$", f"/{sku}.html",p_url)
    else:
        new_link = "N/A"
    # FINAL ROW
    row = (
        "Pet Supermarket",
        pid,
        name,
        "N/A",
        description,
        category,
        main_image,
        price,
        currency,
        sale_price,
        final_price,
        discount,
        "No",
        is_in_stock,
        "N/A",
        brand,
        "N/A",
        mpn,
        upc,
        sku,
        "N/A",
        "N/A",
        json_size or "N/A",
        final_price,
        alt_images,
        product_url,
        num_rating,
        avg_rating,
        hash_key,
        new_link,
        None,
        coupons_and_offers
    )
    return row


# ============================================================
# PROCESS ONE PRODUCT
# ============================================================

def process_product(link_id,url,hash_key,headers,cursor,conn):
    print("=" * 80)
    print("Processing:", url)
    print("Hash:", hash_key)
    print("=" * 80)
    # 1. FETCH PDP
    pdp_response = fetch_pdp(url, headers)
    if not pdp_response:
        print("❌ PDP fetch failed")
        return False
    # 2. SAVE PDP
    try:
        os.makedirs(db.PDP_PAGESAVE, exist_ok=True)
        file_path = os.path.join(db.PDP_PAGESAVE, f"{hash_key}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pdp_response.text)
        print("✅ PDP saved:", file_path)
    except Exception as e:
        print("❌ PDP save failed:", e)
        return False
    # 3. PARSE PDP
    try:
        sel = Selector(text=pdp_response.text)
        # MPN + original product URL
        mpn, p_url = extract_mpn(sel)
        # promotions = []
        # for promo in sel.xpath('//div[contains(@class, "promo-message-with-tooltip")]'):
        #     promotion = promo.xpath('.//span[contains(@class, "promo-callout-msg")]/text()').get()
        #     promotion_description = promo.xpath('.//div[contains(@class, "tooltiptext")]//text()').getall()
        #     promotion = promotion.strip() if promotion else None
        #     promotion_description = " ".join(x.strip() for x in promotion_description if x.strip()) or None
        #     promotions.append({
        #         "title": promotion,
        #         "description": promotion_description,
        #         "coupon_code": None,
        #         "offer_type": None,
        #         "applicable_scope": None,
        #         "discount_kind": None,
        #         "discount_value": None,
        #         "currency": None,
        #         "min_spend": None,
        #         "valid_from": None,
        #         "valid_to": None,
        #         "stackable": None,
        #         "card_network": None,
        #         "card_issuer": None,
        #         "terms": None
        #     })
        # print(promotions)
        # PDP JSON
        raw_json = sel.xpath('//div[@class="pr-pdp-components"]/@data-pr-pdp-components').get()
        if not raw_json:
            print("❌ pr-pdp-components not found")
            return False
        pdp_data = orjson.loads(html.unescape(raw_json))
        product_block = pdp_data.get("product", {})
        variants = product_block.get("variants", [])
        product_url = product_block.get("url", url)
        # HTML sizes
        html_sizes = sel.xpath('//button[contains(@class,"size-attribute")]/@data-attr-value').getall()
        html_sizes_clean = {normalize_size(size) for size in html_sizes}
        print("Variants found:", len(variants))
        # print("HTML sizes:", html_sizes_clean)
    except Exception as e:
        print("❌ PDP parsing failed:",e)
        return False
    # 4. FETCH + EXTRACT VARIANTS
    all_rows = []
    for index, variant in enumerate(variants, 1):
        variant_id = variant.get("page_id_variant")
        if not variant_id:
            continue
        print(f"\n   Variant {index}/{len(variants)}: {variant_id}")
        # Fetch variant API
        api_response = fetch_variant( variant_id, headers)
        if api_response.status_code == 500:
            continue
        if not api_response:
            print(f"❌ Failed variant: {variant_id}")
            return False
        if api_response.status_code == 403:
            print("⚠️ 403 Blocked → do not mark link done")
            return False
        if api_response.status_code != 200:
            print(f"❌ Variant {variant_id} failed: {api_response.status_code}")
            return False
        # Save variation PageSave
        variation_folder = os.path.join(db.PDP_PAGESAVE, "variation_pagesave")
        os.makedirs(variation_folder, exist_ok=True)
        file_path = os.path.join(variation_folder, f"{variant_id}.json")
        json_data = api_response.json()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        if json_data is None:
            return False
        # Extract directly from response
        product = json_data.get("product", {})
        if not product:
            print(f"❌ No product data for {variant_id}")
            continue
        row = extract_variant_data(
            product=product,
            variant_id=variant_id,
            hash_key=hash_key,
            product_url=product_url,
            p_url=p_url,
            html_sizes_clean=html_sizes_clean,
            mpn=mpn
        )

        if row:
            all_rows.append(row)
            print(f"✅ Extracted:{variant_id}")
        time.sleep(SLEEP_BETWEEN_VARIANTS)
    # ========================================================
    # 5. CHECK EXTRACTION
    # ========================================================
    if not all_rows:
        print("❌ No data extracted")
        return False
    print(f"\n✅ Total rows extracted: {len(all_rows)}")
    # ========================================================
    # 6. INSERT DATA INTO DATA TABLE
    # ========================================================
    try:
        insert_query = f"""
            INSERT IGNORE INTO {db.data_table} (
                website,
                pid,
                name,
                short_description,
                description,
                category,
                image_url,
                price,
                price_currency,
                sale_price,
                final_price,
                discount,
                is_on_sale,
                is_in_stock,
                keywords,
                brand,
                manufacturer,
                mpn,
                upc_ean,
                sku,
                colour,
                gender,
                size,
                variant_price,
                alternate_image_urls,
                link_url,
                num_ratings,
                avg_ratings,
                hash_id,
                main_url,
                size_type,
                coupons_and_offers
            )
            VALUES (
                %s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        # delivery_ETA,
        # shipping_cost,
        # return_fee,
        # tags,
        # review_summary,
        # return_policy -- , %s,%s, %s, %s, %s, %s
        # print(f"Rows to insert: {len(all_rows)}")
        # Verify placeholder count before executing
        placeholder_count = insert_query.count("%s")
        value_count = len(all_rows[0]) if all_rows else 0
        # print(f"SQL placeholders: {placeholder_count}")
        # print(f"Values per row:   {value_count}")
        if placeholder_count != value_count:
            raise ValueError(f"Placeholder/value mismatch:{placeholder_count} placeholders vs {value_count} values")
        cursor.executemany(insert_query, all_rows)
        conn.commit()
        print(f"✅ DB insert successful: {cursor.rowcount} rows")
    except Exception as e:
        conn.rollback()
        print(f"❌ DB insert failed: {e}")
        return False

    # ========================================================
    # 7. ONLY AFTER INSERT SUCCESS → DONE
    # ========================================================
    try:
        update_status_done(cursor, link_id )
        conn.commit()
        print("✅ Status updated: done")
    except Exception as e:
        conn.rollback()
        print("❌ Status update failed:", e)
        return False
    print("\n🎉 COMPLETED:", url)
    return True
# ============================================================
# MAIN
# ============================================================

def main():
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': 'https://www.petsupermarket.com/dog/supplies/toys/balls-fetch-toys/dippin%E2%80%99-dots-flying-disc-and-tennis-ball-outdoor-play-dog-toy-set/PSI10527.html',
        'sec-ch-ua': '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36',
    }
    # ========================================================
    # DB CONNECTION
    # ========================================================
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    # ========================================================
    # GET PENDING LINKS
    # ========================================================
    cursor.execute(f"""SELECT id, url, hash_key FROM {db.link_table} WHERE status = 'pending' 
        ORDER BY id ASC """)
    links = cursor.fetchall()
    print(f"Total links: {len(links)}")
    # ========================================================
    # PROCESS
    # ========================================================
    success_count = 0
    failed_count = 0
    for index, row in enumerate(links,1):
        link_id = row["id"]
        url = row["url"]
        hash_key = row["hash_key"]
        print(f"\n\n===== {index}/{len(links)} =====")
        try:
            success = process_product(
                link_id=link_id,
                url=url,
                hash_key=hash_key,
                headers=headers.copy(),
                cursor=cursor,
                conn=conn
            )
            if success:
                success_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            conn.rollback()
            print("❌ Unexpected error:",e)
    # ========================================================
    # CLOSE DB
    # ========================================================
    cursor.close()
    conn.close()
    # ========================================================
    # SUMMARY
    # ========================================================
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print("Total:", len(links))
    print("Success:",success_count)
    print("Failed:",failed_count)
    print("=" * 80)
# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()