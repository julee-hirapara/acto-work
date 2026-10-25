import gzip
import sys
from urllib.parse import urlparse
import pymysql
import requests
from parsel import Selector
import json
import re
import db_config_1 as db
import os
import header_token as ht
from concurrent.futures import ThreadPoolExecutor

def without_class_head_list_structure(table):
    pivoted_data = {}
    headers = table.xpath("//thead//th//text()").getall()
    all_raw = []
    for raw in table.xpath("//tbody//tr"):
        values = raw.xpath(".//td//text()").getall()
        if values:
            all_raw.append(values)
    merged_data = [dict(zip(headers, row)) for row in all_raw]
    headers = merged_data[0].keys()
    pivoted_data = {
        header: re.sub(r'\s+', " ", " | ".join(row[header] for row in merged_data if header in row)).strip()
        for header in headers
    }
    return pivoted_data

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
        item[raw.xpath(".//th//text()").get("unknow")] = " | ".join(item[raw.xpath(".//th//text()").get("unknow")]).strip(" | ")
    return item

def key_value_structure(table):
    th_class = table.xpath("//thead//th[@class]").getall()
    td_class = table.xpath("//thead//td[@class]").getall()
    if not th_class or td_class:
        return without_class_head_list_structure(table)
    all_list = []
    item = {}
    headers = table.xpath("//thead//th//text()").getall()
    if headers:
        all_list.append(headers)
    for tr in table.xpath("//tr"):
        values = tr.xpath(".//td//text()").getall()
        if values:
            all_list.append(values)
    if all_list:
        for lt in all_list:
            item[lt[0]] = re.sub(r'\s+', ' ', " | ".join(lt[1:]).strip(" | ")).strip()
    return item

def extract_table(table):
    html_ele = {}
    for header in table.xpath("//thead//tr//*"):
        key = str(header)
        if key.startswith("<th"):
            html_ele['th'] = html_ele.get("th", 0)
            html_ele['th']+=1
        elif key.startswith("<td"):
            html_ele['td'] = html_ele.get("td", 0)
            html_ele['td']+=1
        elif key.startswith("<tr"):
            html_ele['tr'] = html_ele.get("tr", 0)
            html_ele['tr']+=1
    if "th" in list(html_ele.keys()) and "td" in list(html_ele.keys()):
        table_data = parse_head_list_structure(table)
    else:
        table_data = key_value_structure(table)
    return table_data

def safe_json_load(data):
    try:
        while isinstance(data, str):
            data = json.loads(data)
    except:
        pass
    return data

