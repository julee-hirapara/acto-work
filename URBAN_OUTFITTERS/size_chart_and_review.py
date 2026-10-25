# import gzip
# import hashlib
# import json
# import os
# from urllib.parse import urlparse
# import random
# import pymysql
# import requests
# from parsel import Selector
# from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import sys
# sys.stdout.reconfigure(encoding='utf-8')
# import header_token as ht
# import db_config_1 as db
#
# MAX_THREADS = 1
#
#
# # def load_proxies(file_path):
# #     proxy_list = []
# #     with open(file_path, "r", encoding="utf-8") as f:
# #         for line in f:
# #             line = line.strip()
# #             if not line:
# #                 continue
# #             parts = line.split(":")
# #             if len(parts) != 4:
# #                 print(f"Invalid proxy format: {line}")
# #                 continue
# #             ip, port, user, pwd = parts
# #             proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
# #             proxy_list.append(proxy_url)
# #     return proxy_list
# #
# # def get_random_proxy():
# #     if not PROXIES:
# #         return None
# #     proxy = random.choice(PROXIES)
# #     return {
# #         "http": proxy,
# #         "https": proxy
# #     }
# # =========================
# # AUTH TOKEN
# # =========================
#
# def get_auth_token():
#     with open("token_data.json", "r", encoding='utf-8') as f:
#         token_data = json.load(f)
#
#     reauth_token = token_data.get("reauthToken")
#     print("reauth_token :: ", reauth_token)
#     headers = {
#         'authorization': 'Bearer ***HIDDEN***',
#         'content-type': 'application/json',
#     }
#     response = requests.put(
#         'https://www.urbanoutfitters.com/slipstream/api/token/v0/uo-us/auth',
#         headers=headers,
#         json={'reauthToken': reauth_token},
#     )
#     print("STATUS:", response.status_code)
#     print("TEXT:", response.text[:500])
#     data = response.json()
#
#     with open("token_data.json", "w", encoding='utf-8') as f:
#         json.dump(data, f, indent=4)
#
#     return data.get("authToken")
#
#
# # =========================
# # HELPERS
# # =========================
# def url_to_id(url):
#     return str(int(hashlib.sha256(url.encode()).hexdigest(), 16))[:12]
#
#
# def safe_json_load(data):
#     try:
#         while isinstance(data, str):
#             data = json.loads(data)
#     except:
#         pass
#     return data
#
#
# # =========================
# # EXTRACT FROM SAVED HTML
# # =========================
# def extract_size_slug_data(url, hash_id):
#     # hash_id = url_to_id(url)
#     file_path = f"{db.DATA_PAGESAVE}\\{hash_id}.html.gz"
#     if not os.path.exists(file_path):
#         print(f"❌ Missing file: {file_path}")
#         return None
#     with gzip.open(file_path, "rt", encoding="utf-8") as f:
#         html_content = f.read()
#     sel = Selector(text=html_content)
#     state_block = sel.xpath('//script[@id="urbnInitialPiniaState"]/text()').get()
#     if not state_block:
#         print("❌ No state block")
#         return None
#     data = safe_json_load(state_block)
#     products = data.get("catalog", {}).get("products", {})
#     slug = urlparse(url).path.split("/")[-1]
#     product_root = products.get(slug) or next(iter(products.values()), {})
#     if not product_root:
#         print("❌ product_root missing")
#         return None
#     product_data = product_root.get("product", {})
#     # product_data = "UO_WOMENS_BELTS"
#     # print(product_data.get("sizeGuide"))
#     return (
#         product_data.get("sizeGuide"),
#         # "UO_WOMENS_BELTS",
#         hash_id,
#         product_data.get("productId")
#     )
#
# def clean_text(value):
#     if not isinstance(value, str):
#         return value
#     return " ".join(value.split())
#
# # =========================
# # SIZE CHART
# # =========================
# def fetch_size_chart(size_guide_slug, auth_token, hash_id):
#     file_path = os.path.join(db.SIZE_PAGESAVE, f"{hash_id}_size_chart.json")
#     if os.path.exists(file_path):
#         with open(file_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#     else:
#         cookies = {
#             'SSLB': '1',
#             '_pxvid': '***HIDDEN***',
#             'urbn_data_center_id': 'US-PA',
#             'urbn_tracer': 'LEXQESYA6S',
#             'urbn_geo_region': 'US-PA',
#             '__pxvid': 'b03cad7d-2db5-11f1-99d4-9e8f96808f96',
#             'utag_main_v_id': '***HIDDEN***',
#             '_fbp': 'fb.1.1775039383697.652203888273911344.Bg',
#             'rbuid': 'rbos-2eb03fc8-3d80-408f-8573-d6fa18b42381',
#             '__attentive_id': '***HIDDEN***',
#             '_attn_': '***HIDDEN***',
#             '__attentive_cco': '1775039387893',
#             '_ga': 'GA1.1.1466779818.1775039388',
#             'smartDash': '031a3f32-70dc-4266-b4ae-fc79b849938f',
#             '_scid': 'nQYPhl7nyqhHTQq3wqa7pXcbywujvLhO',
#             '_tt_enable_cookie': '1',
#             '_ttp': '01KN49FDXTMA8SZ3TDJJQZG4A5_.tt.1',
#             '_svsid': '***HIDDEN***',
#             '_lc2_fpi': '18c6eee2a756--01kn49fepv38e014tvq4neqyqx',
#             '__adroll_fpc': '***HIDDEN***',
#             '_gcl_aw': 'GCL.1775041735.EAIaIQobChMIn5e62rjMkwMVpUb_AR2umBjfEAAYASAAEgKaEfD_BwE',
#             '_gcl_dc': 'GCL.1775041735.EAIaIQobChMIn5e62rjMkwMVpUb_AR2umBjfEAAYASAAEgKaEfD_BwE',
#             '_pin_unauth': 'dWlkPU9EbGhPRE0xTldFdE1qQXpOQzAwWkdRekxXRTJZVGN0Wm1JM01qWTRaR1ppWmpreA',
#             'BVBRANDID': '99fef85f-bef7-4395-b81c-7a5f51236d7c',
#             'pxcts': '***HIDDEN***',
#             'cebs': '1',
#             '_li_dcdm_c': '.urbanoutfitters.com',
#             '_lc2_fpi_js': '18c6eee2a756--01kn49fepv38e014tvq4neqyqx',
#             '_ce.clock_data': '***HIDDEN***',
#             '__attentive_dv': '1',
#             '_sctr': '1%7C1778005800000',
#             '_clck': '1j5s1ts%5E2%5Eg5t%5E1%5E2317',
#             'ss-enable-401-reauth-modal': '1',
#             'ss-enable-multi-label-returns': 'true',
#             'SSID': '***HIDDEN***',
#             'SSSC': '***HIDDEN***',
#             'SSRT': '***HIDDEN***',
#             'urbn_auth_payload': '***HIDDEN***',
#             'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+May+06+2026+13%3A35%3A50+GMT%2B0530+(India+Standard+Time)&version=202403.1.0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&consentId=149a6e87-d7a3-4df9-afda-e4fc6727252a&interactionCount=0&isAnonUser=1&landingPath=https%3A%2F%2Fwww.urbanoutfitters.com%2Fshop%2Fbdg-jaya-baggy-boyfriend-jean%3Fcolor%3D106%26type%3DREGULAR%26quantity%3D1%26size%3D26&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1',
#             '_px3': '***HIDDEN***',
#             'utag_main__sn': '8',
#             'utag_main_ses_id': '1778054750513%3Bexp-session',
#             'utag_main__pn': '1%3Bexp-session',
#             'utag_main_isLoggedIn': 'false%3Bexp-session',
#             'utag_main__ss': '0%3Bexp-session',
#             'utag_main_tag_session_256': '1%3Bexp-session',
#             'utag_main_dc_visit': '8',
#             'utag_main_dc_event': '1%3Bexp-session',
#             'mp_urbn_urbanoutfitters_na_mixpanel': '%7B%22distinct_id%22%3A%20%2219d4897912014c-024d279c9814968-26061f51-e1000-19d489791215f3%22%2C%22bc_persist_updated%22%3A%201775041750770%2C%22g_search_engine%22%3A%20%22google%22%7D',
#             '_pxhd': '***HIDDEN***',
#             'utag_main_dc_region': 'ap-east-1%3Bexp-session',
#             'BVBRANDSID': '10ab2103-43d5-4fcb-a7d8-91ca2dd2a128',
#             'cebsp_': '7',
#             '_ce.s': '***HIDDEN***',
#             '_rdt_uuid': '1775039391202.a66e97b6-733f-4aaf-9cbf-4887b6a899cc',
#             '_gcl_au': '1.1.1347756862.1775039388.902696299.1778054747.1778054752',
#             'datadome': '***HIDDEN***',
#             '_uetsid': '***HIDDEN***',
#             '_uetvid': '***HIDDEN***',
#             '_scid_r': 's4YPhl7nyqhHTQq3wqa7pXcbywujvLhOjZ7I4Q',
#             '__attentive_session_id': '***HIDDEN***',
#             '__attentive_pv': '1',
#             '__attentive_ss_referrer': 'https://www.urbanoutfitters.com/shop/bdg-jaya-baggy-boyfriend-jean?color=106&type=REGULAR&quantity=1&size=26',
#             'ttcsid': '1778054738014::6fyz5Esywwlk7oFXdpnI.12.1778054754567.0::1.9057.14588::16528.4.779.743::4949.51.0',
#             'ttcsid_CC2K5NJC77U26CFATFP0': '1778054752600::fmS_HAKFbeYh4bPTZkFA.8.1778054754567.1',
#             'utag_main__se': '4%3Bexp-session',
#             'utag_main__st': '1778056554593%3Bexp-session',
#             '_ga_BBMWPLK0E5': 'GS2.1.s1778054746$o8$g1$t1778054754$j52$l0$h0',
#             '_clsk': '896qf8%5E1778054755224%5E5%5E0%5Eb.clarity.ms%2Fcollect',
#         }
#
#         headers = {
#             'accept': 'application/json, text/plain, */*',
#             'accept-language': 'en-US,en;q=0.9',
#             'authorization': auth_token,
#             'origin': 'https://www.urbanoutfitters.com',
#             'priority': 'u=1, i',
#             'referer': 'https://www.urbanoutfitters.com/',
#             'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
#             'sec-ch-ua-mobile': '?0',
#             'sec-ch-ua-platform': '"Windows"',
#             'sec-fetch-dest': 'empty',
#             'sec-fetch-mode': 'cors',
#             'sec-fetch-site': 'same-site',
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
#             'x-urbn-channel': 'web',
#             'x-urbn-country': 'IN',
#             'x-urbn-currency': 'USD',
#             'x-urbn-experience': 'ss',
#             'x-urbn-geo-region': 'US-PA',
#             'x-urbn-language': 'en-US',
#             'x-urbn-primary-data-center-id': 'US-PA',
#             'x-urbn-site-id': 'uo-us',
#         }
#         # Try multiple payloads
#         payloads = [
#             {
#                 'include': '4',
#                 'contentfulEnvironment': 'master',
#                 'content_type': 'sizeGuideConfiguration',
#                 'fields.slug': size_guide_slug,
#             },
#             {
#                 'include': '1',
#                 'contentfulEnvironment': 'master',
#                 'content_type': 'sizeGuideVendor',
#                 'fields.slug': size_guide_slug,
#             }
#         ]
#
#         data = None
#         for params in payloads:
#             response = requests.get(
#                 'https://api.urbanoutfitters.com/api/content/v1/uo-us/entries',
#                 headers=headers,
#                 params=params,
#                 cookies=cookies
#             )
#             print("payload :", params)
#             print("Trying:", response.url)
#             print("Status:", response.status_code)
#             if response.status_code == 200:
#                 temp_data = response.json()
#                 # valid result check
#                 if temp_data.get("items"):
#                     data = temp_data
#                     # save raw
#                     with open(file_path, "w", encoding="utf-8") as f:
#                         json.dump(data, f, indent=4)
#                     print("✅ Size chart found")
#                     break
#         if not data:
#             return None
#         # proxy = get_random_proxy()
#
#         # params = {
#         #     'include': '4',
#         #     'contentfulEnvironment': 'master',
#         #     'content_type': 'sizeGuideConfiguration',
#         #     'fields.slug': size_guide_slug,
#         # }
#         # response = requests.get(
#         #     'https://api.urbanoutfitters.com/api/content/v1/uo-us/entries',
#         #     headers=headers,
#         #     params=params,
#         #     cookies=cookies
#         #     # proxies=proxy,  # Use the proxy if available and if need to use.
#         #     # verify=False,
#         # )
#         # print(response)
#         # # print(response.text)
#         # data = response.json()
#         # # save raw
#         # if response.status_code == 200:
#         #     with open(file_path, "w", encoding="utf-8") as f:
#         #         json.dump(data, f, indent=4)
#     table = extract_size_guide_column_based(data)
#     formatted = clean_size_json(table)
#     # formatted = convert_to_row_format(table)
#     print(f"📏 Size chart done: {hash_id}")
#     size_data = json.dumps(formatted, ensure_ascii=False)
#     print(size_data)
#     return size_data
#
# # def extract_size_guide_column_based(response):
# #     try:
# #         guide = response["items"][0]["guides"][0]
# #         unit = guide["sizeConversions"][0]["defaultUnitOfMeasurement"].lower()
# #         # ✅ Safe HTML extraction
# #         html = None
# #         if unit == "inches":
# #             html = guide.get("sizeGuideInches")
# #             if not html and guide.get("inchesTables"):
# #                 html = guide["inchesTables"][0].get("tableHtml")
# #         else:
# #             html = guide.get("sizeGuideCentimeters")
# #             if not html and guide.get("centimetersTables"):
# #                 html = guide["centimetersTables"][0].get("tableHtml")
# #         # ❌ Still no HTML
# #         if not html or not isinstance(html, str):
# #             return []
# #         sel = Selector(text=html)
# #         # ✅ Expand headers with colspan
# #         header_cells = sel.xpath("//thead//tr[1]/th")
# #         expanded_headers = []
# #         for th in header_cells[1:]:  # skip "Alpha"
# #             text = th.xpath("string(.)").get()
# #             text = text.strip() if text else ""
# #             colspan = int(th.attrib.get("colspan", 1))
# #             expanded_headers.extend([text] * colspan)
# #         rows = sel.xpath("//tbody//tr")
# #         temp = [{} for _ in expanded_headers]
# #         for row in rows:
# #             cols = row.xpath("./th|./td")
# #             if not cols:
# #                 continue
# #             row_name = cols[0].xpath("string(.)").get()
# #             row_name = row_name.strip() if row_name else ""
# #             values = []
# #             for col in cols[1:]:
# #                 text = col.xpath("string(.)").get()
# #                 text = text.strip() if text else ""
# #                 colspan = int(col.attrib.get("colspan", 1))
# #                 values.extend([text] * colspan)
# #             # pad safely
# #             if len(values) < len(expanded_headers):
# #                 values.extend([""] * (len(expanded_headers) - len(values)))
# #             for i in range(len(expanded_headers)):
# #                 temp[i][row_name] = values[i]
# #         # ✅ Collapse expanded columns into unique sizes
# #         final = {}
# #         for i, size in enumerate(expanded_headers):
# #             if not size:
# #                 continue
# #             if size not in final:
# #                 final[size] = {}
# #             for key, val in temp[i].items():
# #                 if key not in final[size] or not final[size][key]:
# #                     final[size][key] = val
# #         # ✅ Convert to required format
# #         result_rows = []
# #         for size, data in final.items():
# #             row = {"Size": size}
# #             row.update(data)
# #             result_rows.append(row)
# #         return [{"row": result_rows}]
# #     except Exception as e:
# #         print("❌ Size parse error:", e)
# #         return []
#
#
# def extract_size_guide_column_based(response):
#     try:
#         results = [{"row": []}]   # ✅ single container
#         items = response.get("items", [])
#         if not items:
#             return None
#         for item in items:
#             html_list = []
#             # =========================
#             # OLD STRUCTURE
#             # =========================
#             if item.get("guides"):
#                 for guide in item.get("guides", []):
#                     unit = "inches"
#                     size_conversions = guide.get("sizeConversions", [])
#                     if size_conversions:
#                         default_conv = next(
#                             (c for c in size_conversions if c.get("isDefault")),
#                             size_conversions[0]
#                         )
#                         unit = default_conv.get(
#                             "defaultUnitOfMeasurement",
#                             "Inches"
#                         ).lower()
#                     html = None
#                     if "inch" in unit:
#                         html = guide.get("sizeGuideInches")
#                         if not html and guide.get("inchesTables"):
#                             html = guide["inchesTables"][0].get("tableHtml")
#                     else:
#                         html = guide.get("sizeGuideCentimeters")
#                         if not html and guide.get("centimetersTables"):
#                             html = guide["centimetersTables"][0].get("tableHtml")
#                     if not html:
#                         if guide.get("inchesTables"):
#                             html = guide["inchesTables"][0].get("tableHtml")
#                         elif guide.get("centimetersTables"):
#                             html = guide["centimetersTables"][0].get("tableHtml")
#                     if html:
#                         html_list.append(html)
#             # =========================
#             # NEW VENDOR STRUCTURE
#             # =========================
#             elif item.get("tables"):
#                 for table in item.get("tables", []):
#                     html = table.get("tableHtml")
#                     if html:
#                         html_list.append(html)
#             # =========================
#             # PROCESS ALL HTML TABLES
#             # =========================
#             for html in html_list:
#                 if not html or not isinstance(html, str):
#                     continue
#                 sel = Selector(text=html)
#                 # =========================
#                 # GET HEADER
#                 # =========================
#                 header_row = sel.xpath("//thead//tr[1]")
#                 headers = []
#                 header_cells = header_row.xpath("./th|./td")
#                 for cell in header_cells:
#                     text = cell.xpath("string(.)").get(default="").strip()
#                     colspan = int(cell.attrib.get("colspan", 1))
#                     headers.extend([text] * colspan)
#
#                 # =========================
#                 # DETECT TABLE TYPE
#                 # =========================
#                 thead_th_count = len(header_row.xpath("./th"))
#                 thead_td_count = len(header_row.xpath("./td"))
#                 is_column_table = False
#                 # if header row mixes th + td
#                 # it's a rotated column table
#                 if thead_th_count >= 1 and thead_td_count >= 1:
#                     is_column_table = True
#                 # =========================
#                 # COLUMN-BASED TABLE
#                 # =========================
#                 if is_column_table:
#                     header_label = headers[0]
#                     expanded_headers = headers[1:]
#                     rows = sel.xpath("//tbody//tr")
#                     temp = [{} for _ in expanded_headers]
#                     for row in rows:
#                         cols = row.xpath("./th|./td")
#                         if not cols:
#                             continue
#                         row_name = cols[0].xpath("string(.)").get(default="").strip()
#                         values = []
#                         for col in cols[1:]:
#                             text = col.xpath("string(.)").get(default="").strip()
#                             colspan = int(col.attrib.get("colspan", 1))
#                             values.extend([text] * colspan)
#                         if len(values) < len(expanded_headers):
#                             values.extend([""] * (len(expanded_headers) - len(values)))
#                         for i in range(len(expanded_headers)):
#                             temp[i][row_name] = values[i]
#                     final = {}
#                     for i, size in enumerate(expanded_headers):
#                         if not size:
#                             continue
#                         if size not in final:
#                             final[size] = {}
#                         for key, val in temp[i].items():
#                             if key not in final[size] or not final[size][key]:
#                                 final[size][key] = val
#                     result_rows = []
#                     for size, values in final.items():
#                         # keep inseam support
#                         if size.lower() == "inseam":
#                             row = {"Length": "Inseam"}
#                         else:
#                             row = {header_label: size}
#                         # add all converted columns
#                         for key, value in values.items():
#                             row[key] = value
#                         result_rows.append(row)
#                     results[0]["row"].extend(result_rows)
#                     # result_rows = []
#                     # for size, data in final.items():
#                     #     # special handling
#                     #     if size.lower() == "inseam":
#                     #         row = {"Length": "Inseam"}
#                     #     else:
#                     #         row = {header_label: size}
#                     #     row.update(data)
#                     #     result_rows.append(row)
#                     # results[0]["row"].extend(result_rows)
#                 # =========================
#                 # NORMAL ROW TABLE
#                 # =========================
#                 else:
#                     body_rows = sel.xpath("//tbody//tr")
#                     for row in body_rows:
#                         cols = row.xpath("./th|./td")
#                         if not cols:
#                             continue
#                         values = []
#                         for col in cols:
#                             text = col.xpath("string(.)").get(default="").strip()
#                             values.append(text)
#                         # match headers with row values
#                         row_data = {}
#                         for i in range(min(len(headers), len(values))):
#                             row_data[headers[i]] = values[i]
#                         if row_data:
#                             results[0]["row"].append(row_data)
#         return results
#     except Exception as e:
#         print("❌ Size parse error:", e)
#         return None
#
#
# def clean_size_json(data):
#     def clean(val):
#         if val is None:
#             return "N/A"
#         if isinstance(val, str):
#             # remove \n, \t and normalize spaces
#             val = val.replace("\n", " ").replace("\t", " ")
#             val = " ".join(val.split())  # removes extra spaces
#             if val == "":
#                 return "N/A"
#         return val
#     for block in data:
#         if not isinstance(block, dict):
#             continue
#         for row in block.get("row", []):
#             for key in row:
#                 row[key] = clean(row[key])
#     return data
#
#
# def convert_to_row_format(size_dict, unit="inch"):
#     rows = []
#     for size, values in size_dict.items():
#         row = {"Size": clean_text(size)}
#         for key, val in values.items():
#             row[clean_text(key)] = clean_text(val)
#         rows.append(row)
#     return [{"row": rows}]
#
#
# # =========================
# # REVIEWS
# # =========================
# def fetch_reviews_data(headers, product_id, hash_id):
#     file_path = os.path.join(db.REVIEW_PAGESAVE, f"{hash_id}_review.json")
#     if os.path.exists(file_path):
#         with open(file_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#     else:
#         url = f"https://api.urbanoutfitters.com/api/review/v0/uo-us/products/{product_id}/reviews"
#         params = {
#             "merchandise-class": "0112",
#             # "merchandise-class": "0148",
#             "offset": 0,
#             "limit": 5,  # first page size
#             "filter": "",
#             "sort": "submissionTime:desc"
#         }
#         response = requests.get(url, headers=headers, params=params)
#         print("_________________________________________________________________________________")
#         print(response.url)
#         if response.status_code != 200:
#             print(f"❌ HTTP {response.status_code}")
#             return None
#         if response.status_code == 200:
#             data = response.json()
#             # save first page (optional)
#             with open(file_path, "w", encoding="utf-8") as f:
#                 json.dump(data, f, indent=4, ensure_ascii=False)
#     return extract_review_data(data)
#
#
# def extract_review_data(data):
#     try:
#         reviews = []
#         for r in data.get("results", []):
#             date = None
#             if r.get("lastModificationTime"):
#                 try:
#                     date = datetime.fromisoformat(
#                         r["lastModificationTime"]
#                     ).strftime("%Y-%m-%d")
#                 except:
#                     pass
#
#             reviews.append({
#                 "review_name": r.get("userNickname"),
#                 "review_title": r.get("title"),
#                 "review_content": r.get("reviewText"),
#                 "rating": r.get("rating"),
#                 "review_date": date,
#                 "verified": r.get("verified", False)
#             })
#         return {"reviews": reviews}
#
#     except Exception as e:
#         print("❌ Review parse error:", e)
#         return None
#
#
# # =========================
# # WORKER
# # =========================
# # def process_product(url, auth_token, headers, hash_id):
# # # def process_product(url, hash_id):
# #     result = extract_size_slug_data(url, hash_id)
# #     if not result:
# #         return
# #     size_slug, hash_id, product_id = result
# #     print(f"🚀 Processing: {url}")
# #     try:
# #         if size_slug:
# #             fetch_size_chart(size_slug, auth_token, hash_id)
# #             # fetch_size_chart(size_slug, hash_id)
# #     except Exception as e:
# #         print("❌ Size error:", e)
# #     try:
# #         if product_id:
# #             reviews = fetch_reviews_data(headers, product_id, hash_id)
# #             # reviews = fetch_reviews_data(product_id)
# #             print(json.dumps(reviews))
# #     except Exception as e:
# #         print("❌ Review error:", e)
#
#
# # =========================
# # MAIN
# # =========================
#
# def process_product(url, auth_token, headers, hash_id):
#     result = extract_size_slug_data(url, hash_id)
#     if not result:
#         return None
#     size_slug, hash_id, product_id = result
#     print(f"🚀 Processing: {url}")
#     size_data = None
#     review_data = None
#     try:
#         if size_slug:
#             size_data = fetch_size_chart(size_slug, auth_token, hash_id)
#     except Exception as e:
#         print("❌ Size error:", e)
#     try:
#         if product_id:
#             review_data = fetch_reviews_data(headers, product_id, hash_id)
#     except Exception as e:
#         print("❌ Review error:", e)
#     return {
#         "hash_id": hash_id,
#         "size_chart": size_data,
#         "review_text": json.dumps(review_data, ensure_ascii=False) if review_data else None
#     }
#
# # def update_products_in_db(conn, results):
# #     try:
# #         with conn.cursor() as cursor:
# #             query = f"""
# #                 UPDATE {db.data_table}
# #                 SET
# #                     size_chart = %s,
# #                     review_text = %s,
# #                     status = 'done'
# #                 WHERE hash_id = %s
# #             """
# #
# #             values = [
# #                 (
# #                     r["size_chart"],
# #                     r["review_text"],
# #                     r["hash_id"]
# #                 )
# #                 for r in results
# #             ]
# #
# #             cursor.executemany(query, values)
# #
# #         conn.commit()
# #
# #         print(f"✅ Bulk updated {len(results)} rows")
# #
# #     except Exception as e:
# #         print("❌ DB bulk update error:", e)
#
# def update_product_in_db(conn, data):
#     try:
#         with conn.cursor() as cursor:
#             query = f"""
#                 UPDATE {db.data_table}
#                 SET
#                     size_chart = %s,
#                     review_text = %s,
#                     status = 'done'
#                 WHERE hash_id = %s
#             """
#             cursor.execute(query, (
#                 data["size_chart"],
#                 data["review_text"],
#                 data["hash_id"]
#             ))
#         conn.commit()
#         print(f"✅ Updated DB for {data['hash_id']}")
#     except Exception as e:
#         print("❌ DB update error:", e)
#
# def main(rows):
#     # auth_token = ht.get_urban_outfitters_token()
#     # auth_data = ht.get_urban_outfitters_token()
#     data = ht.get_urban_outfitters_token()
#     headers = data["headers"]
#     print(headers)
#     datadome_id = headers.get("x-datadome-clientid")
#     data_center_id = headers.get("x-urbn-primary-data-center-id")
#
#     print(datadome_id)
#     print(data_center_id)
#     # if you want token separately
#     auth_token = data["token"]
#
#     headers = {
#         'accept': 'application/json, text/plain, */*',
#         'accept-language': 'en-US,en;q=0.9',
#         'authorization': auth_token,
#         # 'x-datadome-clientid': auth_data["datadome"],
#         # 'x-urbn-primary-data-center-id': auth_data["data_center"],
#         'origin': 'https://www.urbanoutfitters.com',
#         'priority': 'u=1, i',
#         # 'referer': 'https://www.urbanoutfitters.com/',
#         'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'empty',
#         'sec-fetch-mode': 'cors',
#         'sec-fetch-site': 'same-site',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
#         'x-urbn-channel': 'web',
#         'x-urbn-country': 'IN',
#         'x-urbn-currency': 'USD',
#         'x-urbn-experience': 'ss',
#         'x-urbn-geo-region': 'US-PA',
#         'x-urbn-language': 'en-US',
#         'x-datadome-clientid': datadome_id,
#         'x-urbn-primary-data-center-id': data_center_id,
#         'x-urbn-site-id': 'uo-us',
#     }
#     conn = db.get_db_connection(db.db_name)
#     # for r in rows:
#         # process_product(r['link_url'], auth_token, headers, r['hash_id'])
#     with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#         futures = [
#             executor.submit(process_product, r['link_url'], auth_token, headers, r['hash_id'])
#             for r in rows
#         ]
#         for future in as_completed(futures):
#             try:
#                 result = future.result()
#                 if result:
#                     update_product_in_db(conn, result)
#             except Exception as e:
#                 print("❌ Thread error:", e)
#         # results_to_update = []
#         # for future in as_completed(futures):
#         #     try:
#         #         result = future.result()
#         #         if result:
#         #             results_to_update.append(result)
#         #     except Exception as e:
#         #         print("❌ Thread error:", e)
#         # # bulk update once
#         # if results_to_update:
#         #     update_products_in_db(conn, results_to_update)
#     conn.close()
#
#     # with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#     #     futures = [
#     #         executor.submit(process_product, r['link_url'], auth_token, headers, r['hash_id'])
#     #         # executor.submit(process_product, r['link_url'], r['hash_id'])
#     #         for r in rows
#     #     ]
#     #     for future in as_completed(futures):
#     #         try:
#     #             future.result()
#     #         except Exception as e:
#     #             print("❌ Thread error:", e)
#
#
# # =========================
# # ENTRY
# # =========================
# if __name__ == '__main__':
#     # PROXY_FILE = r"D:\Julee\CODE\URBAN_OUTFITTERS\iproyal-proxies.txt"
#     # PROXIES = load_proxies(PROXY_FILE)
#     # print("Loaded proxies:", len(PROXIES))
#     conn = db.get_db_connection(db.db_name)
#     cur = conn.cursor(pymysql.cursors.DictCursor)
#     # cur.execute(f"""
#     # SELECT t.*
#     # FROM {db.data_table} t
#     # JOIN (
#     #     SELECT hash_id, MAX(id) AS max_id
#     #     FROM {db.data_table}
#     #     WHERE status = 'pending'
#     #     GROUP BY hash_id
#     # ) x ON t.id = x.max_id
#     # LIMIT 150
#     # """)
#     # cur.execute(f"SELECT  * FROM {db.data_table} WHERE status = 'pending' limit 10")
#     cur.execute(f"SELECT  * FROM {db.data_table} WHERE hash_id ='108895362059' ")
#     rows = cur.fetchall()
#     main(rows)
#     cur.close()
#     conn.close()

