import gzip
from datetime import datetime
from urllib.parse import urlparse, parse_qs, quote
import db_config_1 as db
import pymysql
import hashlib
import os
import time
import random
from parsel import Selector
import requests
import urllib.parse
import sys
import re
import json
import headers_and_cookies as h


proxy = {
   "http": f'http://{db.proxy_token}:super=false@proxy.scrape.do:8080',
   "https": f'http://{db.proxy_token}:super=false@proxy.scrape.do:8080',
}


def url_to_id(url):
    h = hashlib.sha256(url.encode()).hexdigest()
    num = int(h, 16)
    short_id = str(num)[0:12]
    return short_id

def safe_json_load(data):
    """Handles multi-level encoded JSON"""
    try:
        while isinstance(data, str):
            data = json.loads(data)
    except:
        pass
    return data

def clean_text_data(value):
    if value is None:
        return "N/A"
    if not isinstance(value, str):
        return value
    text = value
    # Remove control chars (includes actual \n, \r, \t)
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)
    # remove invisible unicode chars
    text = re.sub(r"[\u200B-\u200F\u202A-\u202E\u2060-\u206F]", " ", text)
    # replace escaped chars
    text = text.replace("\\n", " ")
    text = text.replace("\\r", " ")
    text = text.replace("\\t", " ")
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    # remove backslashes
    text = text.replace("\\", "")
    # OPTIONAL: remove forward slashes
    # text = text.replace("/", "")
    # remove extra spaces/newlines/tabs
    text = re.sub(r"\s+", " ", text)
    # trim
    text = text.strip()
    return text if text else "N/A"

def extract_review_data(data, pid):
    if not data:
        return None
    try:
        reviews = []
        review_count = data.get("totalResults", None)
        for r in data.get("results", []):
            date = "N/A"
            if r.get("lastModificationTime"):
                try:
                    date = datetime.fromisoformat(r["lastModificationTime"]).strftime("%Y-%m-%d")
                except:
                    pass
            reviews.append({
                "review_name": clean_text_data(r.get("userNickname", "N/A")),
                "review_title": clean_text_data(r.get("title", "N/A")),
                "review_content": clean_text_data(r.get("reviewText", "N/A")),
                "rating": r.get("rating", "N/A"),
                "review_date": date,
                "verified": r.get("verified", False)
            })
        if reviews:
            return reviews
    except Exception as e:
        print("❌ Review parse error:", e)



