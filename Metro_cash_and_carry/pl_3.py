import hashlib
import pymysql
import urllib.parse
from json_repair import repair_json
import db_config_1 as db
from parsel import Selector
import os
import re
import time
import json
import requests


def traverse(obj, categories, brands):
    if isinstance(obj, dict):
        # 🟢 CATEGORY
        if "block_title" in obj and "block_link" in obj:
            title = obj.get("block_title", {}).get("value")
            link = obj.get("block_link", {}).get("value")
            if title and link and "/collection/" in link:
                clean_url = link.replace("\\u002F", "/")
                slug = clean_url.split("/collection/")[1].split("?")[0]
                slug = slug.strip("/")
                categories.append({
                    "name": title.strip(),
                    "url": clean_url,
                    "slug": slug,
                    "cat_type": "category"
                })
        # 🔵 BRAND
        if "slide_link" in obj or "image_link" in obj:
            link_obj = obj.get("slide_link") or obj.get("image_link")
            if isinstance(link_obj, dict):
                link = link_obj.get("value")
                if link and "brand=" in link:
                    clean_url = link.replace("\\u002F", "/")
                    slug = clean_url.split("brand=")[-1].split("&")[0]
                    slug = slug.strip("/")
                    brands.append({
                        "name": slug,
                        "url": clean_url,
                        "slug": slug,
                        "cat_type": "brand"
                    })
        # 🔁 RECURSION
        for v in obj.values():
            traverse(v, categories, brands)
    elif isinstance(obj, list):
        for item in obj:
            traverse(item, categories, brands)

