# # import random
# # import time
# # import os
# # from curl_cffi import requests
# # from torch.distributed.elastic.multiprocessing.redirects import redirect
# #
# # import db_config as db
# # from parsel import Selector
# # import json
# # import html
# #
# #
# # API_URL = "https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Product-updateSubscription"
# #
# # # ✅ Update status
# # def update_status(link_id):
# #     conn = db.get_db_connection(db.db_name)
# #     cursor = conn.cursor()
# #
# #     cursor.execute(f"UPDATE {db.link_table} SET status = 'done' WHERE id = %s", (link_id,))
# #     conn.commit()
# #     conn.close()
# #
# # import re
# #
# # def normalize_size(name):
# #     match = re.search(r'[\d.]+\s?-?\s?oz', name.lower())
# #     if match:
# #         return match.group(0).replace(" ", "").replace("-", "")
# #     return None
# #
# # # ✅ Process single product
# # def process_product(link_id, url, headers, hash_key):
# #     MAX_RETRIES = 3
# #     print(f"\nProcessing: {url}")
# #     session = requests.Session()
# #     attempt = 0
# #     while attempt < MAX_RETRIES:
# #         try:
# #             res = session.get(url, headers=headers, impersonate="chrome110", allow_redirects=False)
# #             if res.status_code == 200:
# #                 pdp_file_path = os.path.join(db.PDP_PAGESAVE, f"{hash_key}.html")
# #                 with open(pdp_file_path, "w", encoding="utf-8") as f:
# #                     f.write(res.text)
# #                 print("✅ Main page success:", res.status_code)
# #                 break
# #             elif res.status_code == 403:
# #                 attempt += 1
# #                 wait_time = 2 ** attempt + random.uniform(0.5, 1.5)
# #                 print(f"⚠️ 403 Blocked → Retry {attempt}/{MAX_RETRIES} after {wait_time:.2f}s")
# #                 time.sleep(wait_time)
# #             else:
# #                 print("❌ Failed main page:", res.status_code)
# #                 break
# #         except Exception as e:
# #             attempt += 1
# #             print("❌ Request error:", e)
# #             time.sleep(2)
# #     else:
# #         print(f"🚫 Failed to fetch main page after {MAX_RETRIES} retries")
# #         return
# #     offers = []
# #     if res.status_code ==200:
# #         with open(pdp_file_path, "w", encoding='utf-8') as f:
# #             f.write(res.text)
# #         sel = Selector(text=res.text)
# #         available_sizes = sel.xpath(
# #             '//button[contains(@class,"size-attribute") and contains(@class,"selectable")]/@data-attr-value').getall()
# #         available_sizes = [s.lower().replace(" ", "") for s in available_sizes]
# #         print("Available sizes from UI:", available_sizes)
# #         offers = []
# #         # ✅ Try JSON-LD first
# #         scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
# #         for script in scripts:
# #             try:
# #                 data = json.loads(script)
# #                 if data.get('@type') == 'Product':
# #                     offers = data['offers']['offers']
# #                     break
# #             except:
# #                 continue
# #         variants_data = []
# #         # ✅ Case 1: JSON-LD found
# #         if offers:
# #             for offer in offers:
# #                 variants_data.append({
# #                     "pid": offer['sku'],
# #                     "referer": offer['url']
# #                 })
# #         # ✅ Case 2: Fallback to pr-pdp-components
# #         else:
# #             print("⚠️ No JSON-LD offers → using fallback")
# #             raw = sel.xpath('//div[@class="pr-pdp-components"]/@data-pr-pdp-components').get()
# #             if raw:
# #                 decoded = html.unescape(raw)
# #                 data = json.loads(decoded)
# #                 referer = data['product']['url']
# #                 variants = data['product']['variants']
# #                 # for v in variants:
# #                 #     size = normalize_size(v['name'])
# #                 #     if size and size in available_sizes:
# #                 #         variants_data.append({
# #                 #             "pid": v['page_id_variant'],
# #                 #             "referer": referer
# #                 #         })
# #                 #     else:
# #                 #         print(f"❌ Skipping variant: {v['name']} (size: {size})")
# #                 #     if not available_sizes:
# #                 #         print("⚠️ No size filter found → taking all variants")
# #                 #         for v in variants:
# #                 #             variants_data.append({
# #                 #                 "pid": v['page_id_variant'],
# #                 #                 "referer": referer
# #                 #             })
# #                 for v in variants:
# #                     variants_data.append({
# #                         "pid": v['page_id_variant'],
# #                         "referer": referer
# #                     })
# #         # ❌ If still empty
# #         if not variants_data:
# #             print("❌ No variants found at all")
# #             return
# #         MAX_RETRIES = 3
# #
# #         for item in variants_data:
# #             pid = item['pid']
# #             referer = item['referer']
# #             print(f"→ Variant PID: {pid}")
# #             session.get(referer, headers=headers, impersonate="chrome110", allow_redirects=False)
# #             headers['referer'] = url
# #             data = {'pid': pid}
# #             attempt = 0
# #             while attempt < MAX_RETRIES:
# #                 try:
# #                     api_res = session.post(
# #                         API_URL,
# #                         headers=headers,
# #                         data=data,
# #                         impersonate="chrome110",
# #                         allow_redirects=False
# #                     )
# #                     if api_res.status_code == 200:
# #                         variation_folder = "variation_pagesave"
# #                         variation_file_path = os.path.join(db.PDP_PAGESAVE, variation_folder)
# #                         os.makedirs(variation_file_path, exist_ok=True)
# #                         data_file_path = os.path.join(variation_file_path, f"{pid}.json")
# #                         with open(data_file_path, "w", encoding='utf-8') as f:
# #                             json.dump(api_res.json(), f, ensure_ascii=False, indent=4)
# #                         print("✅ Status:", api_res.status_code)
# #                         break  # success → exit retry loop
# #                     elif api_res.status_code == 403:
# #                         attempt += 1
# #                         wait_time = 2 ** attempt  # exponential backoff
# #                         print(f"⚠️ 403 Blocked → Retry {attempt}/{MAX_RETRIES} after {wait_time}s")
# #                         time.sleep(wait_time)
# #                     else:
# #                         print("❌ Failed with status:", api_res.status_code)
# #                         break
# #                 except Exception as e:
# #                     print("❌ Request error:", e)
# #                     attempt += 1
# #                     time.sleep(2)
# #             else:
# #                 print(f"🚫 Skipped PID {pid} after {MAX_RETRIES} retries")
# #             time.sleep(1.5)
# #         # for item in variants_data:
# #         #     pid = item['pid']
# #         #     referer = item['referer']
# #         #     print(f"→ Variant PID: {pid}")
# #         #     session.get(referer, headers=headers, impersonate="chrome110")
# #         #     headers['referer'] = url
# #         #     data = {
# #         #         'pid': pid,
# #         #     }
# #         #     api_res = session.post(
# #         #         API_URL,
# #         #         headers=headers,
# #         #         data=data,
# #         #         impersonate="chrome110"
# #         #     )
# #         #     variation_folder = "variation_pagesave"
# #         #     variation_file_path = os.path.join(db.PDP_PAGESAVE, variation_folder)
# #         #     os.makedirs(variation_file_path, exist_ok=True)
# #         #     data_file_path = os.path.join(variation_file_path, f"{pid}.json")
# #         #     if api_res.status_code == 200:
# #         #         try:
# #         #             with open(data_file_path, "w", encoding='utf-8') as f:
# #         #                 json.dump(api_res.json(), f, ensure_ascii=False, indent=4)
# #         #             print("Status:", api_res.status_code)
# #         #         except Exception as e:
# #         #             print("JSON save error:", e)
# #         #     elif api_res.status_code == 403:
# #         #         print("⚠️ Blocked (403) → retry later")
# #         #         return
# #         #     time.sleep(1.5)
# #         # ✅ Mark as done
# #         update_status(link_id)
# #         print("✅ Completed:", url)
# #
# #
# # # ✅ Main runner
# # def main():
# #     # headers = {
# #     #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
# #     #     'accept-language': 'en-US,en;q=0.9',
# #     #     'cache-control': 'max-age=0',
# #     #     'priority': 'u=0, i',
# #     #     'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
# #     #     'sec-ch-ua-mobile': '?0',
# #     #     'sec-ch-ua-platform': '"Windows"',
# #     #     'sec-fetch-dest': 'document',
# #     #     'sec-fetch-mode': 'navigate',
# #     #     'sec-fetch-site': 'same-origin',
# #     #     'sec-fetch-user': '?1',
# #     #     'upgrade-insecure-requests': '1',
# #     #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
# #     # }
# #     headers = {
# #         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
# #     'accept-language': 'en-US,en;q=0.9',
# #     'priority': 'u=0, i',
# #     # 'referer': 'https://www.petsupermarket.com/dog/food/dry-food/',
# #     'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
# #     'sec-ch-ua-mobile': '?0',
# #     'sec-ch-ua-platform': '"Windows"',
# #     'sec-fetch-dest': 'document',
# #     'sec-fetch-mode': 'navigate',
# #     'sec-fetch-site': 'same-origin',
# #     'sec-fetch-user': '?1',
# #     'upgrade-insecure-requests': '1',
# #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
# #     # 'cookie': '***HIDDEN***',
# # }
# #     conn = db.get_db_connection(db.db_name)
# #     cursor = conn.cursor()
# #     cursor.execute(f"SELECT id, url, hash_key FROM {db.link_table} WHERE status = 'pending' limit 1000")
# #     links = cursor.fetchall()
# #     conn.close()
# #     print(f"Total links: {len(links)}")
# #     for i, row in enumerate(links, 1):
# #         link_id = row['id']
# #         url = row['url']
# #         hash_key = row['hash_key']
# #     # for i, (link_id, url, hash_key) in enumerate(links, 1):
# #         try:
# #             print(f"\n===== {i}/{len(links)} =====")
# #             process_product(link_id, url, headers, hash_key)
# #         except Exception as e:
# #             print("❌ Error:", e)
# #             continue
# #
# #
# # if __name__ == "__main__":
# #     main()
#
#
# import json
# import time
# import os
# import random
# import requests
# # from curl_cffi import requests
# from parsel import Selector
# import db_config as db
# import html
# import tls_client
# proxy = {
#    "http": f'http://{db.proxy_token}:super=false@proxy.scrape.do:8080',
#    "https": f'http://{db.proxy_token}:super=false@proxy.scrape.do:8080',
# }
# API_URL = "https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Product-updateSubscription"
#
#
# # ✅ Update status
# def update_status(link_id):
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor()
#     cursor.execute(f"UPDATE {db.link_table} SET status = 'done' WHERE id = %s", (link_id,))
#     conn.commit()
#     conn.close()
#
# def build_payload(sel, pid):
#     # 1️⃣ Shipment type (DTC / SDD / BOPIS)
#     shipment = "DTC"
#     if sel.xpath('//button[contains(@class,"in-store-pickup-pdp") and contains(@class,"selected")]').get():
#         shipment = "BOPIS"
#     elif sel.xpath('//button[contains(@class,"same-day-pdp") and contains(@class,"selected")]').get():
#         shipment = "SDD"
#     elif sel.xpath('//button[contains(@class,"ship-to-home-pdp") and contains(@class,"selected")]').get():
#         shipment = "DTC"
#     # 2️⃣ AutoShip detection (old working logic preserved)
#     autoship_radio = sel.xpath('//input[@value="autoshipandsave"]')
#     is_autoship = False
#     if autoship_radio:
#         checked = autoship_radio.xpath('./@checked').get()
#         if checked is not None:
#             is_autoship = True
#     # 3️⃣ Options (AutoShip dropdown) — old working logic preserved
#     options_payload = []
#     if is_autoship:
#         option_elem = sel.xpath(
#             '//div[@data-option-id="AutoShipOptions"]//option[@selected]/@data-value-id'
#         ).get()
#         if not option_elem:
#             # fallback to first option
#             option_elem = sel.xpath(
#                 '//div[@data-option-id="AutoShipOptions"]//option[1]/@data-value-id'
#             ).get()
#         if option_elem:
#             options_payload.append({
#                 "optionId": "AutoShipOptions",
#                 "selectedValueId": option_elem
#             })
#     # 4️⃣ Final payload
#     data = {
#         "pid": pid,
#         "options": json.dumps(options_payload),
#         "isAutoShipSelected": str(is_autoship).lower(),
#         "shipment": shipment
#     }
#     return data
#
# def build_payload_buy_once(sel, pid):
#     data = {
#         "pid": pid,
#         "options": [],
#         "isAutoShipSelected": "false",
#         "shipment": "DTC"
#     }
#     return data
#
# # ✅ Process single product
# def process_product(link_id, url, headers, hash_key):
#     print(f"\nProcessing: {url}")
#     # proxy = get_random_proxy()
#     # print("Using Proxy:", proxy)
#     # session = tls_client.Session(
#     #     client_identifier="chrome_142",
#     #     random_tls_extension_order=True
#     # )
#
#     # session = requests.Session()
#
#     # res = requests.get(url, headers=headers, impersonate="chrome110")
#     res = requests.get(url, headers=headers, proxies=proxy, verify=False)
#     pdp_file_path = os.path.join(db.PDP_PAGESAVE, f"{hash_key}.html")
#
#     if res.status_code != 200:
#         print("❌ Failed main page:", res.status_code)
#         return
#
#     # Save PDP page
#     with open(pdp_file_path, "w", encoding='utf-8') as f:
#         f.write(res.text)
#
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
#         referer = item['referer']
#         print(f"→ Variant PID: {pid}")
#         # rep = session.get(referer, headers=headers, impersonate="chrome110")
#         rep = requests.get(referer, headers=headers, proxies=proxy, verify=False)
#         headers['referer'] = url
#
#         sel_variant = Selector(text=rep.text)
#         # payload = build_payload_buy_once(sel_variant, pid)
#         # print("Payload:", payload)
#         payload = {
#             "pid": pid
#         }
#         # api_res = session.post(
#         #     API_URL,
#         #     headers=headers,
#         #     data=payload,
#         #     impersonate="chrome110"
#         # )
#         api_res = requests.post(
#             API_URL,
#             headers=headers,
#             data=payload,
#             proxies=proxy,
#             verify=False
#         )
#
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
#
# def load_proxies(file_path):
#     proxy_list = []
#     with open(file_path, "r", encoding="utf-8") as f:
#         for line in f:
#             line = line.strip()
#             if not line:
#                 continue
#             parts = line.split(":")
#             if len(parts) != 4:
#                 print(f"Invalid proxy format: {line}")
#                 continue
#             ip, port, user, pwd = parts
#             proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
#             proxy_list.append(proxy_url)
#     return proxy_list
#
# def get_random_proxy():
#     if not PROXIES:
#         return None
#     proxy = random.choice(PROXIES)
#     return {
#         "http": proxy,
#         "https": proxy
#     }
#
# def main():
#     headers = {
#         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#         'accept-language': 'en-US,en;q=0.9',
#         'cache-control': 'max-age=0',
#         'priority': 'u=0, i',
#         'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'document',
#         'sec-fetch-mode': 'navigate',
#         'sec-fetch-site': 'same-origin',
#         'sec-fetch-user': '?1',
#         'upgrade-insecure-requests': '1',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
#     }
#
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor()
#     cursor.execute(f"SELECT id, url, hash_key FROM {db.link_table} WHERE status = 'pending' ORDER BY id DESC limit 10 ")
#     links = cursor.fetchall()
#     conn.close()
#
#     print(f"Total links: {len(links)}")
#
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
#     PROXY_FILE = r"D:\Julee\CODE\pet_supermaket\iproyal-proxies.txt"
#     PROXIES = load_proxies(PROXY_FILE)
#     print("Loaded proxies:", len(PROXIES))
#     main()



