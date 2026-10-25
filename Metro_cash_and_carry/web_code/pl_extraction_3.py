import pymysql
import urllib.parse
import os
import re
import json
import time
import string
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import db_config_1 as db
import hashlib


def extract_full_product_data(item):
    results = []
    # ✅ Parent fields
    parent_slug = item.get("slug")
    parent_item_code = item.get("item_code")
    parent_uid = item.get("uid")
    parent_weight = item.get("attributes", {}).get("mkp_weight_name")
    parent_net_qty = item.get("attributes", {}).get("net-quantity")
    parent_mrp = item.get("price", {}).get("marked", {}).get("max")
    parent_rrp = item.get("price", {}).get("effective", {}).get("max")
    parent_discount = item.get("discount")
    brand_name = item.get("brand", {}).get("name")
    category_name = None
    if item.get("categories"):
        category_name = item["categories"][0].get("name")
    # ✅ Store ID
    store_id = item.get("_custom_json", {}).get("network", {}).get("storeId")
    # ✅ Add parent row
    if parent_slug:
        results.append({
            "type": "parent",
            "parent_slug": parent_slug,
            "slug": parent_slug,
            "item_code": parent_item_code,
            "uid": parent_uid,
            "weight": parent_weight,
            "net_quantity": parent_net_qty,
            "mrp": parent_mrp,
            "rrp": parent_rrp,
            "discount": parent_discount,
            "brand": brand_name,
            "category": category_name,
            "store_id": store_id
        })
    # ✅ Variant fields
    variants = item.get("_custom_json", {}).get("variants", [])
    for variant in variants:
        variant_weight = variant.get("mkp_weight_name")
        for v_item in variant.get("items", []):
            v = v_item.get("item", {})
            slug = v.get("slug")
            if not slug:
                continue
            results.append({
                "type": "variant",
                "parent_slug": parent_slug,
                "slug": slug,
                "item_code": v.get("item_code"),
                "uid": v.get("uid"),
                "weight": variant_weight,
                "net_quantity": parent_net_qty,  # ✅ same as parent
                "mrp": v.get("mrp"),
                "rrp": v.get("rrp"),
                "discount": v.get("discountPercentage"),
                "brand": brand_name,
                "category": category_name,
                "store_id": store_id  # ✅ same store_id
            })
    return results


def insert_products(rows, pincode, city, state, state_code):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    insert_query = f"""
    INSERT IGNORE INTO `{db.product_link_table}` (
        item_code,
        images,
        product_name,
        brand_name,
        weight,
        net_quantity,
        country_of_origin,
        store_id,
        mrp,
        rrp,
        discount,
        city,
        pincode,
        category_name,
        cat_slug,
        state_code,
        state,
        type,
        product_slug,
        uid,
        in_stock,
        minimum_quantity,
        maximum_quantity,
        hash_key,
        json_dict,
        status,
        pagesave
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s
    )
    """
    data_to_insert = []
    for row in rows:
        slug = row.get("slug")
        store_id = row.get("store_id")
        # 🔑 UNIQUE HASH (VERY IMPORTANT)
        hash_key = hashlib.md5(f"{slug}_{store_id}_{pincode}".encode()).hexdigest()
        values = (
            row.get("item_code"),
            None,  # images (you can fill later)
            None,  # product_name (optional)
            row.get("brand"),
            row.get("weight"),
            row.get("net_quantity"),
            "India",
            store_id,
            row.get("mrp"),
            row.get("rrp"),
            row.get("discount"),
            city,
            pincode,
            row.get("category"),
            None,  # cat_slug
            state_code,  # state_code (adjust if dynamic)
            state,
            row.get("type"),
            slug,
            row.get("uid"),
            None,  # in_stock
            None,
            None,
            hash_key,
            json.dumps(row),
            "pending",
            row.get("pagesave")
        )
        data_to_insert.append(values)
    try:
        cursor.executemany(insert_query, data_to_insert)
        conn.commit()
        print(f"✅ Inserted/Updated: {len(data_to_insert)} records")
    except Exception as e:
        print(f"❌ Insert error: {e}")
    finally:
        cursor.close()
        conn.close()


