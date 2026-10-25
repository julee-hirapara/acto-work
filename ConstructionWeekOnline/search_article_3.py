import gzip
import hashlib
import random
from urllib.parse import quote, urlencode
from parsel import Selector
import pymysql
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import db_config_1 as db
# from curl_cffi import requests
import requests
from datetime import date, datetime, timedelta
import using_playwright_getting_token as dt
from threading import Lock
import threading
import time
import os
import sys

LAST_PROGRESS = time.time()
PROGRESS_LOCK = threading.Lock()
def update_progress():
    global LAST_PROGRESS
    with PROGRESS_LOCK:
        LAST_PROGRESS = time.time()

global_token = dt.get_new_token_from_browser()
token_lock = Lock()

today = date.today()
START_DATE = today - timedelta(days=2)   # D-2
# END_DATE = today - timedelta(days=1)     # D-1
END_DATE = today

print(START_DATE, END_DATE)

def sha256_hash(text):
    if not text:
        return None
    return hashlib.sha256(text.encode()).hexdigest()


def update_status(keyword, record_id, status):
    conn = db.get_db_connection(db.db_name)
    with conn.cursor() as cur:
        cur.execute(f"UPDATE {db.input_table} SET status=%s WHERE id=%s",
            (status, record_id))
        print(f"{keyword} :: {status} Status updated successfully ")
    conn.commit()

def insert_articles(data_list):
    if not data_list:
        return
    conn = db.get_db_connection(db.db_name)
    try:
        with conn.cursor() as cur:
            columns = ", ".join(data_list[0].keys())
            placeholders = ", ".join(["%s"] * len(data_list[0]))
            query = f"""
                INSERT IGNORE INTO {db.link_table}
                ({columns})
                VALUES ({placeholders})
            """
            values = [tuple(d.values()) for d in data_list]
            cur.executemany(query, values)
        conn.commit()
    finally:
        conn.close()