import orjson
from parsel import Selector
import json
import re
import os
import pymysql
from concurrent.futures import ThreadPoolExecutor


def singular_pipesign(table):
    item = {}
    for raw in table.xpath("//tr"):
        key = raw.xpath(".//th//text()").get()
        if key:
            key = key.strip()
            item[key] = []
        for va in raw.xpath(".//td"):
            value = va.xpath(".//text()").get()
            if value:
                item[key].append(value.strip())
        # item[key] = " , ".join(item.get(key)).strip(" , ") if item.get(key) else "N/A"
    return item


def without_class_head_list_structure(table):
    item = {}
    for ta in table.xpath("//tr"):
        key = ta.xpath(".//*[@scope='col']//text()").get()
        if key:
            item[key] = []
        for ta_2 in ta.xpath(".//td"):
            value = ta_2.xpath(".//text").get()
            if value:
                item[key].append(value.strip())
    if not item:
        headers = table.xpath("//thead//th//text()").getall()
        all_raw = []
        for raw in table.xpath("//tbody//tr"):
            values = raw.xpath(".//td//text()").getall()
            if values:
                all_raw.append(values)
        merged_data = [dict(zip(headers, row)) for row in all_raw]
        headers = merged_data[0].keys()
        item = {
            header: re.sub(r'\s+', " ", " | ".join(row[header] for row in merged_data if header in row)).strip()
            for header in headers
        }
    else:
        counter = 0
        if item:
            for v in item.values():
                if not v:
                    counter += 1
        if counter:
            return singular_pipesign(table)
        else:
            pass
    return item