def fetch_reviews_data(product_id, master_class):
    if not master_class:
        return None
    print("fetching:", product_id)
    target_url = f"https://api.urbanoutfitters.com/api/review/v0/uo-us/products/{product_id}/reviews"
    params = {
        "merchandise-class": master_class,
        "offset": 0,
        "limit": 50,
        "filter": "",
        "sort": "submissionTime:desc"
    }
    # Prepare encoded URL
    prepared = requests.Request("GET",target_url,params=params).prepare()
    encoded_url = quote(prepared.url, safe='')
    proxy_url = f"http://api.scrape.do/?token={db.p_token}&url={encoded_url}&super=true"
    data = None
    max_retries = 2
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}")
            # filename = os.path.join(db.REVIEW_PAGESAVE, f"{product_id}.json")
            # if os.path.exists(filename):
            #     with open(filename, "r", encoding="utf-8") as f:
            #         data = json.load(f)
            filename = os.path.join(db.REVIEW_PAGESAVE, f"{product_id}.json.gz")

            if os.path.exists(filename):
                with gzip.open(filename, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                response = requests.get(target_url, params=params, headers=h.headers, cookies=h.cookies)
                if attempt > 1:
                    response = requests.get(proxy_url,timeout=60)
                print("STATUS:", response.status_code)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        # with open(filename, "w", encoding='utf-8') as f:
                        #     json.dump(data, f, ensure_ascii=False, indent=4)
                        with gzip.open(filename, "wt", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                        print("✅ Reviews found")
                        break
                else:
                    print("❌ Bad response")
        except Exception as e:
            print("ERROR:", e)
        time.sleep(2)
    if not data:
        return None
    review_data = extract_review_data(data, product_id)
    # print("review_data ::: ", review_data)
    # return review_data
    # review_data = {
    #     "reviews": review_data
    # }
    return {
        "reviews": review_data
    }

def fetch_size_chart(size_guide_slug, pid):
    payloads = [
        {
            'include': '4',
            'contentfulEnvironment': 'master',
            'content_type': 'sizeGuideConfiguration',
            'fields.slug': size_guide_slug,
        },
        {
            'include': '1',
            'contentfulEnvironment': 'master',
            'content_type': 'sizeGuideVendor',
            'fields.slug': size_guide_slug,
        }
    ]

    target_url = "https://api.urbanoutfitters.com/api/content/v1/uo-us/entries"
    data = None
    max_retries = 2
    for params in payloads:
        prepared = requests.Request('GET', target_url,params=params).prepare()
        encoded_url = quote(prepared.url, safe='')
        proxy_url = (f"http://api.scrape.do/?token={db.p_token}&url={encoded_url}&super=true")
        for attempt in range(1, max_retries + 1):
            try:
                # filename = os.path.join(db.SIZE_PAGESAVE, f"{pid}.json")
                # if os.path.exists(filename):
                #     with open(filename, "r", encoding="utf-8") as f:
                #         return json.load(f)
                filename = os.path.join(db.SIZE_PAGESAVE, f"{pid}.json.gz")
                # if os.path.exists(filename):
                #     with gzip.open(filename, "rt", encoding="utf-8") as f:
                #         return json.load(f)
                # else:
                response = requests.get(target_url, params=params, headers=h.headers, cookies=h.cookies)
                print(f"Attempt {attempt}")
                if attempt > 1:
                    response = requests.get(proxy_url, timeout=80)
                print("STATUS:", response.status_code)
                # print("HEADERS:", response.headers)
                if response.status_code == 200:
                    temp_data = response.json()
                    if temp_data.get("items"):
                        data = temp_data
                        # with open(filename, "w", encoding='utf-8') as f:
                        #     json.dump(data, f, ensure_ascii=False, indent=4)
                        with gzip.open(filename, "wt", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                        print("✅ Size chart found")
                        return data
                    else:
                        print("⚠️ No items found")
                else:
                    print("⚠️ Bad status code")
            except Exception as e:
                print("ERROR:", e)

        print(f"Payload failed: {params['content_type']}")
        time.sleep(2)

    print("❌ No size chart found from any payload")
    return None
    # for params in payloads:
    #     # Prepare original URL with params
    #     prepared = requests.Request('GET',target_url,params=params).prepare()
    #     encoded_url = quote(prepared.url, safe='')
    #     # Dynamic proxy URL
    #     proxy_url = (
    #         f"http://api.scrape.do/?token={db.p_token}&url={encoded_url}&super=true"
    #     )
    #     for attempt in range(1, max_retries + 1):
    #         try:
    #             filename = os.path.join(db.SIZE_PAGESAVE, f"{pid}.json")
    #             if os.path.exists(filename):
    #                 with open(filename, "r", encoding="utf-8") as f:
    #                     return json.load(f)
    #             else:
    #                 print(f"Attempt {attempt}")
    #                 response = requests.get(proxy_url, timeout=40)
    #                 print("STATUS:", response.status_code)
    #                 if response.status_code == 200:
    #                     temp_data = response.json()
    #                     if temp_data.get("items"):
    #                         data = temp_data
    #                         with open(filename, "w", encoding='utf-8') as f:
    #                             json.dump(data, f, ensure_ascii=False, indent=4)
    #                         print("✅ Size chart found")
    #                         return data
    #                     else:
    #                         print("⚠️ No items found")
    #                 else:
    #                     print("⚠️ Bad status code")
    #         except Exception as e:
    #             print("ERROR:", e)
    #             # Wait before retry
    #     time.sleep(2)
    #     print("❌ No size chart found")
    #     return None



def extract_data(url, sel, has_key):
    hash_id = url_to_id(url)
    rows = []
    new_row = []
    try:
        # --------------------------------------- #
        # Tags
        # --------------------------------------- #
        tags = " | ".join(x.strip()
            for x in sel.xpath('//p[@data-qa-pdp-secondary-callout="true"]//span/text() | //p[@data-qa-badge]/@data-qa-badge').getall()
            if x.strip()
        )
        print(tags)
        # --------------------------------------- #
        # shipping cost and delivery ETA
        # --------------------------------------- #
        rows_table = sel.xpath(
            '//h3[normalize-space()="Shipping"]'
            '/following-sibling::div[contains(@class, "s-pwa-cms")][1]'
            '//table//tbody/tr'
        )
        shipping_cost = {}
        estimated_delivery_time = {}
        for row in rows_table:
            method = row.xpath('./td[1]//text()').getall()
            delivery_time = row.xpath('./td[2]//text()').getall()
            cost = row.xpath('./td[3]//text()').getall()

            method = " ".join(x.strip() for x in method if x.strip())
            delivery_time = " ".join(x.strip() for x in delivery_time if x.strip())
            cost = " ".join(x.strip() for x in cost if x.strip())

            if method:
                estimated_delivery_time[method] = delivery_time
                shipping_cost[method] = cost

        print(json.dumps([shipping_cost]))
        shipping_cost = json.dumps([shipping_cost])
        print(json.dumps([estimated_delivery_time]))
        estimated_delivery_time = json.dumps([estimated_delivery_time])
        # ------------------------ #
        # JSON-LD
        # ------------------------ #
        size_guide_available_not = sel.xpath("//button[contains(@class, 'pwa-size-guide-link')]").get()
        if not size_guide_available_not:
            # print("size guide not available on this page....")
            size_chart_present = "No"
        else:
            size_chart_present = "Yes"
        blocks = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
        if not blocks:
            return rows
        data = None
        for block in blocks:
            try:
                temp = json.loads(block.strip())
                if isinstance(temp, dict) and temp.get("@type") == "Product":
                    data = temp
                    break
            except:
                continue
        if not data:
            return rows
        name = data.get("name")
        mpn = data.get("mpn")
        category = data.get("category", "").replace(" > ", "/")
        rating_data = data.get("aggregateRating", {})
        rating_count = rating_data.get("ratingCount")
        average_ratings = rating_data.get("ratingValue")
        description = re.sub(r"\s+", " ", data.get("description", "")).strip()
        brand = (
            data.get("brand", {}).get("name")
            if isinstance(data.get("brand"), dict)
            else data.get("brand")
        )
        price_currency = data.get("offers", {}).get("priceCurrency", "USD")
        # ------------------------ #
        # PINIA STATE (NEW)
        # ------------------------ #
        state_block = sel.xpath('//script[@id="urbnInitialPiniaState"]/text()').get()
        if not state_block:
            return rows
        data_2 = safe_json_load(state_block)
        catalog = data_2.get("catalog", {})
        products = catalog.get("products", {})
        slug = urlparse(url).path.split("/")[-1]
        product_root = products.get(slug) or next(iter(products.values()), {})
        if not product_root:
            return rows

        product_data = product_root.get("product", {})
        pid = product_data.get("productId") or mpn
        reviews = None
        size_chart = None
        size_guide_slug = product_data.get("sizeGuide")
        merchandiseClass = product_data.get("merchandiseClass")
        if merchandiseClass :
            # reviews, review_count = fetch_reviews_data(pid, merchandiseClass)
            reviews = fetch_reviews_data(pid, merchandiseClass)

        if size_guide_slug:
            size_chart = fetch_size_chart(size_guide_slug, pid)
        print("size_guide_slug :::: ", size_guide_slug)
        print("merchandiseClass :::: ", merchandiseClass)
        # print("reviews :::::::: ", reviews)
        # size_slug = product_root.get("sizeGuide", "")
        # ✅ FIXED COLOR SOURCE
        sku_info = product_root.get("skuInfo", {})
        color_list = sku_info.get("primarySlice", {}).get("sliceItems", [])
        size_list = sku_info.get("secondarySlice", {}).get("sliceItems", [])
        # build maps
        color_map = {str(c.get("code")): c for c in color_list}
        size_map = {}
        for group in size_list:
            fit_type = group.get("code")
            for s in group.get("includedSizes", []):
                size_map[str(s.get("id"))] = {
                    "size": s.get("displayName"),
                    "fit": fit_type
                }

        # ------------------------ #
        # OLD STATE (VARIANTS)
        # ------------------------ #
        selector_map = {}
        old_state_block = sel.xpath('//script[@id="urbnInitialState"]/text()').get()
        if old_state_block:
            old_data = safe_json_load(old_state_block)
            product_key = next(
                (k for k in old_data.keys() if k.startswith("product--")),
                None
            )
            if product_key:
                selector_map = (
                    old_data.get(product_key, {})
                    .get("skuSelection", {})
                    .get("selectorMap", {})
                )
        if not selector_map:
            return rows
        # onsite filter
        # onsite_html_colors = sel.xpath(
        #     "//fieldset[@data-qa-color]//img/@alt"
        # ).getall()
        onsite_html_colors = list(dict.fromkeys(
            sel.xpath(
                "//fieldset[@data-qa-color]//img/@alt | //fieldset[@data-qa-color]//span/@aria-label"
            ).getall()
        ))
        # ------------------------ #
        # LOOP VARIANTS
        # ------------------------ #
        for selector_key, selector_value in selector_map.items():
            try:
                if not selector_value:
                    continue
                if selector_value.get("isDisplayable") is False:
                    continue
                sku_id = str(selector_value.get("skuId"))
                if not sku_id:
                    continue
                saleprice = round(float(selector_value.get("salePrice", 0)), 2)
                listprice = round(float(selector_value.get("listPrice", 0)), 2)
                discount = listprice - saleprice
                discount = None if discount == 0 else round(discount, 2)
                stock_level = selector_value.get("stockLevel", 0)
                is_in_stock = "FALSE" if stock_level == 0 else "TRUE"
                # SIZE
                size_id = str(selector_value.get("sizeId"))
                size_data = size_map.get(size_id, {})
                size = size_data.get("size")
                fit_type = size_data.get("fit", "")
                # COLOR
                parts = selector_key.split("|")
                color_code = parts[0] if parts else ""
                color_data = color_map.get(str(color_code), {})
                colour_name = color_data.get("displayName", color_code)
                # ✅ FINAL IMAGE FIX (skuInfo)
                image_id = color_data.get("id")
                images = []
                if image_id:
                    images = [
                        f"https://images.urbndata.com/is/image/UrbanOutfitters/{image_id}_{img}?$xlarge$&fit=constrain&qlt=80&wid=640"
                        for img in color_data.get("images", [])
                    ]
                image_url = images[0] if images else None
                alt_image_urls = " | ".join(images[1:]) if len(images) > 1 else None
                size_param = urllib.parse.quote_plus(size) if size else ""
                variant_url = (
                    f"https://www.urbanoutfitters.com/shop/{slug}"
                    f"?color={color_code}&type={fit_type}&quantity=1&size={size_param}"
                )
                row = {
                    "website": "Urban Outfitters",
                    "pid": pid,
                    "name": name,
                    "description": description,
                    "category": category,
                    "image_url": image_url,
                    "price": listprice,
                    "price_currency": price_currency,
                    "sale_price": saleprice,
                    "final_price": saleprice,
                    "discount": discount,
                    "is_in_stock": is_in_stock,
                    "brand": brand,
                    "mpn": mpn,
                    "sku": sku_id,
                    "colour": colour_name,
                    "size": size,
                    "variant_price": saleprice,
                    "alternate_image_urls": alt_image_urls,
                    "link_url": variant_url,
                    "num_ratings": rating_count,
                    # "num_ratings": rating_count,
                    "avg_ratings": average_ratings,
                    "hash_id": str(hash_id),
                    "main_url": url,
                    "size_type": f"{size} - {fit_type}" if size else None,
                    "review_text": json.dumps(reviews, ensure_ascii=False) if reviews else None,
                    "size_chart_response": json.dumps(size_chart, ensure_ascii=False) if size_chart else None,
                    # "review_text": reviews,
                    # "size_chart_response": size_chart,
                    "size_chart_present": size_chart_present,
                    "coupons_and_offers":None,
                    "delivery_ETA": estimated_delivery_time,
                    "shipping_cost": shipping_cost,
                    "return_fee" : None,
                    "tags": tags,
                    "review_summary": None,
                    "return_policy" : "https://www.urbanoutfitters.com/help/return-policy"
                }
                rows.append(row)

            except Exception as e:
                print("Variant error:", e)
                continue

        # ------------------------ #
        # FILTER FRONTEND COLORS
        # ------------------------ #
        if onsite_html_colors:
            print(onsite_html_colors)
            new_row = [r for r in rows
                       if r.get("colour") in onsite_html_colors]
        else:
            new_row = rows
        # for row in new_row:
        #     print(row.get("colour"))
        return new_row
    except Exception as e:
        import traceback
        print("Fatal error:", e)
        traceback.print_exc()
        return new_row
# def extract_data(url, sel, has_key):
#     hash_id = url_to_id(url)
#     rows = []
#
#     try:
#         # ------------------------ #
#         # Parse JSON-LD
#         # ------------------------ #
#         blocks = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
#         if not blocks:
#             print("No JSON-LD block found")
#             return rows
#
#         try:
#             data = json.loads(blocks[-1].strip())
#         except Exception as e:
#             print(f"JSON-LD parsing failed: {e}")
#             return rows
#
#         name = data.get("name")
#         mpn = data.get("mpn")
#         category = data.get("category", "")
#         category = category.replace(" > ", "/") if category else ""
#
#         # Handle OLD + NEW offer structure
#         offers_data = data.get("offers", {})
#         sku_list = []
#
#         if isinstance(offers_data, list):
#             sku_list = [
#                 str(item.get("sku"))
#                 for item in offers_data
#                 if item.get("sku")
#             ]
#             price_currency = offers_data[0].get("priceCurrency", "USD")
#
#         elif isinstance(offers_data, dict):
#             price_currency = offers_data.get("priceCurrency", "USD")
#
#         else:
#             price_currency = "USD"
#
#         # ------------------------ #
#         # Parse URBN State
#         # ------------------------ #
#         state_block = sel.xpath('//script[@id="urbnInitialState"]/text()').get()
#         if not state_block:
#             print("No urbnInitialState found")
#             return rows
#
#         try:
#             temp = json.loads(state_block)
#             data_2 = json.loads(temp) if isinstance(temp, str) else temp
#         except Exception as e:
#             print(f"urbnInitialState parsing failed: {e}")
#             return rows
#
#         # Safe product key detection
#         try:
#             key_name = next(
#                 key for key in data_2.keys()
#                 if key.startswith("product--")
#             )
#         except StopIteration:
#             print("Product key not found")
#             return rows
#
#         product_core = data_2.get(key_name, {}).get("core", {}).get("catalogData", {})
#         if not product_core:
#             print("catalogData missing")
#             return rows
#
#         pid = product_core.get("productId")
#         rating_count = product_core.get("reviews", {}).get("count")
#         average_ratings = product_core.get("reviews", {}).get("averageRating")
#
#         product_info = product_core.get("product", {})
#         long_desc = product_info.get("longDescription", "")
#         brand = product_info.get("brand", "")
#         brand_desc = product_info.get("brandDescription", "")
#
#         description_parts = [long_desc]
#         if brand_desc:
#             description_parts.extend([brand, brand_desc])
#
#         description = " ".join(description_parts)
#         clean_description = re.sub(r"[\\\-\*]", "", description)
#         clean_description = re.sub(r"\s+", " ", clean_description).strip()
#
#         color_list = product_core.get("skuInfo", {}).get("primarySlice", {}).get("sliceItems", [])
#         size_list = product_core.get("skuInfo", {}).get("secondarySlice", {}).get("sliceItems", [])
#         selector_map = data_2.get(key_name, {}).get("skuSelection", {}).get("selectorMap", {})
#
#         # ------------------------ #
#         # Collect Hidden SKUs (availableStatus == 1111)
#         # ------------------------ #
#         invalid_skus = set()
#         for slice_item in color_list:
#             for sku_obj in slice_item.get("includedSkus", []):
#                 if sku_obj.get("availableStatus") == 1111:
#                     invalid_skus.add(str(sku_obj.get("skuId")))
#         # Fix slug safely
#         parsed = urlparse(url)
#         slug = parsed.path.split("/")[-1]
#
#         # ------------------------ #
#         # Loop Variants
#         # ------------------------ #
#         for selector_key, selector_value in selector_map.items():
#
#             try:
#                 if not selector_value:
#                     continue
#
#                 sku_id = selector_value.get("skuId")
#                 # Skip hidden SKUs
#                 if sku_id in invalid_skus:
#                     continue
#
#                 if sku_list and sku_id not in sku_list:
#                     continue
#
#                 saleprice = round(float(selector_value.get("salePrice", 0)), 2)
#                 listprice = round(float(selector_value.get("listPrice", 0)), 2)
#
#                 discount = listprice - saleprice
#                 discount = None if discount == 0 else round(discount, 2)
#
#                 stock_level = selector_value.get("stockLevel", 0)
#                 is_in_stock = "FALSE" if stock_level == 0 else "TRUE"
#
#                 colour_id = selector_value.get("colorId")
#                 size_id = selector_value.get("sizeId")
#
#                 # ---- Map Size ----
#                 size = None
#                 fit_type = None
#
#                 for size_item in size_list:
#                     fit_label = size_item.get("displayName")
#                     for s in size_item.get("includedSizes", []):
#                         if str(s.get("id")) == str(size_id):
#                             size = s.get("displayName")
#                             fit_type = fit_label
#                             break
#                     if size:
#                         break
#
#                 new_size_format = f"{size} - {fit_type}" if fit_type else size
#                 fit_type_param = fit_type.upper() if fit_type else ""
#
#                 # ---- Map Color ----
#                 colour_name = None
#                 image_url = ""
#                 alt_image_urls = ""
#                 color_code = None
#
#                 for color_item in color_list:
#                     if str(color_item.get("code")) == str(colour_id):
#                         colour_name = color_item.get("displayName")
#                         color_code = color_item.get("code")
#                         image_id = color_item.get("id")
#
#                         images = [
#                             f"https://images.urbndata.com/is/image/UrbanOutfitters/{image_id}_{img}?$xlarge$&fit=constrain&qlt=80&wid=640"
#                             for img in color_item.get("images", [])
#                         ]
#
#                         if images:
#                             image_url = images[0]
#                             alt_image_urls = " | ".join(images[1:])
#                         break
#
#                 size_param = urllib.parse.quote_plus(size) if size else ""
#
#                 variant_url = (
#                     f"https://www.urbanoutfitters.com/shop/{slug}"
#                     f"?color={color_code}&type={fit_type_param}&quantity=1&size={size_param}"
#                 )
#
#                 row = {
#                     "website": "Urban Outfitters",
#                     "pid": pid,
#                     "name": name,
#                     "short_description": None,
#                     "description": clean_description,
#                     "category": category,
#                     "image_url": image_url,
#                     "price": listprice,
#                     "price_currency": price_currency,
#                     "sale_price": saleprice,
#                     "final_price": saleprice,
#                     "discount": discount,
#                     "is_on_sale": None,
#                     "is_in_stock": is_in_stock,
#                     "keywords": None,
#                     "brand": brand if brand else None,
#                     "manufacturer": None,
#                     "mpn": mpn,
#                     "upc_ean": None,
#                     "sku": sku_id,
#                     "colour": colour_name,
#                     "gender": None,
#                     "size": size,
#                     "variant_price": saleprice,
#                     "alternate_image_urls": alt_image_urls,
#                     "link_url": variant_url,
#                     "num_ratings": rating_count,
#                     "avg_ratings": average_ratings,
#                     "hash_id": str(hash_id),
#                     "main_url": url,
#                     "size_type": new_size_format,
#                 }
#
#                 rows.append(row)
#
#             except Exception as variant_error:
#                 print(f"Variant error for {selector_key}: {variant_error}")
#                 continue
#         # print("rows ::: ", rows)
#         return rows
#
#     except Exception as main_error:
#         print(f"Fatal error while extracting {url}: {main_error}")
#         return rows

# # full_hash = hashlib.sha256(url.encode()).hexdigest()
# hash_id = url_to_id(url)
# rows = []
# # ------------------------ #
# # Parse JSON-LD (block 1)
# # ------------------------ #
# blocks_1 = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
# if not blocks_1:
#     raise ValueError("No application/ld+json blocks found")
# last_block = blocks_1[-1].strip()
# try:
#     data = json.loads(last_block)
#     valid_sku_list = data.get("offers", {}).get("offers") or []
#     if not isinstance(valid_sku_list, list):
#         valid_sku_list = []
#     sku_list = [
#         str(item.get("sku"))
#         for item in valid_sku_list
#         if isinstance(item, dict) and item.get("sku")
#     ]
#     # valid_sku_list = data.get("offers", {}).get("offers")
#     # sku_list = [str(item.get("sku")) for item in valid_sku_list if "sku" in item]
#     name = data["name"]
#     images = data["image"]
#     mpn = data["mpn"]
#     category = data["category"].replace(" > ", "/")
# except json.JSONDecodeError as e:
#     raise ValueError(f"Failed to parse JSON: {e}")
# # ------------------------ #
# # Parse URBN state (block 2)
# # ------------------------ #
# blocks_2 = sel.xpath('//script[@id="urbnInitialState"]/text()').get()
# if not blocks_2:
#     raise ValueError("No URBN state block found")
# try:
#     temp = json.loads(blocks_2)
#     data_2 = json.loads(temp) if isinstance(temp, str) else temp
#     slug = url.split("/")[-1]
#     key_name = f"product--{slug}"
#     # key_name = "product--" + re.sub(r"[^a-z0-9\-]", "", temp_name)
#     pid = data_2[key_name]["core"]["catalogData"]["productId"]
#     rating_count = data_2[key_name]["core"]["catalogData"]["reviews"]["count"]
#     average_ratings = data_2[key_name]["core"]["catalogData"]["reviews"]["averageRating"]
#     long_desc = data_2[key_name]["core"]["catalogData"]["product"].get("longDescription", "")
#     brand = data_2[key_name]["core"]["catalogData"]["product"].get("brand", "")
#     branddescription = data_2[key_name]["core"]["catalogData"]["product"].get("brandDescription", "")
#     parts = [long_desc]  # always include long description
#     if brand and branddescription:
#         parts.append(brand)
#     if branddescription:
#         parts.append(branddescription)
#     description = " ".join(parts)
#     # description = " ".join(part for part in [long_desc, brand, branddescription] if part)
#     clean_description = re.sub(r"[\\\-\*]", "", description)
#     clean_description = re.sub(r"\s+", " ", clean_description).strip()
#     color_name_list = data_2[key_name]["core"]["catalogData"]["skuInfo"]["primarySlice"]["sliceItems"]
#     size_name_list = data_2[key_name]["core"]["catalogData"]["skuInfo"]["secondarySlice"]["sliceItems"]
#     selector_map = data_2[key_name]["skuSelection"]["selectorMap"]
#     # ------------------------ #
#     # Loop through variants
#     # ------------------------ #
#     for selector in selector_map:
#         if selector_map[selector]:
#             sku_id = selector_map[selector]["skuId"]
#             # size = selector_map[selector]["size"]
#             sale_price = selector_map[selector]["salePrice"]
#             list_Price = selector_map[selector]["listPrice"]
#             saleprice = float("{:.2f}".format(float(sale_price)))
#             listprice = float("{:.2f}".format(float(list_Price)))
#             discount = listprice - saleprice
#             if discount == 0:
#                 discount = None
#             stock_level = selector_map[selector]["stockLevel"]
#             is_in_stock = "FALSE" if stock_level == 0 else "TRUE"
#             colour_id = selector_map[selector]["colorId"]
#             size_id = selector_map[selector]["sizeId"]
#             size = None
#             fit_type = None
#             for size_item in size_name_list:
#                 url_size_displayname = size_item["displayName"]
#                 included_size = size_item["includedSizes"]
#                 for all_size in included_size:
#                     sizeid = all_size["id"]
#                     if str(sizeid) == str(size_id):
#                         size = all_size.get("displayName")
#                         fit_type = url_size_displayname
#                         break
#                 if size:
#                     break
#             # Normalize fit_type
#             if fit_type:
#                 new_size_formate = f"{size} - {fit_type}"
#             fit_type = fit_type.upper() if fit_type else ""
#             colour_name = None
#             images_code_lst = []
#             for color_item in color_name_list:
#                 if str(color_item.get("code")) == str(colour_id):
#                     color_code =color_item.get("code")
#                     colour_name = color_item.get("displayName")
#                     image_id = color_item.get("id")
#                     images_level_list = color_item.get("images")
#                     for i in images_level_list:
#                         images_code = f"{image_id}_{i}"
#                         images_code_lst.append(images_code)
#             images = [
#                 f"https://images.urbndata.com/is/image/UrbanOutfitters/{code}?$xlarge$&fit=constrain&qlt=80&wid=640"
#                 for code in images_code_lst
#             ]
#             if images:
#                 image_url = images[0]
#                 alt_image_urls = " | ".join(images[1:])
#             else:
#                 image_url = ""
#                 alt_image_urls = ""
#             # Safety fallback
#             price_currency = data.get("offers", {}).get("priceCurrency", "USD")
#
#             # ------------------------ #
#             # ------------------------ #
#             # Build output row
#             # ------------------------ #
#             if sku_id in sku_list:
#                 size_param = urllib.parse.quote_plus(size) if size else ""
#                 variant_url = (
#                     f"https://www.urbanoutfitters.com/shop/{slug}"
#                     f"?color={color_code}&type={fit_type}&quantity=1&size={size_param}"
#                 )
#                 row = {
#                     "website": "Urban Outfitters",
#                     "pid": pid,
#                     "name": name,
#                     "short_description": None,
#                     "description": clean_description,
#                     "category": category,
#                     "image_url": image_url,
#                     "price": listprice,
#                     "price_currency": price_currency,
#                     "sale_price": saleprice,
#                     "final_price": saleprice,
#                     "discount": None if discount==0 else discount,
#                     "is_on_sale": None,
#                     "is_in_stock": is_in_stock,
#                     "keywords": None,
#                     "brand": brand if brand else None,
#                     "manufacturer": None,
#                     "mpn": mpn,
#                     "upc_ean": None,
#                     "sku": sku_id,
#                     "colour": colour_name,
#                     "gender": None,
#                     "size": size,
#                     "variant_price": saleprice,
#                     "alternate_image_urls": alt_image_urls,
#                     "link_url": variant_url,
#                     "num_ratings": rating_count,
#                     "avg_ratings": average_ratings,
#                     "hash_id": str(hash_id),
#                     "main_url": url,
#                     "size_type": new_size_formate,
#                     "fit_type": fit_type,
#                 }

#  LOAD PROXIES FROM FILE

def load_proxies(file_path):
    proxy_list = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) != 4:
                print(f"Invalid proxy format: {line}")
                continue
            ip, port, user, pwd = parts
            proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
            proxy_list.append(proxy_url)
    return proxy_list

def get_random_proxy():
    if not PROXIES:
        return None
    proxy = random.choice(PROXIES)
    return {
        "http": proxy,
        "https": proxy
    }

def get_datadom_token():
    import requests

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.urbanoutfitters.com',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://www.urbanoutfitters.com/',
        'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    }

    data = {
        'jspl': '***HIDDEN***',
        'eventCounters': '[]',
        'jsType': 'ch',
        'cid': '***HIDDEN***',
        'ddk': '***HIDDEN***',
        'Referer': 'https%3A%2F%2Fwww.urbanoutfitters.com%2Fwomens-clothing',
        'request': '%2Fwomens-clothing',
        'responsePage': 'origin',
        'ddv': '5.9.0',
    }

    response = requests.post('https://dd.urbanoutfitters.com/js/', headers=headers, data=data)
    if response.status_code == 200:
        try:
            result = response.json()
            cookie = result.get("cookie")
            if cookie:
                new_token = cookie.split(";")[0].split("=")[1]
                # save_token(new_token)
                return new_token
        except:
            pass
        # return datadom_token

def fetch_product_url(url, name, category, id):
    # headers = {
    #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    #     'Accept-Language': 'en-US,en;q=0.9',
    #     'Cache-Control': 'max-age=0',
    #     'Connection': 'keep-alive',
    #     'Sec-Fetch-Dest': 'document',
    #     'Sec-Fetch-Mode': 'navigate',
    #     'Sec-Fetch-Site': 'same-origin',
    #     'Sec-Fetch-User': '?1',
    #     'Upgrade-Insecure-Requests': '1',
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    #     'sec-ch-device-memory': '8',
    #     'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    #     'sec-ch-ua-arch': '"x86"',
    #     'sec-ch-ua-full-version-list': '"Chromium";v="146.0.7680.165", "Not-A.Brand";v="24.0.0.0", "Google Chrome";v="146.0.7680.165"',
    #     'sec-ch-ua-mobile': '?0',
    #     'sec-ch-ua-model': '""',
    #     'sec-ch-ua-platform': '"Windows"',
    # }
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Referer': url,
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        'sec-ch-device-memory': '32',
        'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Chromium";v="148.0.7778.217", "Google Chrome";v="148.0.7778.217", "Not/A)Brand";v="99.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        # 'Cookie': '***HIDDEN***',
    }
    print("processing ::: ", url)

    params = {'source': 'PRODUCTIDPRODUCTTRAY',}
    try:
        has_key=  url_to_id(url)
        FILE_PATH = f"{db.DATA_PAGESAVE}\\{has_key}.html.gz"
        if os.path.exists(FILE_PATH):
            with gzip.open(FILE_PATH, "rt", encoding="utf-8") as f:
                html_content = f.read()
        # if os.path.exists(FILE_PATH):
        #     with open(FILE_PATH, "r", encoding='UTF-8') as f:
        #         html_content = f.read()
        else:
            # using IPRoyal proxies

            # response = requests.get(url, headers=headers, proxies=proxy, timeout=5)
            max_retries = 3
            for attempt in range(max_retries):
                # proxy = get_random_proxy()
                # print("Using Proxy:", proxy)
                try:
                    # super_mode = "false" if attempt < 2 else "true"
                    super_mode = 'true'
                    proxy = {
                        "http": f"http://{db.proxy_token}:super={super_mode}@proxy.scrape.do:8080",
                        "https": f"http://{db.proxy_token}:super={super_mode}@proxy.scrape.do:8080",
                    }
                    print(f"TRY {attempt + 1} | super={super_mode}")
                    response = requests.get("https://api.scrape.do/",
                                            params={
                                                "token": db.proxy_token,
                                                "url": url,
                                            },
                                            headers=h.headers,
                                            timeout=600,
                                            allow_redirects=False,
                                            )
                    # # from curl_cffi import requests
                    # response = requests.get(url,
                    #                         headers=h.headers,
                    #                         params=params,
                    #                         # impersonate="chrome120",
                    #                         proxies=proxy,  # Use the proxy if available and if need to use.
                    #                         verify=False,
                    #                         timeout=600,
                    #                         allow_redirects=False
                    #                         )
                    # If status code is not 200, treat it as failure
                    if response.status_code != 200:
                        raise Exception(f"HTTP {response.status_code}")
                    break
                except Exception as e:
                    if response.status_code == 404:
                        status = "failed_404"
                    else:
                        status="failed"
                    conn = db.get_db_connection(db.db_name)
                    cur = conn.cursor()
                    print(f"Retry {attempt + 1}/{max_retries} failed: {e}")
                    cur.execute(f"UPDATE {db.link_table} SET status = '{status}' WHERE id = %s", (id,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    time.sleep(20)
                    return
            else:
                print("❌ Could not fetch page after retries")
                return
            # print(response.headers)
            print(response.status_code)
            if response.status_code == 200:
                html_content = response.text
                with gzip.open(FILE_PATH, "wt", encoding="utf-8") as f:
                    f.write(html_content)
                # with open(FILE_PATH, "w", encoding='UTF-8') as f:
                #     f.write(html_content)
            else:
                response.raise_for_status()
        sel = Selector(html_content)
        result = extract_data(url, sel, has_key)
        try:
            conn = db.get_db_connection(db.db_name)
            cur = conn.cursor()
            for row in result:
                insert_dynamic(db.data_table, row, cur)
            cur.execute(f"UPDATE {db.link_table} SET status = 'done' WHERE id = %s", (id,))
            conn.commit()
            cur.close()
            conn.close()
            print(f"✔ Saved all products for {url}")
        except Exception as e:
            print(f"❌ Database error for {url}: {e}")
    except Exception as e:
        print(f"❌ Error fetching HTML for {name}: {e}")

# def insert_dynamic(table, data_dict, cursor):
#     columns = ", ".join(data_dict.keys())
#     placeholders = ", ".join(["%s"] * len(data_dict))
#     values = []
#     for v in data_dict.values():
#         if isinstance(v, (dict, list)):
#             values.append(json.dumps(v, ensure_ascii=False))
#         else:
#             values.append(v)
#     sql = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
#     cursor.execute(sql, values)

import json

def insert_dynamic(table, data_dict, cursor):
    columns = ", ".join(f"`{col}`" for col in data_dict.keys())
    placeholders = ", ".join(["%s"] * len(data_dict))
    values = []
    for v in data_dict.values():
        if isinstance(v, (dict, list)):
            values.append(json.dumps(v, ensure_ascii=False))
        else:
            values.append(v)
    # Create update part
    update_clause = ", ".join(
        [f"`{col}` = VALUES(`{col}`)" for col in data_dict.keys()]
    )
    sql = f"""
        INSERT INTO `{table}` ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
        {update_clause}
    """
    cursor.execute(sql, values)


# def insert_dynamic(table, data_dict, cursor):
#     """
#     Insert a row dynamically into any table using a dict.
#     Keys = column names, values = row values.
#     """
#     columns = ", ".join(data_dict.keys())
#     placeholders = ", ".join(["%s"] * len(data_dict))
#     values = list(data_dict.values())
#
#     sql = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
#     cursor.execute(sql, values)

from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_THREADS = 1
def main(rows):
    futures = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for p in rows:
            futures.append(
                executor.submit(
                    fetch_product_url,
                    p['url'], p['name'], p['category'], p['id']
                )
            )
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("❌ Thread error:", e)


if __name__ == "__main__":
    # start_index = sys.argv[1]
    # end_index = sys.argv[-1]
    # print("start:", start_index)
    # print("end:", end_index)
    PROXY_FILE = r"D:\Julee\CODE\URBAN_OUTFITTERS\iproyal-proxies.txt"
    PROXIES = load_proxies(PROXY_FILE)
    print("Loaded proxies:", len(PROXIES))
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql .cursors.DictCursor)
    # cur.execute(f"SELECT * FROM {db.link_table} WHERE status = 'pending' AND ID BETWEEN {start_index} AND  {end_index} ORDER BY ID ASC")
    cur.execute(f"SELECT * FROM {db.link_table} WHERE status = 'pending' ORDER BY ID ASC limit 1")
    # cur.execute(f"SELECT * FROM {db.link_table} WHERE hash_id = '9334882367448384'  ORDER BY ID ASC")
    rows = cur.fetchall()
    main(rows)
    cur.close()
    conn.close()