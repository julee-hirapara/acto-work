import os
import pymysql
import requests
import json
import urllib.parse
import hashlib
from datetime import datetime
import time
import db_config_1 as db


# ---------------- FETCH + LOCK RECORDS ----------------
def fetch_and_lock_products():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()

    # Fetch locked rows
    fetch_query = f""" SELECT * FROM {db.product_link_table} WHERE status = 'pending' AND pincode='380001' LIMIT 1 """
    cursor.execute(fetch_query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# ---------------- HEADERS + COOKIES ----------------
def build_headers_cookies(location_data):
    print(location_data)
    # ✅ Remove signature safely (without modifying original)
    clean_location = location_data.copy()
    clean_location.pop("x-fp-signature", None)

    print("Cleaned:", clean_location)
    encoded_location = urllib.parse.quote(json.dumps(clean_location))

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Authorization": f"Bearer ***HIDDEN***",
        "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
        "x-currency-code": "INR",
        "x-fp-date": "20260410T051646Z",
        "x-fp-sdk-version": "1.9.4-13",
        "x-fp-signature": "***HIDDEN***",
        "x-location-detail": json.dumps(clean_location),
        # "x-fp-date": "20260409T075347Z",
        # "x-fp-date": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
        # "x-fp-sdk-version": "1.9.4-13",
        # "x-fp-signature": location_data.get("x-fp-signature"),
        # "x-currency-code": "INR"
    }
    cookies = {
        "app_location_details": encoded_location
    }
    return headers, cookies

# ---------------- PDP API ----------------
def fetch_pdp(product_slug, headers, cookies, hash_key, pincode, retries=3):
    url = f"https://www.metrorrl.com/ext/catalogueDiscovery/api/search/v1.0/products/{product_slug}/"
    folder_path = os.path.join(db.PDP_PAGESAVE, pincode)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{hash_key}_product_details.json")
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            # res = requests.get(url, proxies=proxy, cookies=cookies, timeout=15)
            print(res)
            # print(res.headers)
            if res.status_code == 200:
                pdp_data = res.json()
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(pdp_data, f, ensure_ascii=False, indent=2)
                return
            else:
                print(f"⚠️ Status {res.status_code} | Attempt {attempt+1}")
        except Exception as e:
            print(f"⚠️ Retry {attempt+1}: {e}")
        time.sleep(2)
    return None

# ---------------- LADDER PRICE ----------------
def fetch_ladder_price(product_slug, headers, cookies, store_id, hash_key, pincode, retries=3):
    url = "https://www.metrorrl.com/api/service/application/cart/v1.0/available-ladder-prices"
    params = {
        "slug": product_slug,
        "store_id": store_id
    }
    # Editable location 👇
    location = {
        "country": "INDIA",
        "country_iso_code": "IN",
        "pincode": "380001",
        "state_code": "24",
        "city": "Ahmedabad",
        "state": "Gujarat"
    }
    # Encode location for cookie
    encoded_location = urllib.parse.quote(json.dumps(location))
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Authorization": "Bearer ***HIDDEN***",
        "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
        "x-currency-code": "INR",
        "x-fp-date": "20260410T052103Z",
        "x-fp-sdk-version": "1.9.4-13",
        "x-fp-signature": "***HIDDEN***",
        "x-location-detail": json.dumps(location)
    }

    cookies = {
        "app_location_details": encoded_location
    }
    folder_path = os.path.join(db.PDP_PAGESAVE, pincode)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{hash_key}_add_price_data.json")
    for attempt in range(retries):
        proxy = {
            "http": f'http://{db.proxy_token}:super=true@proxy.scrape.do:8080',
            "https": f'http://{db.proxy_token}:super=true@proxy.scrape.do:8080',
        }
        try:
            # res = requests.get(url, proxies=proxy, params=params, timeout=15)
            res = requests.get(url, headers=headers, cookies=cookies, params=params, timeout=15)
            print(res)
            if res.status_code == 200:
                pdp_data = res.json()
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(pdp_data, f, ensure_ascii=False, indent=2)
            else:
                print(f"⚠️ Status {res.status_code} | Attempt {attempt + 1}")
        except Exception as e:
            print(f"⚠️ Retry {attempt + 1}: {e}")
        time.sleep(2)
    return None

# ---------------- UPDATE DB ----------------
def update_product(row_id, pdp_data, price_data, status):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    query = f"""
    UPDATE {db.product_link_table}
    SET status = %s,
        pdp_response = %s,
        price_response = %s,
        updated_at = NOW()
    WHERE id = %s
    """
    cursor.execute(query, (
        status,
        json.dumps(pdp_data) if pdp_data else None,
        json.dumps(price_data) if price_data else None,
        row_id
    ))
    conn.commit()
    cursor.close()
    conn.close()

# ---------------- MAIN PROCESS ----------------
def process_products():
    rows = fetch_and_lock_products()
    if not rows:
        print("✅ No pending products")
        return
    for row in rows:
        try:
            product_slug = row["product_slug"]
            location_data = json.loads(row["json_dict"])
            store_id = row["store_id"]
            hash_key = row["hash_key"]
            pincode = row["pincode"]
            headers, cookies = build_headers_cookies(location_data)
            print(f"🚀 Processing: {product_slug}")
            # PDP
            pdp_data = fetch_pdp(product_slug, headers, cookies, hash_key, pincode)
            # if not pdp_data:
            #     update_product(row["id"], None, None, "failed")
            #     continue
            # Ladder Price
            price_data = fetch_ladder_price(product_slug, headers, cookies, store_id, hash_key, pincode)
            # Save
            # update_product(row["id"], pdp_data, price_data, "done")
            print(f"✅ Done: {product_slug}")
        except Exception as e:
            print(f"❌ Error: {e}")
            # update_product(row["id"], None, None, "failed")

# ---------------- RUN ----------------
if __name__ == "__main__":
    process_products()