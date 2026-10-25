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


# 🧹 Clean filename
def clean_name(name):
    return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_')


# 🔁 Pagination function (NOW PROPERLY PARAMETERIZED)
def search_with_pagination(query, session, headers, cookies, URL, save_folder):
    print(f"🚀 Start query: {query}")
    all_items = []
    page_id = None
    page_no = 1
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
            if response.status_code == 200:
                # 💾 Save file
                data = response.json()
                file_path = os.path.join(save_folder, f"{query}_page_{page_no}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"❌ {query} error: {e}")
            break
        items = data.get("items", [])
        if not items:
            break
        all_items.extend(items)
        # 💾 Save file
        file_path = os.path.join(save_folder, f"{query}_page_{page_no}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        page_info = data.get("page", {})
        if not page_info.get("has_next"):
            break
        page_id = page_info.get("next_id")
        if not page_id:
            break
        page_no += 1
        time.sleep(0.1)
    return all_items


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
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(search_with_pagination, q, session, headers, cookies, URL, save_folder)
            for q in queries
        ]
        for future in as_completed(futures):
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
    query = f"""SELECT * FROM {db.pincode_table} WHERE pincode = '700099' """
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