import json
import time
import os
from curl_cffi import requests
from parsel import Selector
import db_config_1 as db
import html
import tls_client

API_URL = "https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Product-updateSubscription"
proxy = {"http": f'http://{db.proxy_token}:render=true&super=true@proxy.scrape.do:8080',
         "https": f'http://{db.proxy_token}:render=true&super=true@proxy.scrape.do:8080'}
cookies = {
    'ttcsid_CH8KFEJC77U3VDB5OC4G': '1788175184639::LvAoJZhC8ExiL_SpI2Bw.4.1788175295431.1',
    'ttcsid': '1788173668091::7xXJuPt4FUWmuPbu2_sj.4.1788175295428.0::1.1623773.1626845::2345018.13.176.786::2320556.177.596',
    '_pxvid': '***HIDDEN***',
    '__pxvid': 'ee283187-a52f-11f1-b3aa-b21d2504a196',
    'rskxRunCookie': '0',
    'rCookie': '6fejcr1cw7he5670wt74iwmth5v3wr',
    'og_session_id': '***HIDDEN***',
    'osano_consentmanager_uuid': '367b6434-0e15-44c4-b5d2-3b15adb26aaa',
    'osano_consentmanager': 'zvZtGqwW6XIk11sIeK11G0zYV1nsqons56I8TsRr5w7HfOOcNwo8vUVAnQdQ77b27fUpD6E4BxdWqTKj-Y8on6rPEpD0x47Bgv-DLXA8LOJbpapPwsN95eNn1Qtjug6iNB6xeQV87VYIb3h9BWeSpYcL3a2U7hIb9p2XkfMUpZ73JdT3ssGet_eaYbaDPyUUprMPbOTUWunMbU4rCGeN21jkWfV-kOUW7YUFbyZ3agZ9QUVo-zvrHQK8Jl-WVPGQTEQc8-FhB0m4Pf3AjwXqOxP_mlD9NXZfLPiysDTjtZAxYPjdF3jp3W_svIv3hL6Q',
    '_pxhd': '***HIDDEN***',
    'dwanonymous_4053305edc20ff64eb8871bb843fe7be': '***HIDDEN***',
    'cqcid': 'bcaUVUZa8KzTIFtfJgI6QsBKzf',
    'cquid': '||',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    '__cqact': '%5B%7B%22activityType%22%3A%22addToCart%22%2C%22parameters%22%3A%7B%22cookieId%22%3A%22bcaUVUZa8KzTIFtfJgI6QsBKzf%22%2C%22userId%22%3A%22%22%2C%22product%22%3A%7B%22id%22%3A%22PSI10527%22%2C%22sku%22%3A%224994505891%22%2C%22quantity%22%3A1%2C%22changeQty%22%3A1%7D%2C%22realm%22%3A%22BGTK%22%2C%22siteId%22%3A%22PetSupermarket%22%2C%22instanceType%22%3A%22prd%22%2C%22locale%22%3A%22default%22%7D%7D%5D',
    'DeviceFingerPrintId': '6fejcr1cw7he5670wt74iwmth5v3wr',
    'dwac_aebb837897655f6bf10f0cf8c8': 'rSHTQBm3r4kSkGcyFVqFT-MIlKeB9sjjvcQ%3D|dw-only|||USD|false|America%2FNew%5FYork|true',
    'sid': 'rSHTQBm3r4kSkGcyFVqFT-MIlKeB9sjjvcQ',
    'dwapupreq': '1789973615377',
    'dwsid': 'pKwyNw8v7h6BJDAcfLoc-uqFddCXbol0LnCrxUJeprxt7-xw5MeCTZT9SHVoGb_MRO3vbMijhCkz1qL7gDWhvg==',
    'riskifiedSessionId': 'rSHTQBm3r4kSkGcyFVqFT-MIlKeB9sjjvcQ=',
    'LastClick': '"{\\"datetime\\":\\"2026-09-21T06:53:41.470Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
    'FirstClick': '"{\\"datetime\\":\\"2026-09-21T06:53:41.470Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
    'lastRskxRun': '1789973623290',
    'geo_permission_denied': 'true',
    '_px2': '***HIDDEN***',
    'pxcts': '***HIDDEN***',
}

