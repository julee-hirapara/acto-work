import os
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pymysql
from datetime import datetime
import db_config_1 as db

# ============================================================
# HEADERS
# ============================================================

HEADERS = {
    "sec-ch-ua-platform": '"Windows"',
    "Referer": "https://www.petsupermarket.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    "sec-ch-ua": (
        '"Google Chrome";v="153", '
        '"Not_A Brand";v="8", '
        '"Chromium";v="153"'
    ),
    "sec-ch-ua-mobile": "?0",
}

# ============================================================
# EXTRACT POWERREVIEWS CONFIG
# ============================================================

def extract_powerreview_config(html):
    powerreview_match = re.search(r"window\.POWERREVIEW\s*=\s*\{(.*?)\};",
        html,re.IGNORECASE | re.DOTALL,)
    if not powerreview_match:
        return None
    powerreview_block = powerreview_match.group(1)
    api_key_match = re.search(r'api_key\s*:\s*["\']([^"\']+)["\']', powerreview_block,
        re.IGNORECASE,)
    merchant_id_match = re.search(
        r'merchant_id\s*:\s*["\']([^"\']+)["\']',
        powerreview_block, re.IGNORECASE,)
    locale_match = re.search(
        r'locale\s*:\s*["\']([^"\']+)["\']',
        powerreview_block,re.IGNORECASE,)
    if not api_key_match or not merchant_id_match:
        return None
    return {
        "api_key": api_key_match.group(1),
        "merchant_id": merchant_id_match.group(1),
        "locale": locale_match.group(1) if locale_match else "en_US",
    }

# ============================================================
# UPDATE SQL
# ============================================================

def update_review_summary(cursor, table_name, row_id, reviews):
    query = f""" UPDATE `{table_name}` SET `reviews` = %s WHERE `id` = %s """
    review_json = json.dumps(reviews,ensure_ascii=False,)
    cursor.execute( query,(review_json, row_id),)

def process_record(row, index, total):
    row_id = row["id"]
    hash_id = row["hash_id"]
    pid = row["pid"]
    name = row["name"]
    print(f"[{index}/{total}] Processing: {pid}")
    # ------------------------------------------------
    # 1. FIND PAGESAVE
    # ------------------------------------------------
    file_path = os.path.join(db.PDP_PAGESAVE,f"{hash_id}.html")
    if not os.path.exists(file_path):
        return {
            "status": "pagesave_not_found",
            "id": row_id,
            "hash_id": hash_id,
            "pid": pid,
        }
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        return {
            "status": "error",
            "id": row_id,
            "hash_id": hash_id,
            "pid": pid,
            "error": str(e),
        }
    # ------------------------------------------------
    # 2. EXTRACT POWERREVIEW CONFIG
    # ------------------------------------------------
    config = extract_powerreview_config(html)
    if not config:
        return {
            "status": "config_not_found",
            "id": row_id,
            "hash_id": hash_id,
            "pid": pid,
        }
    api_key = config["api_key"]
    merchant_id = config["merchant_id"]
    locale = config["locale"]
    # ------------------------------------------------
    # 3. CALL POWERREVIEWS
    # ------------------------------------------------
    url = f"https://display.powerreviews.com/m/{merchant_id}/l/{locale}/product/{pid}/reviews"
    params = {
        "apikey": api_key,
        "_noconfig": "true",
    }
    try:
        response = requests.get(url,params=params, timeout=60)
        print(f"[{index}/{total}] PID={pid} | Status={response.status_code}")
        if response.status_code != 200:
            return {
                "status": "api_failed",
                "id": row_id,
                "hash_id": hash_id,
                "pid": pid,
                "status_code": response.status_code,
            }
        api_data = response.json()

    except requests.RequestException as e:
        return {
            "status": "api_failed",
            "id": row_id,
            "hash_id": hash_id,
            "pid": pid,
            "error": str(e),
        }

    except ValueError as e:
        return {
            "status": "api_failed",
            "id": row_id,
            "hash_id": hash_id,
            "pid": pid,
            "error": str(e),
        }
    # ------------------------------------------------
    # 4. SAVE API JSON
    # ------------------------------------------------
    filepath = os.path.join(db.review_folder,f"{hash_id}.json")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(api_data,f,ensure_ascii=False,indent=2)
    except Exception as e:
        print(f"⚠️ JSON save failed for {pid}: {e}")
    # ------------------------------------------------
    # 5. EXTRACT REVIEWS
    # ------------------------------------------------
    reviews = []
    results = api_data.get("results", [])
    for result in results:
        api_reviews = result.get("reviews", [])
        for review in api_reviews:
            details = review.get("details", {})
            metrics = review.get("metrics", {})
            created_date = details.get("created_date")
            review_date = None
            if created_date:
                try:
                    review_date = datetime.fromtimestamp(created_date/1000).strftime("%Y-%m-%d")
                except Exception:
                    review_date = None

            reviews.append({
                "review_name": details.get("nickname") or "N/A",
                "review_title": details.get("headline") or "N/A",
                "review_content": details.get("comments") or "N/A",
                "rating": metrics.get("rating"),
                "review_date": review_date,
                "verified": (
                    review
                    .get("badges", {})
                    .get("is_verified_buyer", False)
                ),
            })

    return {
        "status": "success",
        "id": row_id,
        "hash_id": hash_id,
        "pid": pid,
        "reviews": reviews,
        "review_count": len(reviews),
    }