def extract_size_slug_data(url, hash_id):
    # hash_id = url_to_id(url)
    file_path = f"{db.DATA_PAGESAVE}\\{hash_id}.html.gz"
    if not os.path.exists(file_path):
        print(f"❌ Missing file: {file_path}")
        return None
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        html_content = f.read()
    sel = Selector(text=html_content)
    size_guide_available_not = sel.xpath("//button[contains(@class, 'pwa-size-guide-link')]").get()
    if not size_guide_available_not:
        print("size guide not available on this page....")
        return None
    state_block = sel.xpath('//script[@id="urbnInitialPiniaState"]/text()').get()
    if not state_block:
        print("❌ No state block")
        return None
    data = safe_json_load(state_block)
    products = data.get("catalog", {}).get("products", {})
    slug = urlparse(url).path.split("/")[-1]
    product_root = products.get(slug) or next(iter(products.values()), {})
    if not product_root:
        print("❌ product_root missing")
        return None
    product_data = product_root.get("product", {})
    return product_data.get("sizeGuide")


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
    data = response.json()
    with open("token_data.json", "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    auth_token = data.get("reauthToken")
    return auth_token


def fetch_size_chart(url, hash_id=None):
    # size_guide_slug = extract_size_slug_data(url, hash_id)
    # if not size_guide_slug:
    #     return None
    file_path = os.path.join(db.SIZE_PAGESAVE, f"{hash_id}_size_chart.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f" --------  {hash_id} ")
            return data
#     else:
#         cookies = {
#     'SSLB': '1',
#     'urbn_data_center_id': 'US-PA',
#     'urbn_geo_region': 'US-PA',
#     'urbn_tracer': 'LEXQESYA6S',
#     '_pxvid': '***HIDDEN***',
#     '_ga': 'GA1.1.58757530.1778768579',
#     'BVBRANDID': '0b568e23-df74-4694-aebf-5de3e7c813ed',
#     '__attentive_id': '***HIDDEN***',
#     '_attn_': '***HIDDEN***',
#     '__attentive_cco': '1778768580831',
#     '__attentive_dv': '1',
#     'utag_main_v_id': '***HIDDEN***',
#     '_fbp': 'fb.1.1778768641136.570164475862948537.Bg',
#     '_tt_enable_cookie': '1',
#     '_ttp': '01KRKDYZDZ9PHJ3HJ1164Y167E_.tt.1',
#     'rbuid': 'rbos-ef6b1c75-e300-4e79-9d28-aa81226efc07',
#     'smartDash': '76732e54-c0f9-4228-8774-a992462b4991',
#     '_lc2_fpi': '18c6eee2a756--01krkdyzvcm0t23bm5wpbq9c8c',
#     '_pin_unauth': 'dWlkPU9EbGhPRE0xTldFdE1qQXpOQzAwWkdRekxXRTJZVGN0Wm1JM01qWTRaR1ppWmpreA',
#     '__adroll_fpc': '***HIDDEN***',
#     '_scid': 'oYYPhl7nyqhHTQq3wqa7pXcbywujvLhOjZ7IDQ',
#     'smartDashLRX': '000',
#     '_svsid': '***HIDDEN***',
#     '_ce.clock_data': '***HIDDEN***',
#     '_sctr': '1%7C1778697000000',
#     'ss-enable-401-reauth-modal': '1',
#     'SS_PLP_PERSONALIZATION': '3',
#     'SS_SEARCH_TEST': 'womens-new-arrivals_B',
#     'ss-enable-multi-label-returns': 'true',
#     'ss-enable-password-cvc-recollection': 'true',
#     'SSSC': '***HIDDEN***',
#     'SSRT': '***HIDDEN***',
#     'urbn_auth_payload': '***HIDDEN***',
#     '_px3': '***HIDDEN***',
#     '_pxhd': '***HIDDEN***',
#     'utag_main__sn': '22',
#     'utag_main_ses_id': '1778826327234%3Bexp-session',
#     'utag_main__pn': '1%3Bexp-session',
#     'OptanonConsent': 'isGpcEnabled=0&datestamp=Fri+May+15+2026+11%3A55%3A27+GMT%2B0530+(India+Standard+Time)&version=202403.1.0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&consentId=862c50b4-7c73-4147-964d-c2093e0b08a0&interactionCount=0&isAnonUser=1&landingPath=https%3A%2F%2Fwww.urbanoutfitters.com%2F&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1',
#     'utag_main_isLoggedIn': 'false%3Bexp-session',
#     'utag_main_tag_session_256': '1%3Bexp-session',
#     'utag_main_dc_visit': '20',
#     'utag_main__ss': '0%3Bexp-session',
#     'utag_main_dc_region': 'us-east-1%3Bexp-session',
#     '_rdt_uuid': '1778768641804.7de87ece-7d4e-4027-b11f-95dfdc93bf3b',
#     'mp_urbn_urbanoutfitters_na_mixpanel': '%7B%22distinct_id%22%3A%20%2219e26df7b92b49-00b09860d9a5d78-26061151-1fa400-19e26df7b93a81%22%2C%22bc_persist_updated%22%3A%201778768640916%7D',
#     'SSID': '***HIDDEN***',
#     '_scid_r': 'tYYPhl7nyqhHTQq3wqa7pXcbywujvLhOjZ7IAQ',
#     '_clck': 'x0lnv7%5E2%5Eg62%5E1%5E2326',
#     '__attentive_session_id': '***HIDDEN***',
#     'cebs': '1',
#     '_ce.s': '***HIDDEN***',
#     '_li_dcdm_c': '.urbanoutfitters.com',
#     '_lc2_fpi_js': '18c6eee2a756--01krkdyzvcm0t23bm5wpbq9c8c',
#     '_uetsid': '***HIDDEN***',
#     '_uetvid': '***HIDDEN***',
#     '_gcl_au': '1.1.1347756862.1775039388.46296892.1778826337.1778826339',
#     'utag_main_dc_event': '3%3Bexp-session',
#     'cebsp_': '2',
#     '_clsk': '1a4sim9%5E1778826340540%5E1%5E0%5Ep.clarity.ms%2Fcollect',
#     '__attentive_pv': '1',
#     '__attentive_ss_referrer': 'ORGANIC',
#     'utag_main_ttd_uuid': '07e93b19-c2e5-402f-82bc-7418a62d7572%3Bexp-session',
#     'utag_main_cms_256': '1%3Bexp-session',
#     'datadome': '***HIDDEN***',
#     'BVBRANDSID': '1ecd1d29-82e9-48e6-b967-8bc57c4442f6',
#     'ttcsid': '1778826333491::gT1-cUpkwOuIcxD7OMkt.31.1778826351427.0::1.-12370.0::17925.2.784.629::7241.12.495',
#     'ttcsid_CC2K5NJC77U26CFATFP0': '1778826333489::u-f4GOEsyIup2GZiKy4A.21.1778826351427.1',
#     'utag_main__se': '8%3Bexp-session',
#     'utag_main__st': '1778828151441%3Bexp-session',
#     '_ga_BBMWPLK0E5': 'GS2.1.s1778826334$o3$g1$t1778826351$j43$l0$h0',
# }
#
#
#
#
        # # Try multiple payloads
        # payloads = [
        #     {
        #         'include': '4',
        #         'contentfulEnvironment': 'master',
        #         'content_type': 'sizeGuideConfiguration',
        #         'fields.slug': size_guide_slug,
        #     },
        #     {
        #         'include': '1',
        #         'contentfulEnvironment': 'master',
        #         'content_type': 'sizeGuideVendor',
        #         'fields.slug': size_guide_slug,
        #     }
        # ]
        #
        # data = None
        # for params in payloads:
        #     response = requests.get(
        #         'https://api.urbanoutfitters.com/api/content/v1/uo-us/entries',
        #         headers=HEADERS,
        #         params=params,
        #         cookies=cookies
        #     )
        #     if response.status_code == 200:
        #         temp_data = response.json()
        #         if temp_data.get("items"):
        #             data = temp_data
        #             with open(file_path, "w", encoding="utf-8") as f:
        #                 json.dump(data, f, indent=4)
        #             print("✅ Size chart found")
        #             break
        # if not data:
        #     return None
        # else:
        #     return data

def main(record):

    print("Fetching :", record['hash_id'])
    extracted_data = {}
    data = fetch_size_chart(url=record['main_url'], hash_id=record['hash_id'])
    if not data:
        return None
    try:
        for raw in data['items']:
            for raw_2 in raw['guides']:
                if "inchesTables" in (raw_2.keys()):
                    for raw_3 in raw_2['inchesTables']:
                        table = raw_3['tableHtml']
                        table = Selector(table)
                        extracted_data['inches'] = extract_table(table)
                if "centimetersTables" in (raw_2.keys()):
                    for raw_3 in raw_2['centimetersTables']:
                        table = raw_3['tableHtml']
                        table = Selector(table)
                        extracted_data['centimeters'] = extract_table(table)
    except Exception as e:
        e = str(e)
        if 'guides' in e:
            counter = 1
            for raw in data['items']:
                for raw_2 in raw['tables']:
                    extracted_data[f"default_{counter}"] = extract_table(Selector(raw_2['tableHtml']))
                    counter += 1
        else:
            print(e)
    if not extracted_data:
        return None
    with db.get_db_connection(db.db_name) as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(f"update {db.data_table} set size_chart=%s, status_size='done' where hash_id=%s",
                        (json.dumps(extracted_data), record['hash_id']))
            conn.commit()
            print("Inserted: ", record['hash_id'])

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    data = ht.get_urban_outfitters_token()
    headers = data["headers"]
    datadome_id = headers.get("x-datadome-clientid")
    data_center_id = headers.get("x-urbn-primary-data-center-id")
    # if you want token separately
    auth_token = data["token"]

    HEADERS = {
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
            cur.execute(f"SELECT  DISTINCT main_url, hash_id FROM {db.data_table} WHERE status_size='pending' LIMIT 10")
            # cur.execute(f"SELECT  DISTINCT pid, hash_id FROM {db.data_table} WHERE pid='UO-57537995-000'")
            records = cur.fetchall()
    with ThreadPoolExecutor(max_workers=1) as f:
        f.map(main, records)
