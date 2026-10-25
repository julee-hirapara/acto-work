import json
import time
import random
import pymysql
import hashlib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import db_config as db
import os
import requests


# ==================================
# HASH KEY
# ==================================
def generate_hash_key(product_name, targeted_sku, pincode):
    raw = f"{product_name}|{targeted_sku}|{pincode}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ==================================
# DB FETCH
# ==================================
def get_pincodes_with_cookies():
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
    return rows


def get_all_pending_products(pincodes):
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    format_strings = ",".join(["%s"] * len(pincodes))
    cur.execute(f"""
        SELECT id, product_name, targeted_sku, pincode, url
        FROM {db.availability_data_table}
        WHERE status = 'PENDING'
          AND hash_key IS NULL
          AND pincode IN ({format_strings})
    """, tuple(pincodes))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def update_pincode_status_if_done(pincode):
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT COUNT(*)
        FROM {db.availability_data_table}
        WHERE pincode = %s
          AND status IN ('PENDING', 'PROCESSING')
        """,
        (pincode,)
    )
    remaining = cur.fetchone()[0]
    if remaining == 0:
        cur.execute(
            f"""
            UPDATE {db.pincode_table}
            SET status = 'DONE'
            WHERE pincode = %s
            """,
            (pincode,)
        )
        conn.commit()
        print(f"📍 Pincode {pincode} marked DONE")
    cur.close()
    conn.close()


# ==================================
# BUILD COOKIE → PRODUCTS MAP
# ==================================
def build_cookie_map(pincode_rows, product_rows):
    cookie_by_pincode = {
        row["pincode"]: row["cookies"]
        for row in pincode_rows
    }
    cookie_map = defaultdict(list)
    for product in product_rows:
        cookie = cookie_by_pincode.get(product["pincode"])
        if not cookie:
            continue
        cookie_map[cookie].append(product)
    return cookie_map


def call_flipkart_api(cookies, page_uri, product_id, product_name, targeted_sku, pincode):
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()
    cur.execute(
        f"""
        UPDATE {db.availability_data_table}
        SET status = 'PROCESSING'
        WHERE id = %s AND status = 'PENDING'
        """,
        (product_id,)
    )
    if cur.rowcount == 0:
        # already processed by another thread
        cur.close()
        conn.close()
        return
    conn.commit()
    cur.close()
    conn.close()

    hash_key = generate_hash_key(product_name, targeted_sku, pincode)
    # ----- existing request + JSON save logic stays EXACTLY SAME -----
    headers = {
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
    FILE_PATH = f"{db.DATA_PAGESAVE}\\{hash_key}.json"
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                response_json = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Corrupt JSON, refetching")
            os.remove(FILE_PATH)
            response_json = None
    else:
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
        ROME_ENDPOINTS = [
            "https://2.rome.api.flipkart.com/api/4/page/fetch",
            "https://1.rome.api.flipkart.com/api/4/page/fetch",
        ]
        response_json = None
        blocked_endpoints = set()
        for attempt in range(2):
            for api_url in ROME_ENDPOINTS:
                # ⛔ Skip blocked endpoints
                if api_url in blocked_endpoints:
                    print(f"⏭ Skipping blocked endpoint {api_url}")
                    continue
                try:
                    print(f"🔁 Attempt {attempt + 1} → {api_url}")
                    time.sleep(5 + random.uniform(2, 6))
                    resp = requests.post(
                        api_url,
                        headers=headers,
                        cookies=cookies,
                        json=payload,
                        timeout=30,
                    )
                    # 🚫 Hard-block logic
                    if resp.status_code == 406:
                        print(f"🚫 {api_url} blocked with 406 — removing from retries")
                        blocked_endpoints.add(api_url)
                        continue
                    if resp.status_code != 200:
                        print(f"⚠️ HTTP {resp.status_code}")
                        continue
                    if "productStatus" not in resp.text:
                        print("⚠️ productStatus key missing")
                        continue
                    # ✅ success
                    response_json = resp.json()
                    with open(FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(response_json, f, ensure_ascii=False, indent=2)
                    print(f"✅ Success from {api_url}")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
            if response_json:
                break
            # 🛑 Stop early if all endpoints blocked
            if len(blocked_endpoints) == len(ROME_ENDPOINTS):
                print("❌ All endpoints blocked, aborting retries")
                break
            time.sleep(10)
        if response_json is None:
            print(f"❌ API failed after retries :: {hash_key}")
            try:
                conn = db.get_db_connection(db.db_name)
                cur = conn.cursor()
                cur.execute(
                    f"""
                        UPDATE {db.availability_data_table}
                        SET hash_key = %s,
                            status = 'failed_api'
                        WHERE id = %s
                        """,
                    (hash_key, product_id)
                )
                conn.commit()
                cur.close()
                conn.close()
                print(f"✔ failed products for {hash_key}")
            except Exception as e:
                print(f"❌ Database error for {hash_key}: {e}")
            return
    try:
        product_status = response_json["RESPONSE"]["pageData"]["pageContext"] \
            ["trackingDataV2"]["productStatus"]
    except Exception:
        product_status = "UNKNOWN"

    # =========================
    # UPDATE PRODUCT ROW
    # =========================
    try:
        conn = db.get_db_connection(db.db_name)
        cur = conn.cursor()
        cur.execute(
            f"""
            UPDATE {db.availability_data_table}
            SET hash_key = %s,
                stock_availability_status = %s,
                status = 'DONE'
            WHERE id = %s
            """,
            (hash_key, product_status, product_id)
        )
        conn.commit()
        affected = cur.rowcount
        cur.close()
        conn.close()
        if affected == 0:
            print(f"ℹ DB already updated | product_id={product_id}")
        else:
            print(f"✔ DB updated | product_id={product_id}")

    except Exception as e:
        print(f"❌ PRODUCT DB update failed | product_id={product_id}: {e}")
        return
    # =========================
    # UPDATE PINCODE STATUS
    # =========================
    try:
        update_pincode_status_if_done(pincode)
    except Exception as e:
        print(f"⚠️ Pincode status update failed | pincode={pincode}: {e}")


# ==================================
# THREAD WORKER
# ==================================
def process_cookie_group(cookie_str, products):
    cookies = json.loads(cookie_str)

    for product in products:
        page_uri = "/" + product["url"].split("flipkart.com/")[1]

        print(f"🍪 Processing product_id={product['id']}")

        try:
            call_flipkart_api(
                cookies=cookies,
                page_uri=page_uri,
                product_id=product["id"],
                product_name=product["product_name"],
                targeted_sku=product["targeted_sku"],
                pincode=product["pincode"],
            )
        except Exception as e:
            print(f"❌ ERROR product_id={product['id']}: {e}")

        time.sleep(2 + random.uniform(1, 2))

# def process_cookie_group(cookie_str, products):
#     cookies = json.loads(cookie_str)
#
#     conn = db.get_db_connection(db.db_name)
#     cur = conn.cursor()
#
#     for product in products:
#         page_uri = "/" + product["url"].split("flipkart.com/")[1]
#
#         print(f"🍪 Processing product_id={product['id']}")
#
#         try:
#             hash_key = generate_hash_key(
#                 product["product_name"],
#                 product["targeted_sku"],
#                 product["pincode"]
#             )
#             product_status = call_flipkart_api(cookies, page_uri, hash_key)
#
#             if not product_status:
#                 continue
#
#             hash_key = generate_hash_key(
#                 product["product_name"],
#                 product["targeted_sku"],
#                 product["pincode"]
#             )
#
#             cur.execute(
#                 f"""
#                 UPDATE {db.availability_data_table}
#                 SET hash_key = %s,
#                     stock_availability_status = %s,
#                     status = 'done'
#                 WHERE id = %s
#                 """,
#                 (hash_key, product_status, product["id"])
#             )
#             conn.commit()
#
#             print(f"✅ Saved hash_key → {hash_key}")
#
#         except Exception as e:
#             print(f"❌ ERROR product_id={product['id']}: {e}")
#
#         time.sleep(2 + random.uniform(1, 2))
#
#     cur.close()
#     conn.close()


# ==================================
# MAIN
# ==================================
def main():
    pincode_rows = get_pincodes_with_cookies()
    if not pincode_rows:
        print("⚠️ No cookies found")
        return

    pincodes = [r["pincode"] for r in pincode_rows]
    product_rows = get_all_pending_products(pincodes)

    print(f"📦 Products pending: {len(product_rows)}")

    cookie_map = build_cookie_map(pincode_rows, product_rows)
    print(f"🍪 Cookie sessions: {len(cookie_map)}")

    MAX_WORKERS = min(4, len(cookie_map))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_cookie_group, cookie, products)
            for cookie, products in cookie_map.items()
        ]

        for f in as_completed(futures):
            f.result()

    print("🎉 ALL DONE")

def mark_no_pincode_products():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE {db.availability_data_table} a
        JOIN {db.pincode_table} c
          ON a.pincode = c.pincode
        SET a.status = 'NO_PINCODE'
        WHERE c.status IN ('NOT_AVAILABLE_PINCODE', 'TEMPORARILY_UNAVAILABLE')
          AND a.status = 'PENDING'
    """)
    conn.commit()
    print(f"🚫 Marked {cur.rowcount} products as NO_PINCODE")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
    # mark_no_pincode_products()
