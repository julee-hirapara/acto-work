# -------------------  pdp_data_3.py ---------------------------------


# import json
# import time
# import os
# from curl_cffi import requests
# from parsel import Selector
# import db_config_1 as db
# import html
# import tls_client
#
# API_URL = "https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Product-updateSubscription"
#
# # ✅ Update status
# def update_status(link_id):
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor()
#     cursor.execute(f"UPDATE {db.link_table} SET status = 'redirect' WHERE id = %s", (link_id,))
#     conn.commit()
#     conn.close()
#
# # ✅ Process single product
# def process_product(link_id, url, headers, hash_key):
#     print(f"\nProcessing: {url}")
#     # session = requests.Session()
#     # res = req.get(url, headers=headers, cookies=cookies, impersonate="chrome110", allow_redirects=True)
#     # res = requests.get(url, headers=headers, proxies=proxy, allow_redirects=True,verify=False, timeout=60)
#     res = requests.get(
#         "https://api.scrape.do/",
#         params={
#             "token": db.proxy_token,
#             "url": url,
#         },
#         timeout=30,
#         allow_redirects=False,
#     )
#     # print("-" * 100)
#     # print("Status:", res.status_code)
#     # print("Final URL:", res.url)
#     # print("Headers:", res.headers)
#     # print("-" * 100)
#     pdp_file_path = os.path.join(db.PDP_PAGESAVE, f"{hash_key}.html")
#     if res.status_code != 200:
#         print("❌ Failed main page:", res.status_code)
#         return
#     # Save PDP page
#     with open(pdp_file_path, "w", encoding='utf-8') as f:
#         f.write(res.text)
#     sel = Selector(text=res.text)
#
#     # 1️⃣ Try JSON-LD first
#     variants_data = []
#     scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
#     for script in scripts:
#         try:
#             data = json.loads(script)
#             if data.get('@type') == 'Product':
#                 offers = data['offers']['offers']
#                 for offer in offers:
#                     variants_data.append({
#                         "pid": offer['sku'],
#                         "referer": offer['url']
#                     })
#                 break
#         except:
#             continue
#
#     # 2️⃣ Fallback to pr-pdp-components
#     if not variants_data:
#         print("⚠️ No JSON-LD offers → using fallback")
#         raw = sel.xpath('//div[@class="pr-pdp-components"]/@data-pr-pdp-components').get()
#         if raw:
#             decoded = html.unescape(raw)
#             data = json.loads(decoded)
#             referer = data['product']['url']
#             for v in data['product']['variants']:
#                 variants_data.append({
#                     "pid": v['page_id_variant'],
#                     "referer": referer
#                 })
#
#     if not variants_data:
#         print("❌ No variants found at all")
#         return
#
#     # 3️⃣ Process each variant
#     for item in variants_data:
#         pid = item['pid']
#         print(f"→ Variant PID: {pid}")
#         payload = {
#             "pid": pid,
#             "options": [],
#             "isAutoShipSelected": "false",
#             "shipment": "DTC"
#         }
#         api_res = requests.post(
#             "https://api.scrape.do/",
#             params={
#                 "token": db.proxy_token,
#                 "url": API_URL,
#             },
#             headers=headers,
#             data=payload,
#             timeout=30,
#         )
#         # print("-" * 100)
#         # print(api_res.status_code)
#         # print("api_res.headers", api_res.headers)
#         # print("-" * 100)
#         # Save API response
#         variation_folder = os.path.join(db.PDP_PAGESAVE, "variation_pagesave")
#         os.makedirs(variation_folder, exist_ok=True)
#         data_file_path = os.path.join(variation_folder, f"{pid}.json")
#         if api_res.status_code == 200:
#             try:
#                 with open(data_file_path, "w", encoding='utf-8') as f:
#                     json.dump(api_res.json(), f, ensure_ascii=False, indent=4)
#                 print("Status:", api_res.status_code)
#             except Exception as e:
#                 print("JSON save error:", e)
#         elif api_res.status_code == 403:
#             print("⚠️ Blocked (403) → retry later")
#             return
#
#         time.sleep(0.5)
#
#     # ✅ Mark as done
#     update_status(link_id)
#     print("✅ Completed:", url)
#
# # from concurrent.futures import ThreadPoolExecutor, as_completed
# #
# # MAX_WORKERS = 5  # 🔥 adjust (6–10 best)
# #
# # def main():
# #     headers = {
# #         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
# #         'accept-language': 'en-US,en;q=0.9',
# #         'cache-control': 'max-age=0',
# #         'priority': 'u=0, i',
# #         'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
# #         'sec-ch-ua-mobile': '?0',
# #         'sec-ch-ua-platform': '"Windows"',
# #         'sec-fetch-dest': 'document',
# #         'sec-fetch-mode': 'navigate',
# #         'sec-fetch-site': 'same-origin',
# #         'sec-fetch-user': '?1',
# #         'upgrade-insecure-requests': '1',
# #         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
# #     }
# #
# #     conn = db.get_db_connection(db.db_name)
# #     cursor = conn.cursor()
# #     cursor.execute(f"SELECT id, url, hash_key FROM {db.link_table} WHERE status = 'pending'")
# #     links = cursor.fetchall()
# #     conn.close()
# #
# #     print(f"Total links: {len(links)}")
# #
# #     # 🔥 MULTITHREAD ONLY HERE
# #     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
# #         futures = []
# #
# #         for i, row in enumerate(links, 1):
# #             link_id = row['id']
# #             url = row['url']
# #             hash_key = row['hash_key']
# #
# #             futures.append(
# #                 executor.submit(process_product, link_id, url, headers.copy(), hash_key)
# #             )
# #
# #         # optional: track progress
# #         for i, future in enumerate(as_completed(futures), 1):
# #             try:
# #                 future.result()
# #                 print(f"✅ Completed {i}/{len(futures)}")
# #             except Exception as e:
# #                 print("❌ Thread error:", e)
#
# # ✅ Main runner
# def main():
#     headers =  {
#         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#         'accept-language': 'en-US,en;q=0.9',
#         'cache-control': 'max-age=0',
#         'priority': 'u=0, i',
#         'referer': 'https://www.petsupermarket.com/dog/supplies/toys/balls-fetch-toys/dippin%E2%80%99-dots-flying-disc-and-tennis-ball-outdoor-play-dog-toy-set/PSI10527.html',
#         'sec-ch-ua': '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'document',
#         'sec-fetch-mode': 'navigate',
#         'sec-fetch-site': 'same-origin',
#         'upgrade-insecure-requests': '1',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36',
#     }
#
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor()
#     cursor.execute(f"SELECT id, url, hash_key FROM {db.link_table} "
#                    f"WHERE status = 'pending' ORDER BY id ASC limit 10")
#     links = cursor.fetchall()
#     conn.close()
#     print(f"Total links: {len(links)}")
#     for i, row in enumerate(links, 1):
#         link_id = row['id']
#         url = row['url']
#         hash_key = row['hash_key']
#         try:
#             print(f"\n===== {i}/{len(links)} =====")
#             process_product(link_id, url, headers, hash_key)
#         except Exception as e:
#             print("❌ Error:", e)
#             continue
#
#
# if __name__ == "__main__":
#     main()

# -------------------  pdp_data_3.py ---------------------------------