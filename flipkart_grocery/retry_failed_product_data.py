import json
import time
import random
import hashlib
import os
import pymysql
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import db_config as db

# ==================================
# CONFIG
# ==================================
MAX_WORKERS = 4
RETRY_DELAY = (2, 4)

ROME_ENDPOINTS = [
    "https://2.rome.api.flipkart.com/api/4/page/fetch",
    "https://1.rome.api.flipkart.com/api/4/page/fetch",
]

HEADERS = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://www.flipkart.com',
        'Referer': 'https://www.flipkart.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'X-User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 FKUA/website/42/website/Desktop',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

# ==================================
# HASH KEY
# ==================================
def generate_hash_key(product_name, targeted_sku, pincode):
    raw = f"{product_name}|{targeted_sku}|{pincode}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

# ==================================
# DB FETCH
# ==================================
def get_retry_products():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(f"""
        SELECT id, product_name, targeted_sku, pincode, url
        FROM {db.availability_data_table}
        WHERE status = 'failed_api'
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_cookies_by_pincode():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(f"""
        SELECT pincode, cookies
        FROM {db.pincode_table}
        WHERE status = 'SUCCESS'
          AND cookies IS NOT NULL
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return {r["pincode"]: json.loads(r["cookies"]) for r in rows}

# ==================================
# API CALL
# ==================================
def retry_api(product, cookies):
    product_id = product["id"]
    pincode = product["pincode"]

    hash_key = generate_hash_key(
        product["product_name"],
        product["targeted_sku"],
        pincode
    )

    page_uri = "/" + product["url"].split("flipkart.com/")[1]
    file_path = f"{db.DATA_PAGESAVE}\\{hash_key}.json"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    payload = {
        "pageUri": page_uri,
        "pageContext": {
            "paginatedFetch": True,
            "pageNumber": 2,
            "fetchAllPages": False,
            "paginationContextMap": {
                "nps": {"pricing": "null"},
                "dj": {"context": None, "pageType": "PRODUCT_PAGE"},
            },
        },
    }

    response_json = None
    blocked = set()

    for attempt in range(2):
        for api_url in ROME_ENDPOINTS:
            if api_url in blocked:
                continue
            try:
                print(f"🔁 RETRY product_id={product_id} → {api_url}")
                time.sleep(5 + random.uniform(1, 3))

                resp = requests.post(
                    api_url,
                    headers=HEADERS,
                    cookies=cookies,
                    json=payload,
                    timeout=30
                )

                if resp.status_code == 406:
                    blocked.add(api_url)
                    continue

                if resp.status_code != 200:
                    continue

                if "productStatus" not in resp.text:
                    print("⚠️ productStatus key missing")
                    # continue

                response_json = resp.json()
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(response_json, f, indent=2)

                break
            except Exception as e:
                print(f"❌ API error: {e}")

        if response_json:
            break

    if not response_json:
        print(f"❌ STILL FAILED → product_id={product_id}")
        return

    try:
        product_status = response_json["RESPONSE"]["pageData"]["pageContext"] \
            ["trackingDataV2"]["productStatus"]
    except Exception:
        product_status = "UNKNOWN"

    # ==================================
    # DB UPDATE
    # ==================================
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE {db.availability_data_table}
        SET hash_key = %s,
            stock_availability_status = %s,
            status = 'DONE'
        WHERE id = %s
    """, (hash_key, product_status, product_id))

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ RETRY SUCCESS → product_id={product_id}")

# ==================================
# THREAD WORKER
# ==================================
def worker(products, cookies_by_pincode):
    for p in products:
        cookies = cookies_by_pincode.get(p["pincode"])
        if not cookies:
            continue
        retry_api(p, cookies)
        time.sleep(random.uniform(*RETRY_DELAY))

# ==================================
# MAIN
# ==================================
def main():
    products = get_retry_products()
    if not products:
        print("⚠️ No failed_api products to retry")
        return

    cookies_by_pincode = get_cookies_by_pincode()

    bucket = defaultdict(list)
    for p in products:
        bucket[p["pincode"]].append(p)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(worker, plist, cookies_by_pincode)
            for plist in bucket.values()
        ]
        for f in as_completed(futures):
            f.result()

    print("🎉 RETRY COMPLETED")

if __name__ == "__main__":
    main()