# ✅ Update status
def update_status(link_id):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {db.link_table} SET status = 'redirect' WHERE id = %s", (link_id,))
    conn.commit()
    conn.close()

def build_payload(sel, pid):
    # 1️⃣ Shipment type (DTC / SDD / BOPIS)
    shipment = "DTC"
    if sel.xpath('//button[contains(@class,"in-store-pickup-pdp") and contains(@class,"selected")]').get():
        shipment = "BOPIS"
    elif sel.xpath('//button[contains(@class,"same-day-pdp") and contains(@class,"selected")]').get():
        shipment = "SDD"
    elif sel.xpath('//button[contains(@class,"ship-to-home-pdp") and contains(@class,"selected")]').get():
        shipment = "DTC"
    # 2️⃣ AutoShip detection (old working logic preserved)
    autoship_radio = sel.xpath('//input[@value="autoshipandsave"]')
    is_autoship = False
    if autoship_radio:
        checked = autoship_radio.xpath('./@checked').get()
        if checked is not None:
            is_autoship = True
    # 3️⃣ Options (AutoShip dropdown) — old working logic preserved
    options_payload = []
    if is_autoship:
        option_elem = sel.xpath(
            '//div[@data-option-id="AutoShipOptions"]//option[@selected]/@data-value-id'
        ).get()
        if not option_elem:
            # fallback to first option
            option_elem = sel.xpath(
                '//div[@data-option-id="AutoShipOptions"]//option[1]/@data-value-id'
            ).get()
        if option_elem:
            options_payload.append({
                "optionId": "AutoShipOptions",
                "selectedValueId": option_elem
            })
    # 4️⃣ Final payload
    data = {
        "pid": pid,
        "options": json.dumps(options_payload),
        "isAutoShipSelected": str(is_autoship).lower(),
        "shipment": shipment
    }
    return data

