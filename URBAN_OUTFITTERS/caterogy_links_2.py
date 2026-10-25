import os.path
from curl_cffi import requests
import db_config_1 as db
from parsel import Selector
import json
import header_token as h



def fetch_main_category():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Referer': 'https://www.urbanoutfitters.com',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'sec-ch-device-memory': '8',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Chromium";v="142.0.7444.163", "Google Chrome";v="142.0.7444.163", "Not_A Brand";v="99.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
    }

    cat_file_path = f"{db.CAT_LINK_PAGESAVE}\\main_category.html"
    if os.path.exists(cat_file_path):
        with open(cat_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        response = requests.get('https://www.urbanoutfitters.com/',headers=headers)
        if response.status_code == 200:
            html_content = response.text
            with open(cat_file_path, "w", encoding='utf-8') as f:
                f.write(html_content)
    try:
        sel = Selector(text=html_content)
    except Exception as e:
        print(f"[ERROR] Failed to create Selector → {e}")
        return []
    # ---- Extract JSON-LD ----
    try:
        json_ld_raw = sel.xpath("//script[@type='application/ld+json']/text()").get()
        if not json_ld_raw:
            raise ValueError("JSON-LD <script> not found")
    except Exception as e:
        print(f"[ERROR] Failed to extract JSON-LD → {e}")
        return []
    # ---- Parse JSON ----
    try:
        data = json.loads(json_ld_raw)
        if not isinstance(data, list) or len(data) < 2:
            raise ValueError("Unexpected JSON-LD structure")
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON-LD → {e}")
        return []
    # ---- Extract navigation block ----
    try:
        nav_items = data[1].get("IsPartOf", [])
        if not nav_items:
            raise ValueError("Navigation items missing in JSON")
    except Exception as e:
        print(f"[ERROR] Failed to extract main navigation block → {e}")
        return []
    # ---- Extract main categories ----
    TARGETS = ["Women", "Men", "Accessories", "Beauty"]
    main_categories = []
    for item in nav_items:
        try:
            name = item.get("name", "").strip()
            url = item.get("url")
            if not name or not url:
                raise ValueError(f"Missing 'name' or 'url' in item: {item}")
            if any(name.lower().startswith(t.lower()) for t in TARGETS):
                slug = url.rstrip("/").split("/")[-1]
                main_categories.append({
                    "name": name,
                    "url": url,
                    "slug": slug
                })
        except Exception as e:
            print(f"[ERROR] Failed to extract a category item → {e}")
            continue
    print("main_categories ::: \n", main_categories)
    return main_categories


def fetch_category(categories):
    base_url = "https://api.urbanoutfitters.com/api/catalog/v0/uo-us/navigation"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'authorization': h.get_urban_outfitters_token()['token'],
        'origin': 'https://www.urbanoutfitters.com',
        'priority': 'u=1, i',
        'referer': 'https://www.urbanoutfitters.com/',
        'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        'x-datadome-clientid': '9uosykuSez82A4xvZlqAJLXqKZ9iJBDscwiHiBai1F3EvtXMSApnis2hkxLl5BWeZ5uRWtE08urFAbrFKkWJBClHtS~5NhZyCPqe9hl3bol4gsC90x9zz~a8FrqiHsSm',
        'x-urbn-channel': 'web',
        'x-urbn-country': 'IN',
        'x-urbn-currency': 'USD',
        'x-urbn-experience': 'ss',
        'x-urbn-geo-region': 'AS-SG',
        'x-urbn-language': 'en-US',
        'x-urbn-primary-data-center-id': 'US-NV',
        'x-urbn-site-id': 'uo-us',
        # 'cookie': '***HIDDEN***',
    }

    cookies = {
        'utag_main__sn': '45',
        'utag_main_ses_id': '1778732077832%3Bexp-session',
        'SSSC': '***HIDDEN***',
        'utag_main_dc_region': 'ap-east-1%3Bexp-session',
        '__attentive_session_id': '***HIDDEN***',
        'ss-enable-multi-label-returns': 'true',
        'SS_PLP_PERSONALIZATION': '3',
        'ss-enable-401-reauth-modal': '1',
        'SS_SEARCH_TEST': 'womens-new-arrivals_A',
        'SSLB': '1',
        'utag_main__ss': '0%3Bexp-session',
        '_pxvid': '***HIDDEN***',
        'utag_main_isLoggedIn': 'false%3Bexp-session',
        'utag_main_v_id': '***HIDDEN***',
        'utag_main_dc_visit': 'undefined',
        '_fbp': 'fb.1.1778733389743.590532045229385853.Bg',
        '_ga': 'GA1.1.620004048.1778733390',
        'rbuid': 'rbos-800b632a-4a83-4f88-8161-9e73192f606c',
        '_tt_enable_cookie': '1',
        '_ttp': '01KRJCB6YRSAXR7B1A67E3JM8M_.tt.1',
        'smartDash': '3a944b0f-75cc-41fc-a99f-8a189205da99',
        '_li_dcdm_c': '.urbanoutfitters.com',
        '_lc2_fpi': '18c6eee2a756--01krjcb709wcjhn0k7qs13pbtx',
        '_lc2_fpi_js': '18c6eee2a756--01krjcb709wcjhn0k7qs13pbtx',
        '__adroll_fpc': '***HIDDEN***',
        '__attentive_id': '***HIDDEN***',
        '_attn_': '***HIDDEN***',
        '__attentive_cco': '1778733390999',
        '__attentive_ss_referrer': 'ORGANIC',
        '_pin_unauth': 'dWlkPU9XUXlNMll5WlRndE9XUTVNeTAwTmpKaUxXSm1NR010WkRaa1kyVTRNR0k0TUdWaQ',
        'cebs': '1',
        'smartDashLRX': '008',
        '__attentive_dv': '1',
        '_svsid': '***HIDDEN***',
        '_ce.clock_data': '***HIDDEN***',
        'utag_main_tag_session_256': '1%3Bexp-session',
        '_scid': 'cvrISxuIyTxYW3kY5L8NNVSPhM6am6j7r6caWw',
        'utag_main_ttd_uuid': '7dfd94e8-427e-4856-bea5-007797578a0a%3Bexp-session',
        'utag_main_cms_256': '1%3Bexp-session',
        '_sctr': '1%7C1778697000000',
        'urbn_geo_region': 'AS-SG',
        'urbn_tracer': 'NMNLCZUX5O',
        'urbn_data_center_id': 'US-NV',
        'BVBRANDID': '574940e3-5f25-405f-8aff-19bb12a7dec6',
        'SSID': '***HIDDEN***',
        'utag_main_dc_event': '19%3Bexp-session',
        '_uetsid': '***HIDDEN***',
        '_uetvid': '***HIDDEN***',
        'mp_urbn_urbanoutfitters_na_mixpanel': '%7B%22distinct_id%22%3A%20%2219e24c597d0295-0c0cd5888fa6c48-26061151-e1000-19e24c597d1ef2%22%2C%22bc_persist_updated%22%3A%201778733389778%7D',
        '_ce.s': '***HIDDEN***',
        'cebsp_': '110',
        '_rdt_uuid': '1778733390735.4fc56b0e-4221-4362-b9dd-16207c77267a',
        '_scid_r': 'a_rISxuIyTxYW3kY5L8NNVSPhM6am6j7r6caYw',
        'ttcsid_CC2K5NJC77U26CFATFP0': '1778732226999::ZW7Y3aivq6OBlL_0FIdV.58.1778733788586.1',
        '_gcl_au': '1.1.612694491.1775032009.1247414111.1778732222.1778733797',
        'utag_main__pn': '26%3Bexp-session',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Thu+May+14+2026+10%3A13%3A19+GMT%2B0530+(India+Standard+Time)&version=202403.1.0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&consentId=af184042-6c60-4e50-895b-010cd13ebefc&interactionCount=0&isAnonUser=1&landingPath=https%3A%2F%2Fwww.urbanoutfitters.com%2Fshop%2Fuo-cher-mid-rise-mini-skort3%3Fcolor%3D041%26searchparams%3Dq%3DUO%252520Cher%252520Mid-Rise%252520Mini%252520Skort%26type%3DREGULAR%26quantity%3D1%26reviewPage%3D1%26reviewFilter%3D%26reviewSort%3DsubmissionTime%3Adesc&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1',
        '__attentive_pv': '27',
        'SSRT': '***HIDDEN***',
        '_clck': 'v84tli%5E2%5Eg61%5E1%5E2325',
        '_clsk': '1bmof98%5E1778733868044%5E1%5E1%5Ez.clarity.ms%2Fcollect',
        'ttcsid': '1778732074499::ue00j8KXzTSV6yb1zj4x.59.1778733327106.0::1.1229570.1249542::923057.2.785.572::1795961.104.2108',
        '_pxhd': '***HIDDEN***',
        'urbn_auth_payload': '***HIDDEN***',
        'datadome': '***HIDDEN***',
        'utag_main__se': '53%3Bexp-session',
        'utag_main__st': '1778736353325%3Bexp-session',
        '_ga_BBMWPLK0E5': 'GS2.1.s1778733389$o1$g1$t1778734553$j60$l0$h0',
    }
    results = []
    for cat in categories:
        slug = cat["slug"]
        print(f"Fetching subcategories for: {cat['name']} ({slug})")
        params = {
            "slug": slug,
            "projection-slug": "left-nav-l1",
        }
        sub_cat_file_path = f"{db.CAT_LINK_PAGESAVE}\\{slug}.json"
        if os.path.exists(sub_cat_file_path):
            with open(sub_cat_file_path, "r", encoding='utf-8') as f:
                data = json.loads(f.read())
        else:
            r = requests.get(base_url, params=params, headers=headers,cookies=cookies, impersonate='chrome110')
            if r.status_code != 200:
                print(f"Failed to fetch: {slug}")
                continue
            if r.status_code == 200:
                data = r.json()
                with open(sub_cat_file_path, "w", encoding='utf-8') as f:
                    f.write(r.text)
        if not data:
            return None
        items = data.get("navigationItems", [])
        for block in items:
            try:
                block_name = block.get("displayName", "").strip()
                block_slug = block.get("slug", "")
                if not block_slug:
                    raise ValueError(f"Missing slug for block: {block_name}")
                block_url = f"https://www.urbanoutfitters.com/{block_slug}"
                results.append({
                    "displayName": block_name,
                    "slug": block_slug,
                    "url": block_url,
                    "type": "main"
                })
                for sub in block.get("navigationItems", []):
                    try:
                        sub_name = (sub.get("displayName") or "").strip()
                        sub_slug = sub.get("slug", "")
                        if not sub_slug:
                            raise ValueError(f"Missing slug for subcategory under '{block_name}'")
                        if sub.get("typeCode") == "EXTERNAL":
                            url = sub.get("targetUrl")
                        else:
                            url = f"https://www.urbanoutfitters.com/{sub_slug}"
                        if not url.startswith("http"):
                            url = "https://www.urbanoutfitters.com" + url
                        results.append({
                            "displayName": sub_name,
                            "slug": sub_slug,
                            "url": url,
                            "type": "sub"
                        })
                    except Exception as e:
                        print(f"[ERROR: SUBCATEGORY] Block='{block_name}' Sub='{sub.get('displayName')}' → {e}")
                        continue
            except Exception as e:
                print(f"[ERROR: MAIN BLOCK] Block='{block.get('displayName')}' → {e}")
                continue
    return results


def insert_links(clean_data):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    sql = f"""
    INSERT IGNORE INTO `{db.cat_links_table}` (url, displayname, slug, type, status)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        displayname = VALUES(displayname),
        slug = VALUES(slug),
        type = VALUES(type)
    """
    count = 0
    for item in clean_data:
        values = (
            item["url"],
            item["displayName"],
            item["slug"],
            item["type"],
            "pending"
        )
        try:
            cursor.execute(sql, values)
            count += 1
        except Exception as e:
            print("Duplicate or error:", item["url"], "|", e)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted/Updated: {count} rows")

if __name__ == "__main__":
    main_categories = fetch_main_category()
    all_categories = fetch_category(main_categories)
    insert_links(all_categories)