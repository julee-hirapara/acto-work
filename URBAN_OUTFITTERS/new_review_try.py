import gzip
import hashlib
import json
import os
from urllib.parse import urlparse
import random
import pymysql
import requests
from glom import glom
from parsel import Selector
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
sys.stdout.reconfigure(encoding='utf-8')
import header_token as ht
import db_config_1 as db

MAX_THREADS = 1


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
# =========================
# AUTH TOKEN
# =========================
def get_auth_token():
    with open("token_data.json", "r", encoding='utf-8') as f:
        token_data = json.load(f)

    reauth_token = token_data.get("reauthToken")
    print("reauth_token :: ", reauth_token)
    headers = {
        'authorization': 'Bearer ***HIDDEN***',
        'content-type': 'application/json',
    }
    response = requests.put(
        'https://www.urbanoutfitters.com/slipstream/api/token/v0/uo-us/auth',
        headers=headers,
        json={'reauthToken': reauth_token},
    )
    print("STATUS:", response.status_code)
    print("TEXT:", response.text[:500])
    data = response.json()

    with open("token_data.json", "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    return data.get("authToken")


# =========================
# HELPERS
# =========================
def url_to_id(url):
    return str(int(hashlib.sha256(url.encode()).hexdigest(), 16))[:12]


def safe_json_load(data):
    try:
        while isinstance(data, str):
            data = json.loads(data)
    except:
        pass
    return data

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
# =========================
# EXTRACT FROM SAVED HTML
# =========================
def extract_size_slug_data(url, hash_id):
    # hash_id = url_to_id(url)
    file_path = f"{db.DATA_PAGESAVE}\\{hash_id}.html.gz"

    if not os.path.exists(file_path):
        print(f"❌ Missing file: {file_path}")
        return None

    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        html_content = f.read()

    sel = Selector(text=html_content)
    state_block = sel.xpath('//script[@id="urbnInitialPiniaState"]/text()').get()
    if not state_block:
        print("❌ No state block")
        return None
    try:
        temp = json.loads(state_block)
        data_2 = json.loads(temp) if isinstance(temp, str) else temp
        slug = list(data_2['catalog']['products'].keys())[0]
        master_class = glom(data_2, f"catalog.products.{slug}.product.merchandiseClass", default=None)
    except Exception as e:
        print(e)
        return None
    data = safe_json_load(state_block)
    products = data.get("catalog", {}).get("products", {})

    slug = urlparse(url).path.split("/")[-1]
    product_root = products.get(slug) or next(iter(products.values()), {})

    if not product_root:
        print("❌ product_root missing")
        return None

    product_data = product_root.get("product", {})
    # product_data = "UO_WOMENS_BELTS"
    # print(product_data.get("sizeGuide"))
    return (
        master_class,
        # "UO_WOMENS_BELTS",
        hash_id,
        product_data.get("productId")
    )

def clean_text(value):
    if not isinstance(value, str):
        return value
    return " ".join(value.split())

# =========================
# SIZE CHART
# =========================
def fetch_size_chart(size_guide_slug, auth_token, hash_id):
    file_path = os.path.join(db.SIZE_PAGESAVE, f"{hash_id}_size_chart.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        cookies = {
            'SSLB': '1',
            '_pxvid': '***HIDDEN***',
            'urbn_data_center_id': 'US-PA',
            'urbn_tracer': 'LEXQESYA6S',
            'urbn_geo_region': 'US-PA',
            '__pxvid': 'b03cad7d-2db5-11f1-99d4-9e8f96808f96',
            'utag_main_v_id': '***HIDDEN***',
            '_fbp': 'fb.1.1775039383697.652203888273911344.Bg',
            'rbuid': 'rbos-2eb03fc8-3d80-408f-8573-d6fa18b42381',
            '__attentive_id': '***HIDDEN***',
            '_attn_': '***HIDDEN***',
            '__attentive_cco': '1775039387893',
            '_ga': 'GA1.1.1466779818.1775039388',
            'smartDash': '031a3f32-70dc-4266-b4ae-fc79b849938f',
            '_scid': 'nQYPhl7nyqhHTQq3wqa7pXcbywujvLhO',
            '_tt_enable_cookie': '1',
            '_ttp': '01KN49FDXTMA8SZ3TDJJQZG4A5_.tt.1',
            '_svsid': '***HIDDEN***',
            '_lc2_fpi': '18c6eee2a756--01kn49fepv38e014tvq4neqyqx',
            '__adroll_fpc': '***HIDDEN***',
            '_gcl_aw': 'GCL.1775041735.EAIaIQobChMIn5e62rjMkwMVpUb_AR2umBjfEAAYASAAEgKaEfD_BwE',
            '_gcl_dc': 'GCL.1775041735.EAIaIQobChMIn5e62rjMkwMVpUb_AR2umBjfEAAYASAAEgKaEfD_BwE',
            '_pin_unauth': 'dWlkPU9EbGhPRE0xTldFdE1qQXpOQzAwWkdRekxXRTJZVGN0Wm1JM01qWTRaR1ppWmpreA',
            'BVBRANDID': '99fef85f-bef7-4395-b81c-7a5f51236d7c',
            'pxcts': '***HIDDEN***',
            'cebs': '1',
            '_li_dcdm_c': '.urbanoutfitters.com',
            '_lc2_fpi_js': '18c6eee2a756--01kn49fepv38e014tvq4neqyqx',
            '_ce.clock_data': '***HIDDEN***',
            '__attentive_dv': '1',
            '_sctr': '1%7C1778005800000',
            '_clck': '1j5s1ts%5E2%5Eg5t%5E1%5E2317',
            'ss-enable-401-reauth-modal': '1',
            'ss-enable-multi-label-returns': 'true',
            'SSID': '***HIDDEN***',
            'SSSC': '***HIDDEN***',
            'SSRT': '***HIDDEN***',
            'urbn_auth_payload': '***HIDDEN***',
            'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+May+06+2026+13%3A35%3A50+GMT%2B0530+(India+Standard+Time)&version=202403.1.0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&consentId=149a6e87-d7a3-4df9-afda-e4fc6727252a&interactionCount=0&isAnonUser=1&landingPath=https%3A%2F%2Fwww.urbanoutfitters.com%2Fshop%2Fbdg-jaya-baggy-boyfriend-jean%3Fcolor%3D106%26type%3DREGULAR%26quantity%3D1%26size%3D26&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1',
            '_px3': '***HIDDEN***',
            'utag_main__sn': '8',
            'utag_main_ses_id': '1778054750513%3Bexp-session',
            'utag_main__pn': '1%3Bexp-session',
            'utag_main_isLoggedIn': 'false%3Bexp-session',
            'utag_main__ss': '0%3Bexp-session',
            'utag_main_tag_session_256': '1%3Bexp-session',
            'utag_main_dc_visit': '8',
            'utag_main_dc_event': '1%3Bexp-session',
            'mp_urbn_urbanoutfitters_na_mixpanel': '%7B%22distinct_id%22%3A%20%2219d4897912014c-024d279c9814968-26061f51-e1000-19d489791215f3%22%2C%22bc_persist_updated%22%3A%201775041750770%2C%22g_search_engine%22%3A%20%22google%22%7D',
            '_pxhd': '***HIDDEN***',
            'utag_main_dc_region': 'ap-east-1%3Bexp-session',
            'BVBRANDSID': '10ab2103-43d5-4fcb-a7d8-91ca2dd2a128',
            'cebsp_': '7',
            '_ce.s': '***HIDDEN***',
            '_rdt_uuid': '1775039391202.a66e97b6-733f-4aaf-9cbf-4887b6a899cc',
            '_gcl_au': '1.1.1347756862.1775039388.902696299.1778054747.1778054752',
            'datadome': '***HIDDEN***',
            '_uetsid': '***HIDDEN***',
            '_uetvid': '***HIDDEN***',
            '_scid_r': 's4YPhl7nyqhHTQq3wqa7pXcbywujvLhOjZ7I4Q',
            '__attentive_session_id': '***HIDDEN***',
            '__attentive_pv': '1',
            '__attentive_ss_referrer': 'https://www.urbanoutfitters.com/shop/bdg-jaya-baggy-boyfriend-jean?color=106&type=REGULAR&quantity=1&size=26',
            'ttcsid': '1778054738014::6fyz5Esywwlk7oFXdpnI.12.1778054754567.0::1.9057.14588::16528.4.779.743::4949.51.0',
            'ttcsid_CC2K5NJC77U26CFATFP0': '1778054752600::fmS_HAKFbeYh4bPTZkFA.8.1778054754567.1',
            'utag_main__se': '4%3Bexp-session',
            'utag_main__st': '1778056554593%3Bexp-session',
            '_ga_BBMWPLK0E5': 'GS2.1.s1778054746$o8$g1$t1778054754$j52$l0$h0',
            '_clsk': '896qf8%5E1778054755224%5E5%5E0%5Eb.clarity.ms%2Fcollect',
        }

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': auth_token,
            'origin': 'https://www.urbanoutfitters.com',
            'priority': 'u=1, i',
            'referer': 'https://www.urbanoutfitters.com/',
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
            'x-urbn-primary-data-center-id': 'US-PA',
            'x-urbn-site-id': 'uo-us',
        }
        # Try multiple payloads
        payloads = [
            {
                'include': '4',
                'contentfulEnvironment': 'master',
                'content_type': 'sizeGuideConfiguration',
                'fields.slug': size_guide_slug,
            },
            {
                'include': '1',
                'contentfulEnvironment': 'master',
                'content_type': 'sizeGuideVendor',
                'fields.slug': size_guide_slug,
            }
        ]

        data = None
        for params in payloads:
            response = requests.get(
                'https://api.urbanoutfitters.com/api/content/v1/uo-us/entries',
                headers=headers,
                params=params,
                cookies=cookies
            )
            print("payload :", params)
            print("Trying:", response.url)
            print("Status:", response.status_code)
            if response.status_code == 200:
                temp_data = response.json()
                # valid result check
                if temp_data.get("items"):
                    data = temp_data
                    # save raw
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    print("✅ Size chart found")
                    break
        if not data:
            return None
        # proxy = get_random_proxy()

        # params = {
        #     'include': '4',
        #     'contentfulEnvironment': 'master',
        #     'content_type': 'sizeGuideConfiguration',
        #     'fields.slug': size_guide_slug,
        # }
        # response = requests.get(
        #     'https://api.urbanoutfitters.com/api/content/v1/uo-us/entries',
        #     headers=headers,
        #     params=params,
        #     cookies=cookies
        #     # proxies=proxy,  # Use the proxy if available and if need to use.
        #     # verify=False,
        # )
        # print(response)
        # # print(response.text)
        # data = response.json()
        # # save raw
        # if response.status_code == 200:
        #     with open(file_path, "w", encoding="utf-8") as f:
        #         json.dump(data, f, indent=4)
    table = extract_size_guide_column_based(data)
    formatted = clean_size_json(table)
    # formatted = convert_to_row_format(table)
    print(f"📏 Size chart done: {hash_id}")
    size_data = json.dumps(formatted, ensure_ascii=False)
    print(size_data)
    return size_data