def build_payload_buy_once(sel, pid):
    data = {
        "pid": pid,
        "options": [],
        "isAutoShipSelected": "false",
        "shipment": "DTC"
    }
    return data

# ✅ Process single product
def process_product(link_id, url, headers, hash_key):
    print(f"\nProcessing: {url}")

    # session = requests.Session()
    from curl_cffi import requests as req
    # res = req.get(url, headers=headers, cookies=cookies, impersonate="chrome110", allow_redirects=True)
    res = requests.get(url, headers=headers, proxies=proxy, allow_redirects=True,verify=False, timeout=60)
    # print(res.headers)
    print("--------------------------------------------------------------------------")
    print("Status:", res.status_code)
    print("Final URL:", res.url)
    print("Headers:", res.headers)
    print("Response:", res.text[:2000])
    print("-" * 100)
    # res = session.get(url, headers=headers)
    pdp_file_path = os.path.join(db.PDP_PAGESAVE, f"{hash_key}.html")
    session = tls_client.Session(
        client_identifier="chrome_142",
        random_tls_extension_order=True
    )
    if res.status_code != 200:
        print("❌ Failed main page:", res.status_code)
        return

    # Save PDP page
    with open(pdp_file_path, "w", encoding='utf-8') as f:
        f.write(res.text)

    sel = Selector(text=res.text)

    # 1️⃣ Try JSON-LD first
    variants_data = []
    scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
    for script in scripts:
        try:
            data = json.loads(script)
            if data.get('@type') == 'Product':
                offers = data['offers']['offers']
                for offer in offers:
                    variants_data.append({
                        "pid": offer['sku'],
                        "referer": offer['url']
                    })
                break
        except:
            continue

    # 2️⃣ Fallback to pr-pdp-components
    if not variants_data:
        print("⚠️ No JSON-LD offers → using fallback")
        raw = sel.xpath('//div[@class="pr-pdp-components"]/@data-pr-pdp-components').get()
        if raw:
            decoded = html.unescape(raw)
            data = json.loads(decoded)
            referer = data['product']['url']
            for v in data['product']['variants']:
                variants_data.append({
                    "pid": v['page_id_variant'],
                    "referer": referer
                })

    if not variants_data:
        print("❌ No variants found at all")
        return

    # 3️⃣ Process each variant
    for item in variants_data:
        pid = item['pid']
        referer = item['referer']
        print(f"→ Variant PID: {pid}")
        # rep = session.get(referer, headers=headers, impersonate="chrome110")
        # rep = session.get(referer, headers=headers, cookies=cookies)
        rep = requests.get(referer, headers=headers, proxies=proxy, verify=False)
        headers['referer'] = url

        sel_variant = Selector(text=rep.text)
        # payload = build_payload_buy_once(sel_variant, pid)
        # print("Payload:", payload)
        # payload = {
        #     "pid": pid
        # }
        payload = {
            "pid": pid,
            "options": [],
            "isAutoShipSelected": "false",
            "shipment": "DTC"
        }
        # api_res = session.post(
        #     API_URL,
        #     headers=headers,
        #     cookies=cookies,
        #     data=payload,
        #     # impersonate="chrome110"
        # )
        api_res = requests.post(
            API_URL,
            headers=headers,
            data=payload,
            proxies = proxy,
            verify=False
        )

        # Save API response
        variation_folder = os.path.join(db.PDP_PAGESAVE, "variation_pagesave")
        os.makedirs(variation_folder, exist_ok=True)
        data_file_path = os.path.join(variation_folder, f"{pid}.json")
        if api_res.status_code == 200:
            try:
                with open(data_file_path, "w", encoding='utf-8') as f:
                    json.dump(api_res.json(), f, ensure_ascii=False, indent=4)
                print("Status:", api_res.status_code)
            except Exception as e:
                print("JSON save error:", e)
        elif api_res.status_code == 403:
            print("⚠️ Blocked (403) → retry later")
            return

        time.sleep(0.5)

    # ✅ Mark as done
    update_status(link_id)
    print("✅ Completed:", url)