# ============================================================
# MAIN
# ============================================================
def main():
    MAX_WORKERS = 15
    connection = db.get_db_connection(db.db_name)
    try:
        with connection.cursor() as cursor:
            # ============================================
            # GET DATA
            # ============================================
            query = f"""
                SELECT `id`, `hash_id`, `pid`, `name` FROM `{db.data_table}`
                WHERE `hash_id` IS NOT NULL AND `pid` IS NOT NULL
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            total = len(rows)
            print("=" * 100)
            print(f"Total SQL records: {total}")
            print(f"Threads: {MAX_WORKERS}")
            print("=" * 100)
            processed = 0
            pagesave_not_found = 0
            config_not_found = 0
            api_failed = 0
            reviews_found = 0
            no_reviews = 0
            # ============================================
            # MULTITHREADING STARTS HERE
            # ============================================
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(process_record,row,index, total): row
                    for index, row in enumerate(rows, start=1)
                }
                for future in as_completed(futures):
                    try:
                        result = future.result()
                    except Exception as e:
                        print(f"❌ Thread error: {e}")
                        continue
                    # ====================================
                    # HANDLE RESULT
                    # ====================================
                    if result["status"] == "pagesave_not_found":
                        pagesave_not_found += 1
                        continue
                    if result["status"] == "config_not_found":
                        config_not_found += 1
                        continue
                    if result["status"] == "api_failed":
                        api_failed += 1
                        continue
                    if result["status"] == "success":
                        reviews = result["reviews"]
                        if not reviews:
                            no_reviews += 1
                            continue
                        reviews_found += len(reviews)
                        update_review_summary(
                            cursor=cursor,
                            table_name=db.data_table,
                            row_id=result["id"],
                            reviews=reviews
                        )
                        processed += 1
                        if processed % 100 == 0:
                            connection.commit()
                            print(f"💾 Commit completed: {processed}")
            # ============================================
            # FINAL COMMIT
            # ============================================
            connection.commit()
            # ============================================
            # SUMMARY
            # ============================================
            print("=" * 100)
            print("FINAL SUMMARY")
            print("=" * 100)
            print(f"Total records       : {total}")
            print(f"Processed           : {processed}")
            print(f"Reviews found       : {reviews_found}")
            print(f"No reviews          : {no_reviews}")
            print(f"PageSave not found  : {pagesave_not_found}")
            print(f"Config not found    : {config_not_found}")
            print(f"API failed          : {api_failed}")
            print("=" * 100)
    except Exception as e:
        connection.rollback()
        print("=" * 100)
        print("❌ MAIN ERROR")
        print(e)
        print("=" * 100)
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()