def check_and_scrape_td_col_structure(table):
    data_col = table.xpath("//tbody//tr//td[@scope='col']")
    data_cm = table.xpath("//tbody//tr//td[contains(text(), '(cm)') or contains(text(), '(in)')]")
    if not data_col and not data_cm:
        return None
    headers = []
    for th in table.xpath("//thead//th"):
        text = th.xpath("string(.)").get("").strip()
        colspan = int(th.xpath("./@colspan").get("1"))
        for _ in range(colspan):
            headers.append(text)
    base_label = headers[0] if headers else "Alpha"
    all_list = []
    for tr in table.xpath("//tr"):
        values = []
        for val in tr.xpath(".//td"):
            text = val.xpath("string(.)").get("").strip()
            colspan = int(val.xpath("./@colspan").get("1"))
            values.extend([text] * colspan)
        if values:
            all_list.append(values)
    item = {}
    for lt in all_list:
        key = lt[0]
        value = dict(zip(headers[1:], lt[1:]))
        item[key] = value
    item["_base_label"] = base_label
    return item

# def check_and_scrape_td_col_structure(table):
#     data_col = table.xpath("//tbody//tr//td[@scope='col']")
#     data_cm = table.xpath("//tbody//tr//td[contains(text(), '(cm)') or contains(text(), '(in)')]")
#     if not data_col and not data_cm:
#         return None
#     item = {}
#     all_list = []
#     # headers = table.xpath("//thead//th//text()").getall()
#     # headers = [x.strip() for x in table.xpath("//thead//th//text()").getall()]
#     headers = []
#     for th in table.xpath("//thead//th"):
#         text = th.xpath("string(.)").get("").strip()
#         colspan = int(th.xpath("./@colspan").get("1"))
#         for _ in range(colspan):
#             headers.append(text)
#     base_label = headers[0] if headers else "Size"
#     for tr in table.xpath("//tr"):
#         values = []
#         # for val in tr.xpath(".//td"):
#         #     values.append(val.xpath(".//text()").get("N/A").strip())
#         for val in tr.xpath(".//td"):
#             text = val.xpath("string(.)").get("").strip()
#             colspan = int(val.xpath("./@colspan").get("1"))
#             values.append(text)
#             for _ in range(colspan - 1):
#                 values.append(text)
#             # for _ in range(colspan):
#             #     values.append(text)
#         if values:
#             all_list.append(values)
#     item = {}
#     for lt in all_list:
#         key = lt[0]
#         value = dict(zip(headers[1:], lt[1:]))
#         item[key] = value
#     item["_base_label"] = base_label
#     return item


