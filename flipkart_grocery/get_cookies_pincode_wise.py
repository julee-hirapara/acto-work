import os
import json
import pymysql
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
import db_config as db
import threading


thread_local = threading.local()

def get_browser():
    if not hasattr(thread_local, "playwright"):
        thread_local.playwright = sync_playwright().start()

    if not hasattr(thread_local, "browser"):
        thread_local.browser = thread_local.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

    return thread_local.browser

# ==========================
# UTILS
# ==========================
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def save_page(page, pincode, status):
    base_dir = db.PINCODE_PAGESAVE
    status_dir = os.path.join(base_dir, status)
    ensure_dir(status_dir)

    try:
        html_path = os.path.join(status_dir, f"{pincode}.html")
        png_path = os.path.join(status_dir, f"{pincode}.png")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())

        page.screenshot(path=png_path, full_page=True)

        print(f"📄 Page saved [{status}] → {pincode}")

    except Exception as e:
        print(f"⚠️ Failed to save page for {pincode}: {e}")


def cookies_to_json(cookies):
    return json.dumps({c["name"]: c["value"] for c in cookies})


# ==========================
# PLAYWRIGHT
# ==========================
def set_flipkart_pincode(pincode):
    browser = get_browser()
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        viewport={"width": 1366, "height": 768}
    )
    page = context.new_page()
    try:
        page.goto(
            "https://www.flipkart.com/grocery-supermart-store?marketplace=GROCERY",
            timeout=60000
        )
        # Close login popup
        try:
            page.locator("button:has-text('✕')").click(timeout=3000)
        except:
            pass
        # Enter pincode
        pincode_input = page.locator("input[placeholder='Enter Pincode Here']")
        pincode_input.wait_for(timeout=15000)
        pincode_input.fill(str(pincode))
        page.locator("text=CONTINUE").click()
        page.wait_for_timeout(4000)
        status = "SUCCESS"
        if page.locator(
            "text=Sorry! Currently not available in your pincode"
        ).is_visible():
            status = "NOT_AVAILABLE_PINCODE"
        elif page.locator(
            "text=We have put a temporary hold on new orders"
        ).is_visible():
            status = "TEMPORARILY_UNAVAILABLE"
        elif page.locator(
            "text=Please enter a valid pin code."
        ).is_visible():
            status = "NOT_AVAILABLE_PINCODE"
        # Save page always
        save_page(page, pincode, status)
        cookies = context.cookies() if status == "SUCCESS" else None
        return cookies, status
    finally:
        context.close()

# ==========================
# DB FUNCTIONS
# ==========================
def get_pending_pincodes():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    query = f"""
        SELECT DISTINCT pincode
        FROM {db.pincode_table}
        WHERE status = 'FAILED'
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [row["pincode"] for row in rows]


def update_cookies(pincode, cookies_json, status):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()

    query = f"""
        UPDATE {db.pincode_table}
        SET cookies = %s,
            status = %s
        WHERE pincode = %s
    """

    cursor.execute(query, (cookies_json, status, pincode))
    conn.commit()

    cursor.close()
    conn.close()


# ==========================
# THREAD WORKER
# ==========================
def process_pincode(pincode):
    try:
        print(f"🔄 Processing pincode: {pincode}")

        cookies, status = set_flipkart_pincode(pincode)

        if status != "SUCCESS":
            update_cookies(pincode, None, status)
            print(f"🚫 {status} → {pincode}")
            return

        cookies_json = cookies_to_json(cookies)
        update_cookies(pincode, cookies_json, "SUCCESS")

        print(f"✅ Cookies saved → {pincode}")

    except Exception as e:
        update_cookies(pincode, None, "FAILED")
        print(f"❌ Failed {pincode}: {e}")


# ==========================
# MAIN
# ==========================
def main():
    pincodes = get_pending_pincodes()
    print(f"📌 Total pincodes: {len(pincodes)}")
    MAX_WORKERS = 3  # ⚠️ DO NOT increase (Playwright heavy)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_pincode, pincode)
            for pincode in pincodes
        ]
        for future in as_completed(futures):
            future.result()
    print("🎉 All pincodes processed")


if __name__ == "__main__":
    main()
