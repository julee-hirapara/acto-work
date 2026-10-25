import gzip
import json
import os
import time
import random

from httplib2.auth import auth_param_name
from parsel import Selector
from glom import glom
import pymysql
from curl_cffi import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.stdout.reconfigure(encoding='utf-8')
import header_token as ht
import db_config_1 as db
import re

MAX_THREADS = 1

# AUTH TOKEN
# =========================
def get_auth_token():
    with open("token_data.json", "r", encoding='utf-8') as f:
        token_data = json.load(f)
    # ✅ Extract tokens
    auth_token = token_data.get("authToken")
    reauth_token = token_data.get("reauthToken")

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Origin': 'https://www.urbanoutfitters.com',
        # 'Referer': 'https://www.urbanoutfitters.com/shop/out-from-under-bec-low-rise-mini-skort',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'authorization': 'Bearer ***HIDDEN***',
        'baggage': 'sentry-environment=production,sentry-release=slipstream%404.39.1,sentry-public_key=***HIDDEN***,sentry-trace_id=30bde788ce73480290bfb69e9daa8c93,sentry-org_id=39832,sentry-transaction=%2Fshop%2F%3Aslug(%5Ba-zA-Z0-9_-%5D%2B),sentry-sampled=false,sentry-sample_rand=0.7775300365610607,sentry-sample_rate=0.01',
        'content-type': 'application/json',
        'sec-ch-device-memory': '8',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Chromium";v="146.0.7680.165", "Not-A.Brand";v="24.0.0.0", "Google Chrome";v="146.0.7680.165"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sentry-trace': '***HIDDEN***',
        'x-urbn-channel': 'web',
        'x-urbn-country': 'IN',
        'x-urbn-currency': 'USD',
        'x-urbn-experience': 'ss',
        'x-urbn-geo-region': 'AS-SG',
        'x-urbn-language': 'en-US',
        'x-urbn-primary-data-center-id': 'US-NV',
        'x-urbn-site-id': 'uo-us',
    }

    json_data = {
        'reauthToken': reauth_token,
    }

    response = requests.put(
        'https://www.urbanoutfitters.com/slipstream/api/token/v0/uo-us/auth',
        headers=headers,
        json=json_data,
    )
    # print(response)
    data = response.json()
    with open("token_data.json", "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    # print(data)
    auth_token = data.get("authToken")
    print(auth_token)
    return auth_token

def fetch_master_class_id(hash_id):
    file_name = fr"{db.DATA_PAGESAVE}\{hash_id}.html.gz"
    if not os.path.exists(file_name):
        return None
    with gzip.open(file_name, 'rb') as f:
        tx = f.read().decode('utf-8')

    sel = Selector(tx)

    blocks_2 = sel.xpath('//script[@id="urbnInitialPiniaState"]//text()').get()
    if not blocks_2:
        raise ValueError("No URBN state block found")
    try:
        temp = json.loads(blocks_2)
        data_2 = json.loads(temp) if isinstance(temp, str) else temp
        slug = list(data_2['catalog']['products'].keys())[0]
        return glom(data_2, f"catalog.products.{slug}.product.merchandiseClass", default=None)
    except Exception as e:
        print(e)
        return None

def load_proxies(file_path):
    proxy_list = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) != 4:
                print(f"Invalid proxy format: {line}")
                continue
            ip, port, user, pwd = parts
            proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
            proxy_list.append(proxy_url)
    return proxy_list

def get_random_proxy():
    if not PROXIES:
        return None
    proxy = random.choice(PROXIES)
    return {
        "http": proxy,
        "https": proxy
    }


