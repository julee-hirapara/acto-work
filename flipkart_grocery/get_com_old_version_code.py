import os
import json
import time
import random
import pymysql
import requests
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
import db_config as db

# =====================================
# COMPETITOR OVERRIDES
# =====================================
TABLE_NAME = db.comp_availability_data_table
URL_COLUMN = "competitor_url"
HASH_COLUMN = "competitor_hash_id"
STOCK_COLUMN = "comp_stock_availability_status"

# =====================================
# CONFIG
# =====================================
MAX_PINCODE_WORKERS = 3
PDP_DELAY_RANGE = (2.5, 4.5)

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
# =====================================
# DB HELPERS
# =====================================


def get_pdps_for_pincode(pincode):
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(f"""
        SELECT
            id,
            competitor_hash_id AS hash_key,
            competitor_url AS url
        FROM {db.comp_availability_data_table}
        WHERE pincode = %s
          AND comp_stock_availability_status  = 'AVAILABLE'
          AND Status= 'SUCCESS' 
    """, (pincode,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows


def update_pincode_status(pincode, status):
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE {db.comp_availability_data_table}
        SET status = %s
        WHERE pincode = %s AND comp_stock_availability_status = 'AVAILABLE'
    """, (status, pincode))

    conn.commit()
    cur.close()
    conn.close()


def update_pdp_status(hash_key, stock_status, status="done"):
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE {db.comp_availability_data_table}
        SET stock_availability_status = %s,
            status = %s
        WHERE competitor_hash_id = %s
    """, (stock_status, status, hash_key))

    conn.commit()
    cur.close()
    conn.close()


# =====================================
# PLAYWRIGHT PINCODE SET
# =====================================

def save_page(page, pincode, status):
    base_dir = db.COMP_PINCODE_PAGESAVE
    status_dir = os.path.join(base_dir, status)
    os.makedirs(status_dir, exist_ok=True)
    try:
        html_path = os.path.join(status_dir, f"{pincode}.html")
        png_path = os.path.join(status_dir, f"{pincode}.png")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        page.screenshot(path=png_path, full_page=True)
        print(f"📄 Page saved [{status}] → {pincode}")
    except Exception as e:
        print(f"⚠️ Failed to save page for {pincode}: {e}")


def open_session_and_set_pincode(pincode):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        page = context.new_page()
        page.goto(
            "https://www.flipkart.com/grocery-supermart-store?marketplace=GROCERY",
            timeout=60000
        )
        # Close login popup
        try:
            page.locator("button:has-text('✕')").click(timeout=5000)
        except:
            pass
        # Enter pincode
        pincode_input = page.locator("input[placeholder='Enter Pincode Here']")
        pincode_input.wait_for(timeout=20000)
        pincode_input.fill(str(pincode))
        page.locator("text=CONTINUE").click()
        page.wait_for_timeout(5000)
        status = "SUCCESS"
        try:
            if page.locator(
                "text=Sorry! Currently not available in your pincode"
            ).is_visible(timeout=3000):
                status = "NOT_AVAILABLE_PINCODE"
            elif page.locator(
                "text=We have put a temporary hold on new orders"
            ).is_visible(timeout=3000):
                status = "TEMPORARILY_UNAVAILABLE"
            elif page.locator(
                "text=Please enter a valid pin code."
            ).is_visible(timeout=3000):
                status = "NOT_AVAILABLE_PINCODE"
        except:
            pass
        # 🔥 Save page for all cases
        save_page(page, pincode, status)
        cookies = None
        if status == "SUCCESS":
            cookies = context.cookies()
        browser.close()
        return cookies, status


# =====================================
# PDP API CALL
# =====================================
def fetch_pdp(cookies, page_uri, hash_key):
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
    FILE_PATH = f"{db.C_DATA_PAGESAVE}\\{hash_key}.json"
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
                    # continue
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
                    UPDATE {db.comp_availability_data_table}
                    SET Status = %s
                    WHERE competitor_hash_id = %s AND comp_stock_availability_status = 'AVAILABLE'
                    """,
                ("failed_api", hash_key),
            )
            conn.commit()
            cur.close()
            conn.close()
            print(f"✔ failed products for {hash_key}")
        except Exception as e:
            print(f"❌ Database error for {hash_key}: {e}")
        return

    try:
        product_status = response_json["RESPONSE"]["pageData"]["pageContext"]["trackingDataV2"]["productStatus"]
    except (KeyError, TypeError):
        return "UNKNOWN"
    # -------------------------------
    # Update DB
    # -------------------------------

    print("📦 Product Status:", product_status)
    try:
        conn = db.get_db_connection(db.db_name)
        cur = conn.cursor()
        cur.execute(
            f"""
                UPDATE {db.comp_availability_data_table}
                SET comp_stock_availability_status = %s,
                    status = %s
                WHERE competitor_hash_id = %s AND comp_stock_availability_status = 'AVAILABLE'
                """,
            (product_status, "done", hash_key),
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"✔ Saved all products for {hash_key}")
    except Exception as e:
        print(f"❌ Database error for {hash_key}: {e}")

def update_cookies(pincode, cookies_json, status):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    query = f"""
        UPDATE {db.comp_availability_data_table}
        SET cookies = %s,
            status = %s
        WHERE pincode = %s AND comp_stock_availability_status = 'AVAILABLE'
    """
    cursor.execute(query, (cookies_json, status, pincode))
    conn.commit()
    cursor.close()
    conn.close()
# =====================================
# MAIN WORKER (ONE PINCODE)
# =====================================
def process_pincode(pincode):
    print(f"\n📍 PINCODE START → {pincode}")
    cookies_list, status = open_session_and_set_pincode(pincode)
    if status != "SUCCESS":
        update_pincode_status(pincode, status)
        print(f"🚫 PINCODE FAILED → {pincode} ({status})")
        return
    cookies = {c["name"]: c["value"] for c in cookies_list}
    cookies_json = json.dumps(cookies)
    update_cookies(pincode, cookies_json, status)
    pdps = get_pdps_for_pincode(pincode)
    print(f"📦 PDP COUNT → {len(pdps)}")
    for row in pdps:
        if not row["url"]:
            continue
        page_uri = "/" + row["url"].split("flipkart.com/")[1]
        hash_key = row["hash_key"]
        fetch_pdp(cookies, page_uri, hash_key)
        time.sleep(random.uniform(*PDP_DELAY_RANGE))
    print(f"🎉 PINCODE DONE → {pincode}")



# =====================================
# ENTRY POINT
# =====================================
def main():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(f"""
            SELECT DISTINCT pincode
        FROM {db.comp_availability_data_table}
        WHERE status = 'failed_api'
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    pincodes = [r["pincode"] for r in rows]
    print(f"📌 TOTAL PINCODES → {len(pincodes)}")

    with ThreadPoolExecutor(max_workers=MAX_PINCODE_WORKERS) as executor:
        futures = [executor.submit(process_pincode, p) for p in pincodes]

        for f in as_completed(futures):
            f.result()

    print("\n🎯 ALL PINCODES COMPLETED")


# def mark_no_pincode_products():
#     conn = db.get_db_connection(db.db_name)
#     cur = conn.cursor()
#     cur.execute(f"""
#         UPDATE {db.availability_data_table} a
#         JOIN {db.pincode_table} c
#           ON a.pincode = c.pincode
#         SET a.status = 'NO_PINCODE'
#         WHERE c.status IN ('NOT_AVAILABLE_PINCODE', 'TEMPORARILY_UNAVAILABLE')
#           AND a.status = 'PENDING'
#     """)
#     conn.commit()
#     print(f"🚫 Marked {cur.rowcount} products as NO_PINCODE")
#     cur.close()
#     conn.close()


if __name__ == "__main__":
    main()