def fetch_search_data(keyword, record_id):
    global global_token
    if keyword is None:
        update_status(keyword, record_id, "No_keyword")
        update_progress()
        return
    hash_key = sha256_hash(keyword)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': 'https://www.constructionweekonline.com/',
        'sec-ch-device-memory': '32',
        'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Not;A=Brand";v="8.0.0.0", "Chromium";v="150.0.7871.127", "Google Chrome";v="150.0.7871.127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    }
    page = 1
    retry = 0
    all_articles = []
    # while True:
    while retry < 3:
        update_progress()  # <-- add here
        with token_lock:
            current_token = global_token

        cookies = {
            "datadome": current_token
        }
        if keyword == 'CIA':
            update_status(keyword, record_id, "keyword_not_found")
            break
        if page == 1:
            url = "https://www.constructionweekonline.com/"
            params = {
                "s": keyword,
                "cat_name": ""
            }
            # file_path = os.path.join(db.PL_pagesave_path, f"{hash_key}.html")
            # if os.path.exists(file_path):
            #     with open(file_path, "r", encoding="utf-8") as f:
            #         html = f.read()
            # file_path = os.path.join(db.PL_pagesave_path, f"{hash_key}.html.gz")
            # if os.path.exists(file_path):
            #     with gzip.open(file_path, "rt", encoding="utf-8") as f:
            #         html = f.read()
            # else:
            # # Build the final URL with query parameters
            final_url = f"{url}?{urlencode(params)}"
            headers['referer']=final_url
            scrape_params = {
                "url": final_url,
                "token": db.proxy_token,
                "super": "true"
            }
            try:
                response = requests.get("http://api.scrape.do/",params=scrape_params,
                                        verify=False,timeout=(20, 90))
                html = response.text
            except requests.exceptions.RequestException as e:
                print(f"{keyword} :: Request failed: {e}")
                update_status(keyword, record_id,"pending")
                update_progress()
                return
            # response = requests.get("http://api.scrape.do/",params=scrape_params, verify=False,timeout=90)
            # time.sleep(random.uniform(1, 2))
            # response = requests.get(
            #     # final_url,
            #     'https://www.constructionweekonline.com/', params=params,
            #     cookies=cookies,
            #     headers=headers
            # )
            print(f"{keyword} :: {page} ::: {response.status_code}")
            if response.status_code == 200:
                retry = 0
                html = response.text
                file_path = os.path.join(db.PL_pagesave_path, f"{hash_key}.html.gz")
                with gzip.open(file_path, "wt", encoding="utf-8") as f:
                    f.write(html)

            if response.status_code == 403:
                print(f"{keyword} :: 403 received. Refreshing DataDome token...")
                with token_lock:
                    # Refresh only if another thread hasn't already done it
                    if cookies["datadome"] == global_token:
                        new_token = dt.get_new_token_from_browser()
                        if new_token:
                            global_token = new_token
                    cookies["datadome"] = global_token
                retry += 1
                continue
            elif response.status_code in (500, 502, 503):
                try:
                    response = requests.get(
                        'https://www.constructionweekonline.com/',
                        params=params, cookies=cookies, headers=headers, timeout=(20, 90)
                    )

                except requests.exceptions.RequestException as e:
                    print(f"{keyword} :: Direct request failed: {e}")
                    update_status(keyword, record_id,"pending")
                    update_progress()
                    return
                if "403 Forbidden" in response.text:
                    update_status(keyword, record_id, "keyword_not_found_forbidden")
                    break
                time.sleep(2)
                retry += 1
                continue
            if response.status_code == 404:
                print(f"{keyword} :: No more pages")
                break
        # else:
        #     url = f"https://www.constructionweekonline.com/page/{page}"
        #     params = {
        #         "s": keyword,
        #         "cat_name": ""
        #     }
        #     file_path = os.path.join(db.PL_pagesave_path, f"{hash_key}_{page}.html")
        #     if os.path.exists(file_path):
        #         with open(file_path, "r", encoding="utf-8") as f:
        #             html = f.read()
        #     else:
        #         # # Build the final URL with query parameters
        #         final_url = f"{url}?{urlencode(params)}"
        #         headers['referer']=final_url
        #         response = requests.get(
        #             'https://www.constructionweekonline.com/', params=params,
        #             cookies=cookies,
        #             headers=headers,
        #         )
        #
        #         print(f"{keyword} :: {page} ::: {response.status_code}")
        #         if response.status_code == 200:
        #             html = response.text
        #             file_path = os.path.join(db.PL_pagesave_path, f"{hash_key}_{page}.html")
        #             with open(file_path, "w", encoding='utf-8') as f:
        #                 f.write(response.text)
        #         if response.status_code == 404:
        #             print(f"{keyword} :: No more pages")
        #             break

        selector = Selector(html)
        # No result page
        page_title = selector.xpath('//main[contains(@id, "main")]//h1[contains(@class, "page-title")]/text()').get()
        if page_title == "Nothing Found":
            if page == 1:
                update_status(keyword, record_id, "keyword_not_found")
                update_progress()
            return
        # Extract articles
        articles = selector.xpath('//main[contains(@id, "main")]//article')
        stop_pagination = False
        for article in articles:
            date_str = article.xpath('.//time[contains(@class,"published")]/@datetime').get()
            if not date_str:
                continue
            try:
                published_date = datetime.fromisoformat(
                    date_str.replace("Z", "+00:00")
                ).date()
            except Exception:
                continue

            # Older than D-2 -> stop pagination
            if published_date < START_DATE:
                stop_pagination = True
                break
            # Ignore today's articles
            if published_date > END_DATE:
                continue
            article_id = article.xpath('substring-after(@id, "post-")').get()
            title = article.xpath('.//h2[@class="entry-title"]/a/text()').get()
            link = article.xpath('.//h2[@class="entry-title"]/a/@href').get()
            image = article.xpath('.//figure//img/@src').get()
            category = article.xpath('.//span[contains(@class,"cat-links")]/a/text()').getall()
            category = ', '.join(category).strip() if category else None
            publisher = (
                    article.xpath('.//*[contains(@class,"author-link")]//text()').getall()
                    or article.xpath('.//*[contains(@class,"author")]//a/text()').getall()
            )
            publisher = ''.join(publisher).replace("by", "").strip() if publisher else None
            data = {
                "keyword_id": record_id,
                "keyword": keyword,
                "article_id": article_id,
                "title": title,
                "article_url": link,
                "image_url": image,
                "category": category,
                "publisher": publisher,
                "published_date": date_str,
                "hash_key": hash_key,
                "file_name": file_path,
                "status":"pending"
            }
            all_articles.append(data)
        # No need to crawl more pages
        if stop_pagination:
            print(f"{keyword} :: Reached articles older than {START_DATE}. Stopping pagination.")
            break
        page += 1

    if all_articles:
        insert_articles(all_articles)
        update_status(keyword, record_id, "completed")
        update_progress()
    else:
        update_status(keyword, record_id, "no_recent_articles")
        update_progress()

def watchdog(timeout=120):
    while True:
        idle = time.time() - LAST_PROGRESS
        if idle > timeout:
            print(f"WATCHDOG: No progress for {int(idle)} seconds. Restarting search_article_3.py...\n")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        time.sleep(10)


MAX_THREADS = random.randint(10, 15)

def main(rows):
    futures = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for r in rows:
            future = executor.submit(fetch_search_data,r["keyword"], r["id"])
            futures.append(future)
        try:
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Thread error: {e}")
        except TimeoutError:
            print("\nWATCHDOG: Some threads did not finish within 180 seconds.")
            print("Restarting search_article_3.py...\n")
            os.execv(sys.executable, [sys.executable] + sys.argv)


if __name__ == "__main__":
    threading.Thread(target=watchdog,daemon=True).start()
    while True:
        conn = db.get_db_connection(db.db_name)
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(f""" SELECT * FROM {db.input_table} WHERE status = 'pending' ORDER BY id ASC""")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if not rows:
            print("No pending records found. All records processed.")
            break
            # sys.exit(0)
        print(f"Processing {len(rows)} pending records...")
        main(rows)
        print("Retrying for remaining pending records...\n")



    # conn = db.get_db_connection(db.db_name)
    # cur = conn.cursor(pymysql.cursors.DictCursor)
    # cur.execute(f""" SELECT * FROM {db.input_table} WHERE status = 'pending' ORDER BY ID ASC""")
    # # cur.execute(f""" SELECT * FROM {db.input_table} WHERE status = 'no_recent_articles' ORDER BY ID ASC""")
    # rows = cur.fetchall()
    # print(len(rows))
    # main(rows)
    # cur.close()
    # conn.close()
    # % PYTHON % D:\Julee\CODE\ConstructionWeekOnline\CODE\search_article_3.py
    # if errorlevel 1 goto:error