def fetch_reviews_data(headers, product_id, hash_id):
    master_class = fetch_master_class_id(hash_id)
    if not master_class:
        return None
    print("fetching:", product_id)
    file_path = os.path.join(db.REVIEW_PAGESAVE, f"{hash_id}_review.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # url = f"http://api.scrape.do/?token={token}&url=https://api.urbanoutfitters.com/api/review/v0/uo-us/products/{product_id}/reviews?merchandise-class=0216%26offset=0%26limit=5%26filter=%26sort=submissionTime%3Adesc&super=true"
        # url = f"http://api.scrape.do/?token={token}&url=https://api.urbanoutfitters.com/api/review/v0/uo-us/products/{product_id}/reviews?merchandise-class=0216%26offset=0%26limit=5%26filter=%26sort=submissionTime%3Adesc&super=true"
        url = f"https://api.urbanoutfitters.com/api/review/v0/uo-us/products/{product_id}/reviews"
        params = {
            "merchandise-class": master_class,
            "offset": 0,
            "limit": 50,
            "filter": "",
            "sort": "submissionTime:desc"
        }
        proxy = get_random_proxy()
        for _ in range(2):
            response = requests.get(url,
                                    headers=headers,
                                    params=params,
                                    impersonate=random.choice(['chrome124', 'chrome120', 'chrome110', 'chrome99'])
                                    # proxies=proxy,
                                    # verify=False,
                                    # timeout=600,
                                    # allow_redirects=False
                                    )
            if response.status_code == 200:
                data = response.json()
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            else:
                auth_t = ht.get_urban_outfitters_token()
                headers = auth_t["headers"]
                datadome_id = headers.get("x-datadome-clientid")
                data_center_id = headers.get("x-urbn-primary-data-center-id")
                auth_token = data["token"]
                # auth_token = "***HIDDEN***"
                headers = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'en-US,en;q=0.9',
                    'authorization': auth_token,
                    # 'x-datadome-clientid': auth_data["datadome"],
                    # 'x-urbn-primary-data-center-id': auth_data["data_center"],
                    'origin': 'https://www.urbanoutfitters.com',
                    'priority': 'u=1, i',
                    # 'referer': 'https://www.urbanoutfitters.com/',
                    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
                    'x-urbn-channel': 'web',
                    'x-urbn-country': 'IN',
                    'x-urbn-currency': 'USD',
                    'x-urbn-experience': 'ss',
                    'x-urbn-geo-region': 'US-PA',
                    'x-urbn-language': 'en-US',
                    'x-datadome-clientid': datadome_id,
                    'x-urbn-primary-data-center-id': data_center_id,
                    'x-urbn-site-id': 'uo-us',
                }
                time.sleep(2)
                print(f"❌ HTTP {response.status_code}")
    if not data:
        return None
    extract_review_data(data, product_id)



def extract_review_data(data, pid):
    if not data:
        return None
    try:
        reviews = []
        for r in data.get("results", []):
            date = "N/A"
            if r.get("lastModificationTime"):
                try:
                    date = datetime.fromisoformat(
                        r["lastModificationTime"]
                    ).strftime("%Y-%m-%d")
                except:
                    pass

            reviews.append({
                "review_name": r.get("userNickname", "N/A"),
                "review_title": r.get("title", "N/A"),
                "review_content": r.get("reviewText", "N/A"),
                "rating": r.get("rating", "N/A"),
                "review_date": date,
                "verified": r.get("verified", False)
            })
        if reviews:
            with db.get_db_connection(db.db_name) as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cur:
                    cur.execute(f"UPDATE {db.data_table} SET review_text=%s, status_review='done' WHERE pid=%s",(json.dumps(reviews),pid))
                    conn.commit()
                    print("Inserted: ", pid)
    except Exception as e:
        print("❌ Review parse error:", e)



def main(records):
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [
            executor.submit(fetch_reviews_data, headers, r['pid'], r['hash_id'])
            for r in records
        ]
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as e:
                print("❌ Thread error:", e)

if __name__ == '__main__':
    # start_index = sys.argv[1]
    # end_index = sys.argv[-1]
    PROXY_FILE = r"D:\Julee\CODE\URBAN_OUTFITTERS\iproyal-proxies.txt"
    PROXIES = load_proxies(PROXY_FILE)
    data = ht.get_urban_outfitters_token()
    headers = data["headers"]
    datadome_id = headers.get("x-datadome-clientid")
    print(datadome_id)
    data_center_id = headers.get("x-urbn-primary-data-center-id")
    auth_token = data["token"]
    # auth_token = '***HIDDEN***'
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': auth_token,
        # 'x-datadome-clientid': auth_data["datadome"],
        # 'x-urbn-primary-data-center-id': auth_data["data_center"],
        'origin': 'https://www.urbanoutfitters.com',
        'priority': 'u=1, i',
        # 'referer': 'https://www.urbanoutfitters.com/',
        'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
        'x-urbn-channel': 'web',
        'x-urbn-country': 'IN',
        'x-urbn-currency': 'USD',
        'x-urbn-experience': 'ss',
        'x-urbn-geo-region': 'US-PA',
        'x-urbn-language': 'en-US',
        'x-datadome-clientid': datadome_id,
        'x-urbn-primary-data-center-id': data_center_id,
        'x-urbn-site-id': 'uo-us',
    }
    with db.get_db_connection(db.db_name) as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # cur.execute(f"SELECT  DISTINCT pid, hash_id FROM {db.data_table} WHERE num_ratings IS NOT NULL AND status_review='pending' AND pid BETWEEN '{start_index}' and '{end_index}'")
            cur.execute(f"SELECT  DISTINCT pid, hash_id FROM {db.data_table} WHERE num_ratings IS NOT NULL AND status_review='pending'")
            # cur.execute(f"SELECT  DISTINCT pid, hash_id FROM {db.data_table} WHERE pid='UO-57537995-000'")
            records = cur.fetchall()
    main(records)