def search_with_pagination(query, session, headers, cookies, URL, save_folder,
                           pincode, city, state, state_code):
    print(f"🚀 Start query: {query}")
    session = requests.Session()
    page_id = None
    page_no = 1
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    while True:
        params = {
            "f": "display:AAAA:::type:product:::source:suggestion:::search:true",
            "page_size": 100,
            "q": query
        }
        if page_id:
            params["page_id"] = page_id
        try:
            response = session.get(URL, headers=headers, params=params, cookies=cookies, timeout=10)
            if response.status_code != 200:
                print(f"❌ {query} failed: {response.status_code}")
                break
            data = response.json()
            # 💾 OPTIONAL: save JSON backup
            file_path = os.path.join(save_folder, f"{query}_page_{page_no}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"❌ {query} error: {e}")
            break
        items = data.get("items", [])
        if not items:
            break
        # 🔥 EXTRACT + INSERT HERE
        all_rows = []
        for item in items:
            extracted = extract_full_product_data(item)
            for row in extracted:
                row["pagesave"] = f"{query}_page_{page_no}.json"
                all_rows.append(row)
        # 🔥 INSERT INTO DB
        insert_products(all_rows, pincode, city, state, state_code)
        # Pagination
        page_info = data.get("page", {})
        if not page_info.get("has_next"):
            break
        page_id = page_info.get("next_id")
        if not page_id:
            break
        page_no += 1
        time.sleep(0.1)
    cursor.close()
    conn.close()


# 🔥 MAIN SCRAPER FUNCTION
def web_pl_pattern_wise(pincode, city, state, state_code):
    # 📍 Location
    location_data = {
        "country": "INDIA",
        "country_iso_code": "IN",
        "pincode": str(pincode),
        "state_code": str(state_code),
        "city": str(city),
        "state": str(state)
    }
    cookies = {
        "app_location_details": urllib.parse.quote(json.dumps(location_data))
    }
    # cookies = {
    #     'anonymous_id': '***HIDDEN***',
    #     'old_browser_anonymous_id': '***HIDDEN***',
    #     '_ga': 'GA1.1.1553543780.1776327087',
    #     'app_location_details': '%7B%22country%22%3A%22INDIA%22%2C%22country_iso_code%22%3A%22IN%22%2C%22pincode%22%3A%22380054%22%2C%22state_code%22%3A%2224%22%2C%22city%22%3A%22Ahmedabad%22%2C%22state%22%3A%22Gujarat%22%7D',
    #     '_clck': '27fr4n%5E2%5Eg5h%5E0%5E2297',
    #     'f.session': 's%3AV6q03PbeY3tkL8CGxvpOkRDRisvr0PBy.xy3XSZTJKa21OTfjmlHdgoos92kcoYPLmkWHtmgkcRg',
    #     'x_jmp_session': 'si8zhAD5SaRilFoDOuKQ1',
    #     '_ga_01PYHVEWE6': 'GS2.1.s1777006259$o31$g1$t1777007232$j55$l0$h0',
    #     '_clsk': '1ruqkbo%5E1777007232695%5E11%5E1%5El.clarity.ms%2Fcollect',
    # }
    # headers = {
    #     'Accept': 'application/json, text/plain, */*',
    #     'Accept-Language': 'en-US,en;q=0.9',
    #     'Authorization': 'Bearer ***HIDDEN***',
    #     'Connection': 'keep-alive',
    #     'Sec-Fetch-Dest': 'empty',
    #     'Sec-Fetch-Mode': 'cors',
    #     'Sec-Fetch-Site': 'same-origin',
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    #     'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    #     'sec-ch-ua-mobile': '?0',
    #     'sec-ch-ua-platform': '"Windows"',
    #     'x-currency-code': 'INR',
    #     'x-fp-date': '20260424T051228Z',
    #     'x-fp-sdk-version': '1.9.4-13',
    #     'x-fp-signature': '***HIDDEN***',
    #     'x-location-detail': '{"country":"INDIA","country_iso_code":"IN","pincode":"380054","state_code":"24","city":"Ahmedabad","state":"Gujarat"}',
    #     # 'Cookie': '***HIDDEN***',
    # }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": "Bearer ***HIDDEN***",
        "User-Agent": "Mozilla/5.0",
        "x-location-detail": json.dumps(location_data),
    }
    URL = "https://www.metrorrl.com/ext/catalogueDiscovery/api/search/v1.0/products/"
    session = requests.Session()
    save_folder = os.path.join(db.PL_PAGESAVE, f"search_pages_{pincode}")
    os.makedirs(save_folder, exist_ok=True)
    # ⚠️ Query patterns
    queries = []
    # A → Z
    for c1 in string.ascii_uppercase:
        queries.append(c1)
    # AA → ZZ
    for c1 in string.ascii_uppercase:
        for c2 in string.ascii_uppercase:
            queries.append(c1 + c2)
    # AAA → ZZZ (⚠️ VERY HEAVY)
    for c1 in string.ascii_uppercase:
        for c2 in string.ascii_uppercase:
            for c3 in string.ascii_uppercase:
                queries.append(c1 + c2 + c3)
    print(f"🚀 Total queries: {len(queries)}")
    all_results = []
    seen_uids = set()
    # 🔥 Threading
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                search_with_pagination,
                q, session, headers, cookies, URL, save_folder,
                pincode, city, state, state_code
            )
            for q in queries
        ]
        for future in as_completed(futures):
            # try:
            #     future.result()
            # except Exception as e:
            #     print(f"❌ Thread error: {e}")
            try:
                items = future.result()
                for item in items:
                    uid = item.get("uid")
                    if uid and uid not in seen_uids:
                        seen_uids.add(uid)
                        all_results.append(item)
            except Exception as e:
                print(f"❌ Thread error: {e}")
    print(f"✅ DONE {pincode} → {len(all_results)} products")
    return all_results


# 🚀 MAIN FUNCTION
def main():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = f"""SELECT * FROM {db.pincode_table} WHERE status='pending' """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        print("❌ No pincode found")
        return
    for r in rows:
        try:
            pincode = r["pincode"]
            city = r["city"]
            state = r["state"]
            state_code = r["state_code"]
            print(f"\n🚀 Running for {pincode} - {city}")
            products = web_pl_pattern_wise(pincode, city, state, state_code)
            print(f"📦 Total products: {len(products)}")
            # ✅ Update DB
            conn = db.get_db_connection(db.db_name)
            cursor = conn.cursor()
            update_query = f"""UPDATE `{db.pincode_table}` SET status='done' WHERE pincode=%s"""
            cursor.execute(update_query, (pincode,))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"✅ Marked DONE → {pincode}")
        except Exception as e:
            print(f"❌ Error for {r}: {e}")


# ▶ RUN
if __name__ == "__main__":
    main()