import json
import os.path
import urllib.parse
import pymysql
import db_config_1 as db
# import requests
from curl_cffi import requests
from parsel import Selector
import time
import re
import header_token as ht
import hashlib
import gzip
import json


def url_to_id(url):
    h = hashlib.sha256(url.encode()).hexdigest()
    num = int(h, 16)
    short_id = str(num)[0:12]
    return short_id


headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': ht.get_urban_outfitters_token()['token'],
    'content-type': 'application/json',
    'origin': 'https://www.urbanoutfitters.com',
    'priority': 'u=1, i',
    'referer': 'https://www.urbanoutfitters.com/',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'x-urbn-channel': 'web',
    'x-urbn-country': 'IN',
    'x-urbn-currency': 'USD',
    'x-urbn-experience': 'ss',
    'x-urbn-geo-region': 'AS-SG',
    'x-urbn-language': 'en-US',
    'x-urbn-pool': 'INTL_DIRECT',
    'x-urbn-primary-data-center-id': 'US-NV',
    'x-urbn-site-id': 'uo-us',
}


def fetch_pl_links_with_total(rows):
    for row in rows:
        cat_url = row["url"]
        cat_name = row["displayname"]
        slug = row["slug"]
        cat_id = row["id"]

        print(f"\n📌 Fetching category: {cat_name} ({cat_url})")

        # ------------------------------
        # STEP 1 — GET CATEGORY PAGE HTML
        # ------------------------------
        try:
            # FILE_PATH = f"{db.LINK_PAGESAVE}\\{slug}.html"
            # if os.path.exists(FILE_PATH):
            #     with open(FILE_PATH, "r", encoding='UTF-8') as f:
            #         html_content = f.read()
            FILE_PATH = f"{db.LINK_PAGESAVE}\\{slug}.html.gz"
            if os.path.exists(FILE_PATH):
                with gzip.open(FILE_PATH, "rt", encoding="utf-8") as f:
                    html_content = f.read()
            else:
                response = requests.get(cat_url, headers=headers, timeout=20)
                print(response.status_code)
                if response.status_code == 200:
                    html_content = response.text
                    # with open(FILE_PATH, "w", encoding='UTF-8') as f:
                    #     f.write(html_content)
                    with gzip.open(FILE_PATH, "wt", encoding="utf-8") as f:
                        f.write(html_content)

            sel = Selector(html_content)
            count_text = sel.xpath("//p[contains(@class, 'c-pwa-tile-result-count')]//text()").get()
            if not count_text:
                print(f"❌ Count not found for {cat_name}")
                continue
            match = re.search(r"(\d+)", count_text)
            if not match:
                print(f"❌ Could not parse count for {cat_name}")
                continue

            total_count = int(match.group(1))
            print(f"🔢 Total products: {total_count}")

        except Exception as e:
            print(f"❌ Error fetching HTML for {cat_name}: {e}")
            continue

        # -------------------------
        # STEP 2 — BUILD API URL
        # -------------------------
        slug = cat_url.rstrip("/").split("/")[-1]
        api_url = (
            f"https://api.urbanoutfitters.com/api/catalog-search-service/v0/uo-us/tiles/{slug}"
        )
        json_data = {
            'pageSize': total_count,  # in this pagesize limit is 10000 if any category's totalcount is more than 10000 then need to implement pagination.
            'skip': 0,
            'projectionSlug': 'categorytiles',
            'personalization': '0',
            'customerConsent': 'true',
            'featureProductIds': [],
        }
        # -------------------------
        # STEP 3 — API REQUEST
        # -------------------------
        try:
            # file_path = f"{db.LINK_PAGESAVE}\\{slug}.json"
            # if os.path.exists(file_path):
            #     with open(file_path, "r", encoding="utf-8") as f:
            #         data = json.load(f)
            file_path = f"{db.LINK_PAGESAVE}\\{slug}.json.gz"

            if os.path.exists(file_path):
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                cookies = {
                    'SSLB': '1',
                    'urbn_geo_region': 'AS-SG',
                    'urbn_data_center_id': 'US-NV',
                    'urbn_tracer': 'VDWGNAAA7P',
                    'utag_main_v_id': '***HIDDEN***',
                    '_fbp': 'fb.1.1781606125671.828508829702287667.Bg',
                    '_scid': '8frCjSq8zQC7vrRDgbShsemPjgO4npijTKy-Tg',
                    'BVBRANDID': '1bb6d5d5-23c2-422b-bda8-9e2146523a73',
                    '_tt_enable_cookie': '1',
                    '_ttp': '01KV8004XB5PHEB222WP5N2FJ6_.tt.1',
                    '_lc2_fpi': '18c6eee2a756--01kv8004yaj6z6hen9ztvk5m5n',
                    '__attentive_id': '***HIDDEN***',
                    '_attn_': '***HIDDEN***',
                    '__attentive_cco': '1781606126832',
                    '_svsid': '***HIDDEN***',
                    '__adroll_fpc': '***HIDDEN***',
                    '_pin_unauth': 'dWlkPVpXWmlZVFl6T1RBdFlUZzJOQzAwWmpNMkxUbGhNalF0WWpJeFlqZzVNR1ExWVdVMA',
                    '_ga': 'GA1.1.695608221.1781606128',
                    'OptanonAlertBoxClosed': '2026-06-16T10:35:28.347Z',
                    '__obref': '2a0b9efd-6b58-439d-ba69-9e494726ca83',
                    'mt.v': '2.2053451854.1785917026737',
                    'styliticsWidgetSession': '4a9a333f-d690-4d17-a994-4241390b1a4e',
                    '_ce.s': '***HIDDEN***',
                    '_dyid_server': '6480680127563940034',
                    '_dyid': '6480680127563940034',
                    'rbuid': 'rbos-497f8f09-964c-4025-a9f8-54d3e376dadd',
                    'smartDash': 'bab10c25-d949-4b6f-9b7b-47677f3a295f',
                    '_li_dcdm_c': '.urbanoutfitters.com',
                    '_lc2_fpi_js': '18c6eee2a756--01kv8004yaj6z6hen9ztvk5m5n',
                    '_sctr': '1%7C1791484200000',
                    '_clck': '1cbbq6o%5E2%5Ega8%5E1%5E2353',
                    'monetate_social_proof': '',
                    'ss-enable-401-reauth-modal': '1',
                    'ss-enable-multi-label-returns': 'true',
                    'SSID': '***HIDDEN***',
                    'SSSC': '***HIDDEN***',
                    'urbn_is_active_dy_session': 'true',
                    '_dyjsession': 'y7fiw36dn1ql5krq7p7oaafwyt4bmaro',
                    'OptanonConsent': 'isGpcEnabled=0&datestamp=Mon+Oct+12+2026+10%3A13%3A45+GMT%2B0530+(India+Standard+Time)&version=202606.1.0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&consentId=2b255836-e584-40b8-8fb9-75692ba80197&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0002%3A1%2CC0001%3A1%2CC0003%3A1%2CC0004%3A1&iType=1&geolocation=GB%3BENG&AwaitingReconsent=false&isDntEnabled=0&prevHadToken=0',
                    'utag_main__sn': '44',
                    'utag_main_ses_id': '1791780227947%3Bexp-session',
                    'utag_main__pn': '1%3Bexp-session',
                    '_dy_soct': '1791780228!!',
                    'utag_main_isLoggedIn': 'false%3Bexp-session',
                    'utag_main_tag_session_256': '1%3Bexp-session',
                    'utag_main_dc_visit': '44',
                    'utag_main__ss': '0%3Bexp-session',
                    'utag_main_dc_region': 'us-east-1%3Bexp-session',
                    'mp_urbn_urbanoutfitters_na_mixpanel': '%7B%22distinct_id%22%3A%20%2219ed000128082e-0c6414a4bff057-26061151-e1000-19ed0001281133d%22%2C%22bc_persist_updated%22%3A%201781606126210%7D',
                    '__attentive_session_id': '***HIDDEN***',
                    '_rdt_uuid': '1781606126415.a814df14-d6ac-4e1e-9ed6-83344dc1159c',
                    '__attentive_pv': '1',
                    '__attentive_ss_referrer': 'ORGANIC',
                    '_scid_r': 'CPrCjSq8zQC7vrRDgbShsemPjgO4npijTKy-vg',
                    '__attentive_dv': '1',
                    'utag_main_ttd_uuid': '0ab22fe8-bfa7-41f7-8b97-8d607fadc075%3Bexp-session',
                    'utag_main_cms_256': '1%3Bexp-session',
                    'utag_main__se': '3%3Bexp-session',
                    'utag_main__st': '1791782036751%3Bexp-session',
                    '_uetsid': '***HIDDEN***',
                    '_uetvid': '***HIDDEN***',
                    '_gcl_au': '1.1.898374089.1791551837.163911079.1791780232.1791780237.933950495.1791780232.1791780237',
                    'utag_main_dc_event': '2%3Bexp-session',
                    'ttcsid_CC2K5NJC77U26CFATFP0': '1791780231067::gbtddezMO9Ml05Ka5f1W.44.1791780237408.1',
                    'ttcsid': '1791780217015::Ztk0U00bIRstUUr2l2gV.36.1791780237408.0::1.20060.14053::17971.1.1188.254::2077.22.0',
                    '_clsk': '7elhe%5E1791781708672%5E5%5E0%5Ee.clarity.ms%2Fcollect',
                    'SSRT': '***HIDDEN***',
                    'urbn_auth_payload': '***HIDDEN***',
                    '_ga_BBMWPLK0E5': 'GS2.1.s1791780222$o26$g1$t1791781711$j60$l0$h0',
                    'datadome': '***HIDDEN***',
                }

                headers = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'en-US,en;q=0.9',
                    'authorization': 'Bearer ***HIDDEN***',
                    'content-type': 'application/json',
                    'origin': 'https://www.urbanoutfitters.com',
                    'priority': 'u=1, i',
                    'referer': 'https://www.urbanoutfitters.com/',
                    'sec-ch-ua': '"Chromium";v="154", "Google Chrome";v="154", "Not A(Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',
                    'x-datadome-clientid': 'bHDRzWH8W9mOy~tJSHHwIn4vt2GAthZyJfZ2wDJDah7qEUrNDBwYOBVNkd04E56AlQj96z4ZLj4Ss~f9XxWdioa4xzY3BZ84OCAzSYlZ74eHaorOdyYNCBMt2O3Pbzb1',
                    'x-urbn-channel': 'web',
                    'x-urbn-country': 'US',
                    'x-urbn-currency': 'USD',
                    'x-urbn-experience': 'ss',
                    'x-urbn-geo-region': 'AS-SG',
                    'x-urbn-language': 'en-US',
                    'x-urbn-primary-data-center-id': 'US-NV',
                    'x-urbn-site-id': 'uo-us',
                    # 'cookie': '***HIDDEN***',
                }

                # proxy = {
                #     "http": f'http://{db.proxy_token}:super=false@proxy.scrape.do:8080',
                #     "https": f'http://{db.proxy_token}:super=false@proxy.scrape.do:8080',
                # }
                # response = requests.post(api_url, json=json_data, proxies=proxy, verify=False, timeout=60)
                response = requests.post(api_url, headers=headers, cookies=cookies, json=json_data, timeout=25)
                if response.status_code == 200:
                    data = response.json()
                    with gzip.open(file_path, "wt", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    # with open(file_path, "w", encoding='UTF-8') as f:
                    #     json.dump(data, f, indent=4, ensure_ascii=False)
                if response.status_code != 200:
                    print(f"❌ API failed for {cat_name}: HTTP {response.status_code}")
                    continue
            try:
                records = data.get("records", [])
                for rec in records:
                    product = rec.get("allMeta", {}).get("tile", {}).get("product", {})
                    name = product.get("displayName")
                    slug = product.get("productSlug")
                    product_id = product.get("productId")
                    brand = product.get("brand")
                    reviews = rec.get("allMeta", {}).get("tile", {}).get("reviews", {})
                    avg_rating = reviews.get("averageRating")
                    review_count = reviews.get("count")
                    if not slug:
                        continue
                    url = f"https://www.urbanoutfitters.com/shop/{slug}"
                    hash_id = url_to_id(url)
                    print(f"product_name ::: {name} --- slug :::: {slug}")
                    insert_link(url, name, cat_name, slug, product_id, brand, avg_rating, review_count, hash_id)
            except Exception as e:
                print(f"not found path ::: {e}")

        except Exception as e:
            print(f"❌ API error for {cat_name}: {e}")
            continue

        # -------------------------
        # STEP 4 — SAVE TO DATABASE
        # -------------------------
        try:
            conn = db.get_db_connection(db.db_name)
            cur = conn.cursor()

            cur.execute(f"UPDATE {db.cat_links_table} SET status = 'done' WHERE id = %s", (cat_id,))
            conn.commit()
            cur.close()
            conn.close()
            print(f"✔ Saved all products for {cat_name}")
        except Exception as e:
            print(f"❌ Database error for {cat_name}: {e}")
        time.sleep(1)


def insert_link(url, name, category, slug, product_id, brand, avg_rating, review_count, hash_id):
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()
    sql = f"""
        INSERT IGNORE INTO {db.link_table} (url, name, category, slug, product_id, brand, avg_rating, review_count, hash_id, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """     # ON DUPLICATE KEY UPDATE url = url
    values = (url, name, category, slug, product_id, brand, avg_rating, review_count, hash_id, "pending")
    cur.execute(sql, values)
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(f"SELECT * FROM {db.cat_links_table} WHERE status = 'pending'")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    fetch_pl_links_with_total(rows)

# import json
# import os.path
# import urllib.parse
# import pymysql
# import db_config_1 as db
# # import requests
# from curl_cffi import requests
# from parsel import Selector
# import time
# import re
# import header_token as ht
# import hashlib
#
#
# def url_to_id(url):
#     h = hashlib.sha256(url.encode()).hexdigest()
#     num = int(h, 16)
#     short_id = str(num)[0:16]
#     return short_id
#
# def cookies_to_dict(cookie_list):
#     return {c['name']: c['value'] for c in cookie_list}
#
#
# def fetch_pl_links_with_total(rows, cookies, headers):
#     for row in rows:
#         cat_url = row["url"]
#         cat_name = row["displayname"]
#         slug = row["slug"]
#         cat_id = row["id"]
#
#         print(f"\n📌 Fetching category: {cat_name} ({cat_url})")
#
#         # ------------------------------
#         # STEP 1 — GET CATEGORY PAGE HTML
#         # ------------------------------
#         try:
#             FILE_PATH = f"{db.LINK_PAGESAVE}\\{slug}.html"
#             if os.path.exists(FILE_PATH):
#                 with open(FILE_PATH, "r", encoding='UTF-8') as f:
#                     html_content = f.read()
#             else:
#                 response = requests.get(cat_url, headers=headers, timeout=20)
#                 print(response.status_code)
#                 if response.status_code == 200:
#                     html_content = response.text
#                     with open(FILE_PATH, "w", encoding='UTF-8') as f:
#                         f.write(html_content)
#
#             sel = Selector(html_content)
#             count_text = sel.xpath("//p[contains(@class, 'c-pwa-tile-result-count')]//text()").get()
#             if not count_text:
#                 print(f"❌ Count not found for {cat_name}")
#                 continue
#             match = re.search(r"(\d+)", count_text)
#             if not match:
#                 print(f"❌ Could not parse count for {cat_name}")
#                 continue
#
#             total_count = int(match.group(1))
#             print(f"🔢 Total products: {total_count}")
#
#         except Exception as e:
#             print(f"❌ Error fetching HTML for {cat_name}: {e}")
#             continue
#
#         # -------------------------
#         # STEP 2 — BUILD API URL
#         # -------------------------
#         slug = cat_url.rstrip("/").split("/")[-1]
#         api_url = (
#             f"https://api.urbanoutfitters.com/api/catalog-search-service/v0/uo-us/tiles/{slug}"
#         )
#         json_data = {
#             'pageSize': total_count,
#             'skip': 0,
#             'projectionSlug': 'categorytiles',
#             'personalization': '0',
#             'customerConsent': 'true',
#             'featureProductIds': [],
#         }
#         # -------------------------
#         # STEP 3 — API REQUEST
#         # -------------------------
#         try:
#             file_path = f"{db.LINK_PAGESAVE}\\{slug}.json"
#             if os.path.exists(file_path):
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     data = json.load(f)
#             else:
#                 # cookies = {
#                 #     'SSLB': '1',
#                 #     'urbn_tracer': 'ZE96T39SS2',
#                 #     'urbn_data_center_id': 'US-NV',
#                 #     'urbn_geo_region': 'AS-SG',
#                 #     'pxcts': '***HIDDEN***',
#                 #     '_pxvid': '***HIDDEN***',
#                 #     '__pxvid': '236dde89-2dcc-11f1-98ee-5a268632e391',
#                 #     'utag_main_v_id': '***HIDDEN***',
#                 #     '_fbp': 'fb.1.1775049022180.995590058561286270.Bg',
#                 #     '__attentive_id': '***HIDDEN***',
#                 #     '_attn_': '***HIDDEN***',
#                 #     '__attentive_cco': '1775049022344',
#                 #     '__attentive_dv': '1',
#                 #     'rbuid': 'rbos-a1936001-5f98-4178-ba99-7282659419a6',
#                 #     'cebs': '1',
#                 #     '_scid': 'FtK4lZfhulDOwzn4MYklGijndBrtSaVI',
#                 #     '_pin_unauth': 'dWlkPU5XSTRPREpsWW1FdFptUTBaUzAwWlRaa0xXSmhaVE10WTJaa1lqSTNaVEJqTjJReA',
#                 #     '_ga': 'GA1.1.1541687442.1775049026',
#                 #     '_ce.clock_data': '***HIDDEN***',
#                 #     'smartDash': '94734ade-4802-4431-bba9-7f50943360ce',
#                 #     '__adroll_fpc': '***HIDDEN***',
#                 #     '_li_dcdm_c': '.urbanoutfitters.com',
#                 #     '_lc2_fpi': '18c6eee2a756--01kn4jnbf0jp6b3dt6cwjh387c',
#                 #     '_lc2_fpi_js': '18c6eee2a756--01kn4jnbf0jp6b3dt6cwjh387c',
#                 #     '_tt_enable_cookie': '1',
#                 #     '_ttp': '01KN4JNGNCV9ZZAK1HXKNKAM64_.tt.1',
#                 #     '_sctr': '1%7C1774981800000',
#                 #     '_clck': '9epz7y%5E2%5Eg4u%5E1%5E2282',
#                 #     'ss-enable-401-reauth-modal': '1',
#                 #     'ss-cart-confirm-variant': '1',
#                 #     'ss-enable-multi-label-returns': 'true',
#                 #     'SSID': '***HIDDEN***',
#                 #     'SSSC': '***HIDDEN***',
#                 #     'SSRT': '***HIDDEN***',
#                 #     'urbn_auth_payload': '***HIDDEN***',
#                 #     '_pxhd': '***HIDDEN***',
#                 #     'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Apr+01+2026+19%3A22%3A46+GMT%2B0530+(India+Standard+Time)&version=202403.1.0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&consentId=3f391d38-c440-4a32-af31-cd5eb08933be&interactionCount=0&isAnonUser=1&landingPath=https%3A%2F%2Fwww.urbanoutfitters.com%2Fwomens-clothing&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1',
#                 #     'utag_main__sn': '2',
#                 #     'utag_main_ses_id': '1775051571485%3Bexp-session',
#                 #     'utag_main__pn': '1%3Bexp-session',
#                 #     'utag_main_isLoggedIn': 'false%3Bexp-session',
#                 #     'utag_main_tag_session_256': '1%3Bexp-session',
#                 #     'utag_main_dc_visit': '2',
#                 #     'utag_main_dc_event': '1%3Bexp-session',
#                 #     'mp_urbn_urbanoutfitters_na_mixpanel': '%7B%22distinct_id%22%3A%20%2219d492a9ba73ee-0078e2ece821038-26061f51-e1000-19d492a9ba8b0b%22%2C%22bc_persist_updated%22%3A%201775049022377%7D',
#                 #     '_rdt_uuid': '1775049025056.c0ee0425-c395-4680-bab6-8741f8d48fad',
#                 #     'cebsp_': '6',
#                 #     '_ce.s': '***HIDDEN***',
#                 #     'utag_main_dc_region': 'ap-east-1%3Bexp-session',
#                 #     '_uetsid': '***HIDDEN***',
#                 #     '_uetvid': '***HIDDEN***',
#                 #     '_px3': '***HIDDEN***',
#                 #     '_gcl_au': '1.1.199364533.1775049025.913670040.1775051559.1775051572',
#                 #     '_scid_r': 'ElK4lZfhulDOwzn4MYklGijndBrtSaVI_HEyXA',
#                 #     '_clsk': '1mekixc%5E1775051573081%5E3%5E0%5Ey.clarity.ms%2Fcollect',
#                 #     '__attentive_session_id': '***HIDDEN***',
#                 #     '__attentive_pv': '1',
#                 #     '__attentive_ss_referrer': 'ORGANIC',
#                 #     'datadome': '***HIDDEN***',
#                 #     'utag_main__se': '2%3Bexp-session',
#                 #     'utag_main__ss': '0%3Bexp-session',
#                 #     'utag_main__st': '1775053473154%3Bexp-session',
#                 #     '_ga_BBMWPLK0E5': 'GS2.1.s1775051559$o2$g1$t1775051673$j59$l0$h0',
#                 #     'ttcsid': '1775051572683::8D1igs3r6KXS8NtYAZLK.2.1775051673642.0::1.-13414.0::100937.1.1202.16837::99253.25.16672',
#                 #     'ttcsid_CC2K5NJC77U26CFATFP0': '1775051572682::VUZYlx0Yaq1gDh0ifILw.2.1775051673642.1',
#                 # }
#                 response = requests.post(api_url, headers=headers, cookies=cookies, json=json_data, timeout=25)
#                 if response.status_code == 200:
#                     data = response.json()
#                     with open(file_path, "w", encoding='UTF-8') as f:
#                         json.dump(data, f, indent=4, ensure_ascii=False)
#                 if response.status_code != 200:
#                     print(f"❌ API failed for {cat_name}: HTTP {response.status_code}")
#                     continue
#             try:
#                 records = data.get("records", [])
#                 for rec in records:
#                     product = rec.get("allMeta", {}).get("tile", {}).get("product", {})
#                     name = product.get("displayName")
#                     slug = product.get("productSlug")
#                     product_id = product.get("productId")
#                     brand = product.get("brand")
#                     reviews = rec.get("allMeta", {}).get("tile", {}).get("reviews", {})
#                     avg_rating = reviews.get("averageRating")
#                     review_count = reviews.get("count")
#                     if not slug:
#                         continue
#                     url = f"https://www.urbanoutfitters.com/shop/{slug}"
#                     hash_id = url_to_id(url)
#                     print(f"product_name ::: {name} --- slug :::: {slug}")
#                     insert_link(url, name, cat_name, slug, product_id, brand, avg_rating, review_count, hash_id)
#             except Exception as e:
#                 print(f"not found path ::: {e}")
#
#         except Exception as e:
#             print(f"❌ API error for {cat_name}: {e}")
#             continue
#
#         # -------------------------
#         # STEP 4 — SAVE TO DATABASE
#         # -------------------------
#         try:
#             conn = db.get_db_connection(db.db_name)
#             cur = conn.cursor()
#
#             cur.execute(f"UPDATE {db.cat_links_table} SET status = 'done' WHERE id = %s", (cat_id,))
#             conn.commit()
#             cur.close()
#             conn.close()
#             print(f"✔ Saved all products for {cat_name}")
#         except Exception as e:
#             print(f"❌ Database error for {cat_name}: {e}")
#         time.sleep(1)
#
#
# def insert_link(url, name, category, slug, product_id, brand, avg_rating, review_count, hash_id):
#     conn = db.get_db_connection(db.db_name)
#     cur = conn.cursor()
#     sql = f"""
#         INSERT IGNORE INTO {db.link_table} (url, name, category, slug, product_id, brand, avg_rating, review_count, hash_id, status)
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#     """     # ON DUPLICATE KEY UPDATE url = url
#     values = (url, name, category, slug, product_id, brand, avg_rating, review_count, hash_id, "pending")
#     cur.execute(sql, values)
#     conn.commit()
#     cur.close()
#     conn.close()
#
#
# if __name__ == "__main__":
#     conn = db.get_db_connection(db.db_name)
#     cur = conn.cursor(pymysql.cursors.DictCursor)
#     cur.execute(f"SELECT * FROM {db.cat_links_table} WHERE status = 'pending'")
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#     token, cookies = ht.get_urban_outfitters_token()
#     cookie_dict = cookies_to_dict(cookies)
#     print(cookie_dict)
#     headers = {
#         'accept': 'application/json, text/plain, */*',
#         'accept-language': 'en-US,en;q=0.9',
#         'authorization': 'Bearer ***HIDDEN***',
#         'content-type': 'application/json',
#         'origin': 'https://www.urbanoutfitters.com',
#         'priority': 'u=1, i',
#         'referer': 'https://www.urbanoutfitters.com/',
#         'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'empty',
#         'sec-fetch-mode': 'cors',
#         'sec-fetch-site': 'same-site',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
#         'x-urbn-channel': 'web',
#         'x-urbn-country': 'IN',
#         'x-urbn-currency': 'USD',
#         'x-urbn-experience': 'ss',
#         'x-urbn-geo-region': 'AS-SG',
#         'x-urbn-language': 'en-US',
#         'x-urbn-primary-data-center-id': 'US-NV',
#         'x-urbn-site-id': 'uo-us',
#         # 'accept': 'application/json, text/plain, */*',
#         # 'accept-language': 'en-US,en;q=0.9',
#         # 'authorization': token,
#         # 'content-type': 'application/json',
#         # 'origin': 'https://www.urbanoutfitters.com',
#         # 'priority': 'u=1, i',
#         # 'referer': 'https://www.urbanoutfitters.com/',
#         # 'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#         # 'sec-ch-ua-mobile': '?0',
#         # 'sec-ch-ua-platform': '"Windows"',
#         # 'sec-fetch-dest': 'empty',
#         # 'sec-fetch-mode': 'cors',
#         # 'sec-fetch-site': 'same-site',
#         # 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
#         # 'x-urbn-channel': 'web',
#         # 'x-urbn-country': 'IN',
#         # 'x-urbn-currency': 'USD',
#         # 'x-urbn-experience': 'ss',
#         # 'x-urbn-geo-region': 'AS-SG',
#         # 'x-urbn-language': 'en-US',
#         # 'x-urbn-primary-data-center-id': 'US-NV',
#         # 'x-urbn-site-id': 'uo-us',
#     }
#     fetch_pl_links_with_total(rows, cookie_dict, headers)