# def extract_size_guide_column_based(response):
#     try:
#         guide = response["items"][0]["guides"][0]
#         unit = guide["sizeConversions"][0]["defaultUnitOfMeasurement"].lower()
#         # ✅ Safe HTML extraction
#         html = None
#         if unit == "inches":
#             html = guide.get("sizeGuideInches")
#             if not html and guide.get("inchesTables"):
#                 html = guide["inchesTables"][0].get("tableHtml")
#         else:
#             html = guide.get("sizeGuideCentimeters")
#             if not html and guide.get("centimetersTables"):
#                 html = guide["centimetersTables"][0].get("tableHtml")
#         # ❌ Still no HTML
#         if not html or not isinstance(html, str):
#             return []
#         sel = Selector(text=html)
#         # ✅ Expand headers with colspan
#         header_cells = sel.xpath("//thead//tr[1]/th")
#         expanded_headers = []
#         for th in header_cells[1:]:  # skip "Alpha"
#             text = th.xpath("string(.)").get()
#             text = text.strip() if text else ""
#             colspan = int(th.attrib.get("colspan", 1))
#             expanded_headers.extend([text] * colspan)
#         rows = sel.xpath("//tbody//tr")
#         temp = [{} for _ in expanded_headers]
#         for row in rows:
#             cols = row.xpath("./th|./td")
#             if not cols:
#                 continue
#             row_name = cols[0].xpath("string(.)").get()
#             row_name = row_name.strip() if row_name else ""
#             values = []
#             for col in cols[1:]:
#                 text = col.xpath("string(.)").get()
#                 text = text.strip() if text else ""
#                 colspan = int(col.attrib.get("colspan", 1))
#                 values.extend([text] * colspan)
#             # pad safely
#             if len(values) < len(expanded_headers):
#                 values.extend([""] * (len(expanded_headers) - len(values)))
#             for i in range(len(expanded_headers)):
#                 temp[i][row_name] = values[i]
#         # ✅ Collapse expanded columns into unique sizes
#         final = {}
#         for i, size in enumerate(expanded_headers):
#             if not size:
#                 continue
#             if size not in final:
#                 final[size] = {}
#             for key, val in temp[i].items():
#                 if key not in final[size] or not final[size][key]:
#                     final[size][key] = val
#         # ✅ Convert to required format
#         result_rows = []
#         for size, data in final.items():
#             row = {"Size": size}
#             row.update(data)
#             result_rows.append(row)
#         return [{"row": result_rows}]
#     except Exception as e:
#         print("❌ Size parse error:", e)
#         return []