# from concurrent.futures import ThreadPoolExecutor, as_completed
#
# MAX_WORKERS = 5  # 🔥 adjust (6–10 best)
#
# def main():
#     headers = {
#         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#         'accept-language': 'en-US,en;q=0.9',
#         'cache-control': 'max-age=0',
#         'priority': 'u=0, i',
#         'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'document',
#         'sec-fetch-mode': 'navigate',
#         'sec-fetch-site': 'same-origin',
#         'sec-fetch-user': '?1',
#         'upgrade-insecure-requests': '1',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
#     }
#
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor()
#     cursor.execute(f"SELECT id, url, hash_key FROM {db.link_table} WHERE status = 'pending'")
#     links = cursor.fetchall()
#     conn.close()
#
#     print(f"Total links: {len(links)}")
#
#     # 🔥 MULTITHREAD ONLY HERE
#     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
#         futures = []
#
#         for i, row in enumerate(links, 1):
#             link_id = row['id']
#             url = row['url']
#             hash_key = row['hash_key']
#
#             futures.append(
#                 executor.submit(process_product, link_id, url, headers.copy(), hash_key)
#             )
#
#         # optional: track progress
#         for i, future in enumerate(as_completed(futures), 1):
#             try:
#                 future.result()
#                 print(f"✅ Completed {i}/{len(futures)}")
#             except Exception as e:
#                 print("❌ Thread error:", e)

# ✅ Main runner
def main():
    headers =  {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': 'https://www.petsupermarket.com/dog/supplies/toys/balls-fetch-toys/dippin%E2%80%99-dots-flying-disc-and-tennis-ball-outdoor-play-dog-toy-set/PSI10527.html',
        'sec-ch-ua': '"Google Chrome";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36',
    }

    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, url, hash_key FROM {db.link_table} WHERE status = 'pending' ORDER BY id ASC limit 1")
    links = cursor.fetchall()
    conn.close()

    print(f"Total links: {len(links)}")

    for i, row in enumerate(links, 1):
        link_id = row['id']
        url = row['url']
        hash_key = row['hash_key']
        try:
            print(f"\n===== {i}/{len(links)} =====")
            process_product(link_id, url, headers, hash_key)
        except Exception as e:
            print("❌ Error:", e)
            continue


if __name__ == "__main__":
    main()