def parse_head_list_structure(table):
    th_class = table.xpath("//thead//th[@class]").getall()
    td_class = table.xpath("//thead//td[@class]").getall()
    if not th_class or td_class:
        return without_class_head_list_structure(table)
    item = {}
    for raw in table.xpath("//tr"):
        item[raw.xpath(".//th//text()").get("unknow")] = []
        for tr in raw.xpath(".//td"):
            item[raw.xpath(".//th//text()").get("unknow")].append(tr.xpath(".//text()").get("N/A"))
        item[raw.xpath(".//th//text()").get("unknow")] = " , ".join(
            item[raw.xpath(".//th//text()").get("unknow")]).strip(" , ")
    return item


def key_value_structure(table):
    th_class = table.xpath("//thead//th[@class]").getall()
    td_class = table.xpath("//thead//td[@class]").getall()
    if not th_class and not td_class:
        return without_class_head_list_structure(table)
    all_list = []
    item = {}
    headers = table.xpath("//thead//th//text()").getall()
    if headers:
        item = {k: [] for k in headers}
    for tr in table.xpath("//tr"):
        values = tr.xpath(".//td//text()").getall()
        if values:
            all_list.append(values)
    if all_list:
        for i in all_list:
            t = list(zip(headers, i))
            for another_loop in t:
                item[another_loop[0]].append(another_loop[-1])
        item = {k.strip(): " , ".join(v).strip(" , ") for k, v in item.items()}
    return item