def extract_size_guide_column_based(response):
    try:
        results = [{"row": []}]   # ✅ single container
        items = response.get("items", [])
        if not items:
            return None
        for item in items:
            html_list = []
            # =========================
            # OLD STRUCTURE
            # =========================
            if item.get("guides"):
                for guide in item.get("guides", []):
                    unit = "inches"
                    size_conversions = guide.get("sizeConversions", [])
                    if size_conversions:
                        default_conv = next(
                            (c for c in size_conversions if c.get("isDefault")),
                            size_conversions[0]
                        )
                        unit = default_conv.get(
                            "defaultUnitOfMeasurement",
                            "Inches"
                        ).lower()
                    html = None
                    if "inch" in unit:
                        html = guide.get("sizeGuideInches")
                        if not html and guide.get("inchesTables"):
                            html = guide["inchesTables"][0].get("tableHtml")
                    else:
                        html = guide.get("sizeGuideCentimeters")
                        if not html and guide.get("centimetersTables"):
                            html = guide["centimetersTables"][0].get("tableHtml")
                    if not html:
                        if guide.get("inchesTables"):
                            html = guide["inchesTables"][0].get("tableHtml")
                        elif guide.get("centimetersTables"):
                            html = guide["centimetersTables"][0].get("tableHtml")
                    if html:
                        html_list.append(html)
            # =========================
            # NEW VENDOR STRUCTURE
            # =========================
            elif item.get("tables"):
                for table in item.get("tables", []):
                    html = table.get("tableHtml")
                    if html:
                        html_list.append(html)
            # =========================
            # PROCESS ALL HTML TABLES
            # =========================
            for html in html_list:
                if not html or not isinstance(html, str):
                    continue
                sel = Selector(text=html)
                # =========================
                # GET HEADER
                # =========================
                header_row = sel.xpath("//thead//tr[1]")
                headers = []
                header_cells = header_row.xpath("./th|./td")
                for cell in header_cells:
                    text = cell.xpath("string(.)").get(default="").strip()
                    colspan = int(cell.attrib.get("colspan", 1))
                    headers.extend([text] * colspan)

                # =========================
                # DETECT TABLE TYPE
                # =========================
                thead_th_count = len(header_row.xpath("./th"))
                thead_td_count = len(header_row.xpath("./td"))
                is_column_table = False
                # if header row mixes th + td
                # it's a rotated column table
                if thead_th_count >= 1 and thead_td_count >= 1:
                    is_column_table = True
                # =========================
                # COLUMN-BASED TABLE
                # =========================
                if is_column_table:
                    header_label = headers[0]
                    expanded_headers = headers[1:]
                    rows = sel.xpath("//tbody//tr")
                    temp = [{} for _ in expanded_headers]
                    for row in rows:
                        cols = row.xpath("./th|./td")
                        if not cols:
                            continue
                        row_name = cols[0].xpath("string(.)").get(default="").strip()
                        values = []
                        for col in cols[1:]:
                            text = col.xpath("string(.)").get(default="").strip()
                            colspan = int(col.attrib.get("colspan", 1))
                            values.extend([text] * colspan)
                        if len(values) < len(expanded_headers):
                            values.extend([""] * (len(expanded_headers) - len(values)))
                        for i in range(len(expanded_headers)):
                            temp[i][row_name] = values[i]
                    final = {}
                    for i, size in enumerate(expanded_headers):
                        if not size:
                            continue
                        if size not in final:
                            final[size] = {}
                        for key, val in temp[i].items():
                            if key not in final[size] or not final[size][key]:
                                final[size][key] = val
                    result_rows = []
                    for size, values in final.items():
                        # keep inseam support
                        if size.lower() == "inseam":
                            row = {"Length": "Inseam"}
                        else:
                            row = {header_label: size}
                        # add all converted columns
                        for key, value in values.items():
                            row[key] = value
                        result_rows.append(row)
                    results[0]["row"].extend(result_rows)
                    # result_rows = []
                    # for size, data in final.items():
                    #     # special handling
                    #     if size.lower() == "inseam":
                    #         row = {"Length": "Inseam"}
                    #     else:
                    #         row = {header_label: size}
                    #     row.update(data)
                    #     result_rows.append(row)
                    # results[0]["row"].extend(result_rows)
                # =========================
                # NORMAL ROW TABLE
                # =========================
                else:
                    body_rows = sel.xpath("//tbody//tr")
                    for row in body_rows:
                        cols = row.xpath("./th|./td")
                        if not cols:
                            continue
                        values = []
                        for col in cols:
                            text = col.xpath("string(.)").get(default="").strip()
                            values.append(text)
                        # match headers with row values
                        row_data = {}
                        for i in range(min(len(headers), len(values))):
                            row_data[headers[i]] = values[i]
                        if row_data:
                            results[0]["row"].append(row_data)
        return results
    except Exception as e:
        print("❌ Size parse error:", e)
        return None