# ----------------------------
# 💾 DB INSERT
# ----------------------------
def insert_categories(categories, location):
    print("location ::::::::::::", location)
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    insert_query = f"""
    INSERT IGNORE INTO `{db.category_table}`
    (category_name, slug, link, pincode, state_code, city, state, type, json_dict, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for cat in categories:
        cursor.execute(insert_query, (
            cat.get("name"),
            cat.get("slug"),
            cat.get("url"),
            location.get("pincode"),
            location.get("state_code"),
            location.get("city"),
            location.get("state"),
            cat.get("cat_type"),
            json.dumps(location),
            "pending"
        ))
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Categories inserted into DB")

def fetch_category_page(pincode, city, state, filename_prefix="category"):
    url = "https://www.metrorrl.com/undefined"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2) AppleWebKit/537.36 Chrome/119 Mobile Safari/537.36"
    }
    location_cookie = {
        "country": "INDIA",
        "country_iso_code": "IN",
        "pincode": pincode,
        "state_code": "06",
        "city": city,
        "state": state
    }
    encoded_location = urllib.parse.quote(json.dumps(location_cookie))
    cookies = {"app_location_details": encoded_location}
    try:
        file_path = os.path.join(db.PL_PAGESAVE, f"{filename_prefix}_{pincode}.html")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                response_data = f.read()
        else:
            session = requests.Session()
            response = session.get(url, headers=headers, cookies=cookies)
            print(f"[{pincode}] Status Code:", response.status_code)
            if response.status_code != 200:
                print("❌ Request failed")
                return
            if response.status_code == 200:
                file_path = os.path.join(db.PL_PAGESAVE, f"{filename_prefix}_{pincode}.html")
                # with open(file_path, "w", encoding="utf-8") as f:
                #     response_data = f.write(response.text)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
                response_data = response.text

        sel =  Selector(text=response_data)
        match = re.search(
            r'window\.__INITIAL_STATE__=(.*?);</script>',
            response_data,
            re.DOTALL
        )
        if not match:
            print("❌ INITIAL_STATE not found")
            return
        raw_js = match.group(1)
        fixed_json_str = repair_json(raw_js)
        json_data = json.loads(fixed_json_str)
        print("✅ JSON repaired successfully")
        # ----------------------------
        # 📦 EXTRACT CATEGORY + BRAND
        # ----------------------------
        categories = []
        brands = []
        traverse(json_data, categories, brands)
        categories = list({c["slug"]: c for c in categories if c["slug"]}.values())
        brands = list({b["slug"]: b for b in brands if b["slug"]}.values())
        print(f"🟢 Categories Found: {len(categories)}")
        print(f"🔵 Brands Found: {len(brands)}")
        # ----------------------------
        # 📍 EXTRACT CONFIG LOCATION
        # ----------------------------
        script_text = sel.xpath(
            '//script[contains(text(),"window.config")]/text()'
        ).get()
        if not script_text:
            print("❌ window.config not found")
        else:
            raw_json = script_text.split("window.config=")[-1].strip()
            if raw_json.endswith(";"):
                raw_json = raw_json[:-1]
            config = json.loads(raw_json)
            location_details = config.get("location_details", {})

            PINCODE_DATA = load_pincode_data()
            sig_data = PINCODE_DATA.get(pincode)
            if not sig_data:
                print(f"❌ No signature found for pincode: {pincode}")
                return
            location_details['x-fp-signature'] = sig_data["x-fp-signature"]
            location_details['x-fp-date'] = sig_data["x-fp-date"]
            # Convert string → dict
            location_details.update(json.loads(sig_data["x-location-detail"]))
            # IMPORTANT: use string version
            # location_details['x-location-detail'] = sig_data["x-location-detail"]
            # location_details['x-fp-signature'] = "***HIDDEN***"
            # location_details['x-fp-date'] = "20260413T043257Z"
            # location_details['x-location-detail'] = '{"country":"INDIA","country_iso_code":"IN","pincode":"110001","state_code":"07","city":"Central Delhi","state":"Delhi"}'
            # location_details['x-fp-signature'] = "***HIDDEN***"
            # location_details['x-fp-signature'] = "***HIDDEN***"
            print("📍 Location Data:")
            print(location_details)
            # ----------------------------
            # 💾 INSERT INTO DB
            # ----------------------------
            insert_categories(categories, location_details)
            insert_categories(brands, location_details)
            print(f"[{pincode}] Saved to {file_path}")
    except Exception as e:
        print(f"[{pincode}] Error:", str(e))


def get_categories_from_db():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = f""" SELECT * FROM `{db.category_table}` WHERE status = 'pending' """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def build_ladder_payload(items, pincode):
    ladder_items = []
    for item in items:
        try:
            ladder_items.append({
                "uid": item.get("uid"),
                "item_code": item.get("item_code"),
                "article_type": item.get("attributes", {}).get("article-type"),
                "marked_price": {
                    "min": item.get("price", {}).get("marked", {}).get("min"),
                    "max": item.get("price", {}).get("marked", {}).get("max")
                },
                "effective_price": {
                    "min": item.get("price", {}).get("effective", {}).get("min"),
                    "max": item.get("price", {}).get("effective", {}).get("max")
                }
            })
        except Exception as e:
            print("⚠️ Skipping item:", e)
    return {
        "items": ladder_items,
        "pincode": pincode,
        "zoneId": ""
    }

def parse_ladder_response(ladder_json):
    result = {}
    available_ladders = ladder_json.get("available_ladders", {})
    for uid, ladders in available_ladders.items():
        uid_list = []
        for ladder in ladders:
            uid_list.append({
                "min_qty": ladder.get("min_quantity"),
                "max_qty": ladder.get("max_quantity"),
                "margin": str(ladder.get("margin")),
                "mrp": str(ladder.get("price", {}).get("marked")),
                "retail_price_per_pc": str(ladder.get("price", {}).get("offer_price"))
            })
        result[str(uid)] = uid_list
    return result

def fetch_ladder_data(payload, location, save_path):
    url = "https://www.metrorrl.com/ext/infibeam/application/api/v1.0/check-ladders"
    encoded_location = urllib.parse.quote(json.dumps({
        "country": "INDIA",
        "country_iso_code": "IN",
        "pincode": location.get("pincode"),
        "state_code": location.get("state_code"),
        "city": location.get("city"),
        "state": location.get("state")
    }))
    headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://www.metrorrl.com",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119 Mobile Safari/537.36",
    "x-fp-sdk-version": "1.9.4-13",
    "X-Requested-With": "XMLHttpRequest"
}
    cookies = {
        "app_location_details": encoded_location
    }
    try:
        # ✅ CHECK IF FILE EXISTS
        if os.path.exists(save_path):
            print(f"📂 Reading from existing file: {save_path}")
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            res = requests.post(url, headers=headers, cookies=cookies, json=payload, timeout=15)
            print("📊 Ladder Status:", res.status_code)
            if res.status_code == 200:
                data = res.json()
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print("✅ Ladder saved:", save_path)
            else:
                print("❌ Ladder failed:", res.text)
                return {}
        parse_ladder_data = parse_ladder_response(data)
        return parse_ladder_data
    except Exception as e:
        print("❌ Ladder Error:", e)
        return {}



def fetch_products_by_slug(slug, location, cat_type, pincode):
    print(f"🔹 Type: {cat_type} | Slug: {slug}")
    print(location)
    original_slug = slug
    encoded_location = urllib.parse.quote(json.dumps(location))
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": "Bearer ***HIDDEN***",
        "User-Agent": "Mozilla/5.0",
        "x-currency-code": "INR",
        "x-fp-sdk-version": "1.9.4-13",
        "x-location-detail": json.dumps({
            "country": "INDIA",
            "country_iso_code": "IN",
            "pincode": location.get("pincode"),
            "state_code": location.get("state_code"),
            "city": location.get("city"),
            "state": location.get("state")
        })
    }
    cookies = {
        "app_location_details": encoded_location
    }
    # ✅ Decide API
    if cat_type == "category":
        base_url = f"https://www.metrorrl.com/ext/catalogueDiscovery/api/search/v1.0/collections/{original_slug}/items/"
        params_extra = {}
    else:  # brand
        base_url = "https://www.metrorrl.com/ext/catalogueDiscovery/api/search/v1.0/products/"
        params_extra = {
            "f": f"brand:{original_slug}:::search:true:::source:suggestion"
        }
    # ✅ Clean slug ONLY for filename
    clean_slug = re.sub(r'[^a-zA-Z0-9]+', '_', original_slug).strip('_')
    folder_path = os.path.join(db.PL_PAGESAVE, "pl_pagesave", pincode)
    os.makedirs(folder_path, exist_ok=True)
    page_id = ""
    page_no = 1
    all_products = []
    while True:
        params = {
            "page_id": page_id,
            "page_size": "100"
        }
        params.update(params_extra)
        file_path = os.path.join(folder_path, f"{cat_type}_{clean_slug}_page_{page_no}.json")
        # ✅ CHECK IF FILE EXISTS
        if os.path.exists(file_path):
            print(f"📂 Reading from existing file: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            response = requests.get(base_url, headers=headers, cookies=cookies, params=params)
            print(f"📄 Page {page_no} | Status: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ Failed for slug: {original_slug}")
                break
            # ✅ SAVE FILE PAGE-WISE
            # file_path = os.path.join(folder_path, f"{cat_type}_{clean_slug}_page_{page_no}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"💾 Saved: {file_path}")
            data = response.json()
        items = data.get("items", [])
        if not items:
            print("❌ No more items")
            break
        if items:
            # 🔥 Build payload for ALL 100 products
            ladder_payload = build_ladder_payload(items, pincode)
            # 📁 Save path
            ladder_file = os.path.join(db.PDP_PAGESAVE, pincode)
            os.makedirs(ladder_file, exist_ok=True)
            offer_file_path = os.path.join(ladder_file, f"{cat_type}_{clean_slug}_page_{page_no}_qty_offer_price.json")
            # 🚀 Call ladder API
            ladder_data = fetch_ladder_data(ladder_payload, location, offer_file_path)
        for item in items:
            images = []
            medias = item.get("medias", [])
            if isinstance(medias, list):
                for media in medias:
                    url = media.get("url")
                    if url:
                        images.append(url)
            uid = str(item.get("uid"))
            # ✅ GET LADDER FOR THIS PRODUCT
            ladders = ladder_data.get(uid, []) if ladder_data else []
            images = json.dumps(images)
            product = {
                "product_slug": item.get("slug"),
                "item_code" : item.get("item_code"),
                "images": images,
                "product_name": item.get("name"),
                "uid": item.get("uid"),
                "store_id": item.get("_custom_json", {}).get("network", {}).get("storeId"),
                "brand_name": item.get("brand", {}).get("name"),
                "weight": item.get("attributes", {}).get("mkp_weight_name"),
                "net_quantity": item.get("attributes", {}).get("net-quantity"),
                "country_of_origin": "India",
                "mrp": str(item.get("price", {}).get("marked", {}).get("min")),
                "rrp": str(item.get("price", {}).get("effective", {}).get("min")),
                "discount": str(item.get("discount")),
                "city": location.get("city"),
                "pincode": location.get("pincode"),
                "in_stock": item.get("sellable"),
                "minimum_quantity" : item.get("_custom_json", {}).get("moq", {}).get("min_OQ"),
                "maximum_quantity" : item.get("_custom_json", {}).get("moq", {}).get("max_OQ"),
                "cat_slug": original_slug,
                "type": cat_type,
                "json_dict": json.dumps(location),
                "pagesave": file_path,
                "quantity_price_tiers": json.dumps(ladders),
                "price_pagesave": offer_file_path
            }
            all_products.append(product)
        page_info = data.get("page", {})
        if not page_info.get("has_next"):
            print("✅ Pagination finished")
            break
        page_id = page_info.get("next_id")
        page_no += 1   # 🔥 increment page
        time.sleep(0.3)
    return all_products

def insert_products(products, row, json_dict):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    insert_query = f"""INSERT IGNORE INTO {db.product_link_table} (
        item_code, images, product_name, brand_name, weight, net_quantity,
        country_of_origin, store_id, mrp, rrp, discount, city, pincode,
        category_name, cat_slug, state_code, state, type,
        product_slug, uid, in_stock, minimum_quantity, maximum_quantity, hash_key, json_dict, status, pagesave, quantity_price_tiers, price_pagesave
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    data = []
    for p in products:
        product_slug = p.get("product_slug")
        pincode = row.get("pincode")
        # 🔑 Create hash_key (product_slug + pincode)
        raw_key = f"{product_slug}+{pincode}"
        hash_key = hashlib.md5(raw_key.encode()).hexdigest()
        data.append((
            p.get("item_code"),
            p.get("images"),
            p.get("product_name"),
            p.get("brand_name"),
            p.get("weight"),
            p.get("net_quantity"),
            p.get("country_of_origin"),
            p.get("store_id"),
            p.get("mrp"),
            p.get("rrp"),
            p.get("discount"),
            p.get("city"),
            p.get("pincode"),
            row.get("category_name"),
            p.get("cat_slug"),
            row.get("state_code"),
            row.get("state"),
            p.get("type"),
            p.get("product_slug"),
            p.get("uid"),
            str(p.get("in_stock")),
            str(p.get("minimum_quantity")),
            str(p.get("maximum_quantity")),
            hash_key,
            json_dict,
            "pending",
            p.get("pagesave"),
            p.get("quantity_price_tiers"),
            p.get("price_pagesave")
        ))
    cursor.executemany(insert_query, data)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Inserted {len(data)} products")

def mark_category_done(slug, pincode):
    try:
        conn = db.get_db_connection(db.db_name)
        cursor = conn.cursor()
        query = f"""
        UPDATE `{db.category_table}`
        SET status = 'done'
        WHERE slug = %s AND pincode = %s
        """
        cursor.execute(query, (slug, pincode))
        conn.commit()
        print(f"✅ Marked DONE → {slug} ({pincode})")
    except Exception as e:
        print(f"❌ Error updating status: {e}")
    finally:
        cursor.close()
        conn.close()


def main():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # query = f""" SELECT * FROM {db.pincode_table} WHERE status = 'pending' and pincode='700001'"""
    query = f""" SELECT * FROM {db.pincode_table} WHERE pincode='700001'"""
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        print("No pending pincode found.")
    for r in rows:
        try:
            pincode = r["pincode"]
            city = r["city"]
            state = r["state"]
            fetch_category_page(pincode, city, state)
            categories = get_categories_from_db()
            print(f"🚀 Found {len(categories)} categories")
            for row in categories:
                slug = row["slug"]
                cat_type = row["type"]
                json_dict = row["json_dict"]
                location = {
                    "pincode": row["pincode"],
                    "state_code": row["state_code"],
                    "city": row["city"],
                    "state": row["state"]
                }
                print(f"\n🔄 Processing: {slug}")
                products = fetch_products_by_slug(slug, location, cat_type, row["pincode"])
                print(f"📦 Products fetched: {len(products)}")
                if products:
                    insert_products(products, row, json_dict)
                    # 🔥 Mark category as done
                    mark_category_done(slug, row["pincode"])
            try:
                conn = db.get_db_connection(db.db_name)
                cursor = conn.cursor()
                query = f""" UPDATE `{db.pincode_table}` SET status = 'done' WHERE pincode = %s """
                cursor.execute(query, (pincode))
                conn.commit()
                print(f"✅ Marked DONE → ({pincode})")
            except Exception as e:
                print(f"❌ Error updating status: {e}")
            finally:
                cursor.close()
                conn.close()
        except Exception as e:
            print(f"❌ Error for {r}: {e}")


def load_pincode_data():
    with open("payload_data.json", "r") as f:
        return json.load(f)

# ----------------------------
# ▶ RUN
# ----------------------------
if __name__ == '__main__':
    main()