def extract_table(table):
    table_data = check_and_scrape_td_col_structure(table)
    if table_data:
        return table_data
    html_ele = {}
    for header in table.xpath("//thead//tr//*"):
        key = str(header)
        if key.startswith("<th"):
            html_ele['th'] = html_ele.get("th", 0)
            html_ele['th'] += 1
        elif key.startswith("<td"):
            html_ele['td'] = html_ele.get("td", 0)
            html_ele['td'] += 1
        elif key.startswith("<tr"):
            html_ele['tr'] = html_ele.get("tr", 0)
            html_ele['tr'] += 1
    if "th" in list(html_ele.keys()) and "td" in list(html_ele.keys()):
        table_data = parse_head_list_structure(table)
    else:
        table_data = key_value_structure(table)
    return table_data


def main(record):
    file_name = fr"D:\Julee\PAGESAVES\URBAN_OUTFITTERS\06_2026\size_chart\{record['pid']}.json"
    if not os.path.exists(file_name):
        return None
    with open(file_name, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
    # data = record["size_chart_response"]
    # if isinstance(data, str):
    #     data = json.loads(data)
    extracted_data = {}
    try:
        for raw in data['items']:
            chart_name_title = raw.get("displayTitle")
            for raw_2 in raw['guides']:
                display_name = raw_2.get("displayName", "size_guide")
                extracted_data[display_name] = {}
                if "inchesTables" in (raw_2.keys()):
                    for raw_3 in raw_2['inchesTables']:
                        table = raw_3['tableHtml']
                        table = Selector(table)
                        extracted_data[display_name]['inches'] = extract_table(table)
                if "centimetersTables" in (raw_2.keys()):
                    for raw_3 in raw_2['centimetersTables']:
                        table = raw_3['tableHtml']
                        table = Selector(table)
                        extracted_data[display_name]['centimeters'] = extract_table(table)

    except Exception as e:
        e = str(e)
        if 'guides' in e:
            counter = 1
            for raw in data['items']:
                display_name = raw.get("displayTitle")
                for raw_2 in raw['tables']:
                    extracted_data[display_name] = extract_table(Selector(raw_2['tableHtml']))
                    counter += 1
        else:
            print(e)
    # if extracted_data:
    #     # print(extracted_data)
    final_output = []
    for chart_name, chart_values in extracted_data.items():
        units = []
        if "inches" in chart_values:
            units.append("in")
        if "centimeters" in chart_values:
            units.append("cm")
        if units == []:
            units = ["in"]
        # guides structure
        if isinstance(chart_values, dict) and (
                "inches" in chart_values or
                "centimeters" in chart_values
        ):
            if "inches" in chart_values:
                final_output.append(
                    convert_to_schema(
                        chart_name,
                        # chart_name_title,
                        chart_values["inches"],
                        "in",
                        units
                    )
                )
            if "centimeters" in chart_values:
                final_output.append(
                    convert_to_schema(
                        chart_name,
                        # chart_name_title,
                        chart_values["centimeters"],
                        "cm",
                        units
                    )
                )
        # tables structure
        else:
            final_output.append(
                convert_to_schema(
                    # chart_name_title,
                    chart_name,
                    chart_values,
                    "in",
                    units
                )
            )
    # con = get_connection()
    # cur = con.cursor()
    # try:
    #     cur.execute(
    #         "update data_062026 set size_chart=%s, status='done' where pid=%s",
    #         (json.dumps(final_output, ensure_ascii=False), record['pid'])
    #     )
    # finally:
    #     cur.close()
    #     con.close()
    # print(json.dumps(final_output, indent=2, ensure_ascii=False))
    con = None
    cur = None

    try:
        # #  pip install DBUtils
        # from dbutils.pooled_db import PooledDB
        #
        # pool = PooledDB(
        #     creator=pymysql,
        #     maxconnections=20,
        #     host='localhost',
        #     user='root',
        #     password='***HIDDEN***',
        #     database='urban_outfitters'
        # )
        # con = pool.connection()
        # cur = con.cursor()
        con = pymysql.connect(user='root', host='localhost', database='urban_outfitters', password='***HIDDEN***',
                              autocommit=True)
        cur = con.cursor(pymysql.cursors.DictCursor)
        updates = []
        updates.append(
            (json.dumps(final_output, ensure_ascii=False),record['pid'])
        )
        cur.executemany(
            """
            UPDATE data_062026
            SET size_chart=%s,
                status='done'
            WHERE pid=%s
            """,
            updates
        )
        con.commit()
    except Exception as e:
        print(f"PID {record['pid']} ERROR:", e)

    finally:
        if cur:
            cur.close()
        if con:
            con.close()
    # cur.execute("update data_062026 set size_chart=%s, status='done' where pid=%s",
    #             (json.dumps(final_output, ensure_ascii=False), record['pid']))
    # con.commit()
    print("Updated: ", record['pid'])


def normalize_key(text):
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
    return text.strip("_")

def get_unit_from_label(label):
    label = (label or "").lower()
    if "(in)" in label or " inch" in label or " inches" in label:
        return "in"
    if "(cm)" in label or " centimeter" in label or " centimeters" in label:
        return "cm"
    return ""

def convert_to_schema(chart_name, chart_data, unit, units):
    if not chart_data:
        return None
    # base_label = chart_data.pop("_base_label", "Size")
    base_label = chart_data.pop("_base_label", "Size") or "Alpha"
    base_key = normalize_key(base_label) or "alpha"
    keys = list(chart_data.keys())
    if not keys:
        return None
    # ==================================================
    # FORMAT 3
    # {
    #   "Waist": {"XS":"24","S":"26"},
    #   "Hip": {"XS":"34","S":"36"}
    # }
    # ==================================================
    if all(isinstance(v, dict) for v in chart_data.values()):
        all_sizes = []
        for values in chart_data.values():
            all_sizes.extend(values.keys())
        all_sizes = list(dict.fromkeys(all_sizes))
        base_key = normalize_key(base_label)
        column_type = "measurement"
        if any(x in base_label.lower() for x in ["alpha", "numeric", "size"]):
            column_type = "size_label"
        if column_type == "size_label":
            columns = [{
                "key": base_key,
                "label": base_label,
                "type": column_type
            }]
        else:
            columns = [{
                "key": base_key,
                "label": base_label,
                "type": column_type,
                "unit": get_unit_from_label(base_label),
            }]
        for key in keys:
            column_type = "measurement"
            if any(x in key.lower() for x in ["alpha", "numeric", "size"]):
                column_type = "size_label"
            if column_type == "size_label":
                columns.append({
                    "key": normalize_key(key),
                    "label": key,
                    "type": column_type
                })
            else:
                columns.append({
                    "key": normalize_key(key),
                    "label": key,
                    "type": column_type,
                    "unit": get_unit_from_label(key)
                })
        rows = []
        for size in all_sizes:
            row = {base_key: size}
            for key in keys:
                row[normalize_key(key)] = chart_data[key].get(size)
            rows.append(row)
        return {
            "chart_name": chart_name,
            "chart_type": "",
            "garment_type": "",
            "age_group": "",
            "fit_category": "",
            "gender": "",
            "default_unit": "in",
            "available_units": units,
            "columns": columns,
            "rows": rows
        }
    # ==================================================
    # FORMAT 2
    # pipe/comma separated strings
    # ==================================================
    normalized = {}
    for key, value in chart_data.items():
        if isinstance(value, str):
            if "|" in value:
                normalized[key] = [
                    x.strip()
                    for x in value.split("|")
                    if x.strip()
                ]
            elif "," in value:
                normalized[key] = [
                    x.strip()
                    for x in value.split(",")
                    if x.strip()
                ]
            else:
                normalized[key] = [value]
        else:
            normalized[key] = value
    chart_data = normalized
    # ==================================================
    # FORMAT 1
    # list structure
    # ==================================================
    # if not all(isinstance(v, list) for v in chart_data.values()):
    #     return None
    cleaned_chart_data = {}
    for key, value in chart_data.items():
        new_key = key.strip() if key else "Alpha"
        cleaned_chart_data[new_key] = value
    chart_data = cleaned_chart_data
    columns = []
    first_col = True
    # for key in chart_data.keys():
    #     column_type = "measurement"
    #     if any(x in key.lower() for x in ["alpha", "numeric", "size"]):
    #         column_type = "size_label"
    #     columns.append({
    #         "key": normalize_key(key),
    #         "label": key,
    #         "type": column_type,
    #         "unit": ""
    #     })
    for key in chart_data.keys():

        actual_label = key.strip() if key else "Alpha"
        actual_key = normalize_key(actual_label) or "alpha"

        column_type = "measurement"
        if any(x in actual_label.lower() for x in ["alpha", "numeric", "size"]):
            column_type = "size_label"
        if column_type == "size_label":
            columns.append({
                "key": actual_key,
                "label": actual_label,
                "type": column_type
            })
        else:
            columns.append({
                "key": actual_key,
                "label": actual_label,
                "type": column_type,
                "unit": get_unit_from_label(actual_label)
            })
        # columns.append({
        #     "key": actual_key,
        #     "label": actual_label,
        #     "type": column_type,
        #     "unit": get_unit_from_label(actual_label)
        # })
        first_col = False
    row_count = max(len(v) for v in chart_data.values())
    rows = []
    for i in range(row_count):
        row = {}
        for key in chart_data.keys():
            values = chart_data[key]
            row_key = normalize_key(key) or "alpha"
            row[row_key] = (
                values[i]
                if i < len(values)
                else ""
            )
            # row[normalize_key(key)] = (
            #     values[i]
            #     if i < len(values)
            #     else None
            # )
        rows.append(row)
    return {
        "chart_name": chart_name,
        "chart_type": "",
        "garment_type": "",
        "age_group": "",
        "fit_category": "",
        "gender": "",
        "default_unit": "in",
        "available_units": units,
        "columns": columns,
        "rows": rows
    }

# def convert_to_schema(chart_name, chart_data, unit, units):
#     keys = list(chart_data.keys())
#     if not keys:
#         return None
#     first_value = chart_data[keys[0]]
#     # ----------------------------------
#     # FORMAT 3
#     # nested dictionaries
#     # ----------------------------------
#     # if isinstance(first_value, dict):
#     if all(isinstance(v, dict) for v in chart_data.values()):
#         all_sizes = []
#         for values in chart_data.values():
#             all_sizes.extend(values.keys())
#         all_sizes = list(dict.fromkeys(all_sizes))
#         size_column = "size"
#         for candidate in ["size", "alpha", "length"]:
#             if candidate.lower() in [s.lower() for s in all_sizes]:
#                 size_column = normalize_key(candidate)
#                 break
#         columns = [{
#             "key": size_column,
#             "label": size_column.replace("_", " ").title(),
#             "type": "size_label"
#         }]
#         # all_sizes = []
#         # for values in chart_data.values():
#         #     all_sizes.extend(values.keys())
#         # all_sizes = list(dict.fromkeys(all_sizes))
#         # base_label = chart_data.pop("_base_label", "Size")
#         # base_key = normalize_key(base_label)
#         # columns = [{
#         #     "key": base_key,
#         #     "label": base_label,
#         #     "type": "size_label"
#         # }]
#         # columns = [{
#         #     "key": "size",
#         #     "label": "Size",
#         #     "type": "size_label"
#         # }]
#         for key in keys:
#             columns.append({
#                 "key": normalize_key(key),
#                 "label": key,
#                 "type": "measurement"
#             })
#         rows = []
#         for size in all_sizes:
#             row = {
#                 "size": size
#             }
#             for key in keys:
#                 row[normalize_key(key)] = (chart_data[key].get(size))
#             rows.append(row)
#         return {
#             "chart_name": chart_name,
#             "chart_type": "",
#             "garment_type": "",
#             "age_group": "",
#             "fit_category": "",
#             "gender": "",
#             "default_unit": "in",
#             "available_units": units,
#             "columns": columns,
#             "rows": rows
#         }
#     # ----------------------------------
#     # FORMAT 2
#     # comma-separated strings
#     # ----------------------------------
#     normalized = {}
#     for key, value in chart_data.items():
#         if isinstance(value, str):
#             if "|" in value:
#                 normalized[key] = [
#                     x.strip()
#                     for x in value.split("|")
#                     if x.strip()
#                 ]
#             elif "," in value:
#                 normalized[key] = [
#                     x.strip()
#                     for x in value.split(",")
#                     if x.strip()
#                 ]
#             else:
#                 normalized[key] = [value]
#         else:
#             normalized[key] = value
#     chart_data = normalized
#     # ----------------------------------
#     # FORMAT 1
#     # lists
#     # ----------------------------------
#     columns = []
#     for key in chart_data.keys():
#         columns.append({
#             "key": normalize_key(key),
#             "label": key,
#             "type": "size_label"
#         })
#     row_count = max(
#         len(v)
#         for v in chart_data.values()
#     )
#     rows = []
#     for i in range(row_count):
#         row = {}
#         for key in chart_data.keys():
#             values = chart_data[key]
#             row[normalize_key(key)] = (
#                 values[i]
#                 if i < len(values)
#                 else None
#             )
#         rows.append(row)
#     return {
#         "chart_name": chart_name,
#         "chart_type": "",
#         "garment_type": "",
#         "age_group": "",
#         "fit_category": "",
#         "gender": "",
#         # "chart_name": chart_name,
#         # "chart_type": "size_conversion",
#         "default_unit": "in",
#         "available_units": units,
#         "columns": columns,
#         "rows": rows
#     }


def get_connection():
    return pymysql.connect(
        user='root',
        host='localhost',
        database='urban_outfitters',
        password='***HIDDEN***',
        autocommit=True
    )

if __name__ == "__main__":
    # main()
    con = pymysql.connect(user='root', host='localhost', database='urban_outfitters', password='***HIDDEN***', autocommit=True)
    cur = con.cursor(pymysql.cursors.DictCursor)
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM data_062026 where status='done' AND pid='UO-107304768-000'")
    cur.execute(f"SELECT  DISTINCT main_url, pid FROM data_062026 where status='pending'")
    records = cur.fetchall()
    print(len(records))
    # con = pymysql.connect(user='root',host='localhost',database='urban_outfitters',password='***HIDDEN***')
    # cur = con.cursor(pymysql.cursors.DictCursor)
    # cur.execute("""
    #         SELECT DISTINCT main_url, pid, size_chart_response
    #         FROM data_062026
    #         WHERE status='pending'
    #         LIMIT 1000
    #     """)
    # records = cur.fetchall()
    # cur.close()
    # con.close()
    # with ThreadPoolExecutor(max_workers=10) as executor:
    #     executor.map(main, records)
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(main, record) for record in records]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("THREAD ERROR:", repr(e))
    # for record in records:
    #     main(record)