def clean_size_json(data):
    def clean(val):
        if val is None:
            return "N/A"
        if isinstance(val, str):
            # remove \n, \t and normalize spaces
            val = val.replace("\n", " ").replace("\t", " ")
            val = " ".join(val.split())  # removes extra spaces
            if val == "":
                return "N/A"
        return val
    for block in data:
        if not isinstance(block, dict):
            continue
        for row in block.get("row", []):
            for key in row:
                row[key] = clean(row[key])
    return data


def convert_to_row_format(size_dict, unit="inch"):
    rows = []
    for size, values in size_dict.items():
        row = {"Size": clean_text(size)}
        for key, val in values.items():
            row[clean_text(key)] = clean_text(val)
        rows.append(row)
    return [{"row": rows}]


# =========================
# REVIEWS
# =========================
def fetch_reviews_data(headers, product_id, hash_id, master_class):
    file_path = os.path.join(db.REVIEW_PAGESAVE, f"{hash_id}_review.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        url = f"https://api.urbanoutfitters.com/api/review/v0/uo-us/products/{product_id}/reviews"
        params = {
            "merchandise-class": master_class,
            # "merchandise-class": '0147',
            "offset": 0,
            "limit": 50,
            "filter": "",
            "sort": "submissionTime:desc"
        }
        response = requests.get(url, headers=headers, params=params)
        print("_________________________________________________________________________________")
        print(response.url)
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            return None
        if response.status_code == 200:
            data = response.json()
            # print(data)
            # # check result list
            # if data.get("result"):  # only true if result is not []
            #     with open(file_path, "w", encoding="utf-8") as f:
            #         json.dump(data, f, indent=4, ensure_ascii=False)
            #     print("File saved")
            # else:
            #     print("result is empty, file not saved")
            # save first page (optional)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
    return extract_review_data(data)


def extract_review_data(data):
    # try:
    #     reviews = []
    #     for r in data.get("results", []):
    #         date = None
    #         if r.get("lastModificationTime"):
    #             try:
    #                 date = datetime.fromisoformat(
    #                     r["lastModificationTime"]
    #                 ).strftime("%Y-%m-%d")
    #             except:
    #                 pass
    #
    #         reviews.append({
    #             "review_name": r.get("userNickname"),
    #             "review_title": r.get("title"),
    #             "review_content": r.get("reviewText"),
    #             "rating": r.get("rating"),
    #             "review_date": date,
    #             "verified": r.get("verified", False)
    #         })
    #     return {"reviews": reviews}
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
        if reviews == []:
            return  None
        else:
            return {"reviews": reviews}
    except Exception as e:
        print("❌ Review parse error:", e)
        return None


# =========================
# WORKER
# =========================
# def process_product(url, auth_token, headers, hash_id):
# # def process_product(url, hash_id):
#     result = extract_size_slug_data(url, hash_id)
#     if not result:
#         return
#     size_slug, hash_id, product_id = result
#     print(f"🚀 Processing: {url}")
#     try:
#         if size_slug:
#             fetch_size_chart(size_slug, auth_token, hash_id)
#             # fetch_size_chart(size_slug, hash_id)
#     except Exception as e:
#         print("❌ Size error:", e)
#     try:
#         if product_id:
#             reviews = fetch_reviews_data(headers, product_id, hash_id)
#             # reviews = fetch_reviews_data(product_id)
#             print(json.dumps(reviews))
#     except Exception as e:
#         print("❌ Review error:", e)


# =========================
# MAIN
# =========================

def process_product(url, auth_token, headers, hash_id):
    result = extract_size_slug_data(url, hash_id)
    print("result ::: ", result)
    if not result:
        return None
    master_class, hash_id, product_id = result
    # print(f"🚀 Processing: {url}")
    # size_data = None
    # review_data = None
    # try:
    #     if size_slug:
    #         size_data = fetch_size_chart(size_slug, auth_token, hash_id)
    # except Exception as e:
    #     print("❌ Size error:", e)
    try:
        if product_id:
            review_data = fetch_reviews_data(headers, product_id, hash_id, master_class)
    except Exception as e:
        print("❌ Review error:", e)
    return {
        "hash_id": hash_id,
        # "size_chart": size_data,
        "review_text": json.dumps(review_data, ensure_ascii=False) if review_data else None
    }

# def update_products_in_db(conn, results):
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
#
#             values = [
#                 (
#                     r["size_chart"],
#                     r["review_text"],
#                     r["hash_id"]
#                 )
#                 for r in results
#             ]
#
#             cursor.executemany(query, values)
#
#         conn.commit()
#
#         print(f"✅ Bulk updated {len(results)} rows")
#
#     except Exception as e:
#         print("❌ DB bulk update error:", e)

def update_product_in_db(conn, data):
    if data is None:
        return
    try:
        with conn.cursor() as cursor:
            query = f"""
                UPDATE {db.data_table}
                SET
                    review_text = %s,
                    status_review = 'done'
                WHERE hash_id = %s
            """
            cursor.execute(query, (
                data["review_text"],
                data["hash_id"]
            ))
        conn.commit()
        print(f"✅ Updated DB for {data['hash_id']}")
    except Exception as e:
        print("❌ DB update error:", e)

def main(rows):
    # auth_token = ht.get_urban_outfitters_token()
    # auth_data = ht.get_urban_outfitters_token()
    data = ht.get_urban_outfitters_token()
    headers = data["headers"]
    print(headers)
    datadome_id = headers.get("x-datadome-clientid")
    data_center_id = headers.get("x-urbn-primary-data-center-id")
    # if you want token separately
    auth_token = data["token"]
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
    conn = db.get_db_connection(db.db_name)
    # for r in rows:
        # process_product(r['link_url'], auth_token, headers, r['hash_id'])
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [
            executor.submit(process_product, r['link_url'], auth_token, headers, r['hash_id'])
            for r in rows
        ]
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    update_product_in_db(conn, result)
            except Exception as e:
                print("❌ Thread error:", e)
        # results_to_update = []
        # for future in as_completed(futures):
        #     try:
        #         result = future.result()
        #         if result:
        #             results_to_update.append(result)
        #     except Exception as e:
        #         print("❌ Thread error:", e)
        # # bulk update once
        # if results_to_update:
        #     update_products_in_db(conn, results_to_update)
    conn.close()

    # with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    #     futures = [
    #         executor.submit(process_product, r['link_url'], auth_token, headers, r['hash_id'])
    #         # executor.submit(process_product, r['link_url'], r['hash_id'])
    #         for r in rows
    #     ]
    #     for future in as_completed(futures):
    #         try:
    #             future.result()
    #         except Exception as e:
    #             print("❌ Thread error:", e)


# =========================
# ENTRY
# =========================
if __name__ == '__main__':
    # PROXY_FILE = r"D:\Julee\CODE\URBAN_OUTFITTERS\iproyal-proxies.txt"
    # PROXIES = load_proxies(PROXY_FILE)
    # print("Loaded proxies:", len(PROXIES))
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(f"""
    SELECT t.*
    FROM {db.data_table} t
    JOIN (
        SELECT hash_id, MAX(id) AS max_id
        FROM {db.data_table}
        WHERE status_review = 'pending' AND num_ratings IS NOT NULL
        GROUP BY hash_id
    ) x ON t.id = x.max_id
    limit 10
    """)
    # cur.execute(f"SELECT  DISTINCT pid, hash_id FROM {db.data_table} WHERE num_ratings IS NOT NULL AND status_review='pending'")
    # cur.execute(f"SELECT  * FROM {db.data_table} WHERE hash_id ='933488236744' ")
    rows = cur.fetchall()
    main(rows)
    cur.close()
    conn.close()