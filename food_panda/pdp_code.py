import hashlib
import os
import time
from os import times

import pandas as pd
import tls_client

import db_config_1 as db
import pymysql
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests
import random
from parsel import Selector
import re
import json
from datetime import datetime
proxy = {
   "http": f'http://***HIDDEN***:super=false@proxy.scrape.do:8080',
   "https": f'http://***HIDDEN***:super=false@proxy.scrape.do:8080',
}
# api_key = '***HIDDEN***'


# #  LOAD PROXIES FROM FILE
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


def insert_master_data(vendor_info, menu_rows):
    # if not vendor_info or not menu_rows:
    #     return
    if not vendor_info:
        return
    if not menu_rows:
        menu_rows = [{
            "category_name": None,
            "menu_name": None,
            "discounted_price": None,
            "regular_price": None,
            "menu_image": None,
            "description": None,
            "tags": None,
            "item_code": None,
            "delivery_date": None
        }]
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    insert_query = f"""
        INSERT IGNORE INTO {db.data_table} (
            url,
            restaurant_name,
            restaurant_image,
            cuisines,
            currency,
            country_code,
            opening_hours,
            phone_number,
            address,
            post_code,
            city,
            latitude,
            longitude,
            rating,
            rating_count,
            brand,
            minimum_order_value,
            category_name,
            menu_name,
            price,
            mrp,
            discount,
            menu_image,
            description,
            tags,
            extra_data,
            scraped_date,
            scraped_time
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
    """
    values = []
    for item in menu_rows:
        price = item.get("discounted_price") or 0
        mrp = item.get("regular_price") or price
        try:
            discount = round(float(mrp) - float(price), 2)
        except:
            discount = 0
        extra_data = {
            "vendor_id": vendor_info.get("vendor_id"),
            "item_code": item.get("item_code"),
            "delivery_date": item.get("delivery_date"),
            "platform": vendor_info.get("platform"),
            "delivery_details": vendor_info.get("delivery_details")
        }
        row = (
            vendor_info.get("url"),
            vendor_info.get("vendor_name"),
            vendor_info.get("vendor_image"),
            vendor_info.get("cuisine"),
            "RM",
            vendor_info.get("country_code"),
            vendor_info.get("opening_hours"),
            vendor_info.get("phone_number"),
            vendor_info.get("address"),
            vendor_info.get("post_code"),
            vendor_info.get("city"),
            vendor_info.get("latitude"),
            vendor_info.get("longitude"),
            vendor_info.get("rating"),
            vendor_info.get("rating_count"),
            vendor_info.get("brand"),
            vendor_info.get("minimum_order_value"),
            item.get("category_name"),
            item.get("menu_name"),
            price,
            mrp,
            discount,
            item.get("menu_image"),
            item.get("description"),
            item.get("tags"),
            json.dumps(extra_data, ensure_ascii=False),
            vendor_info.get("scraped_date"),
            vendor_info.get("scraped_time")
        )
        values.append(row)
    if values:
        cursor.executemany(insert_query, values)
        conn.commit()
        print(f"✅ Inserted rows: {cursor.rowcount}")
    cursor.close()
    conn.close()


# def get_random_proxy():
#     if not PROXIES:
#         return None
#     proxy = random.choice(PROXIES)
#     return {
#         "http": proxy,
#         "https": proxy
#     }


IMPERSONATE_LIST = [
    "chrome99",
    "chrome110",
    "edge99",
    "safari15_3",
    "chrome120"
]
random.choice(IMPERSONATE_LIST)

def extract_lat_lang(html_text):
    sel = Selector(text=html_text)
    # ---------- SEO JSON ----------
    seo_raw = sel.xpath('//script[@type="application/ld+json"]/text()').get()
    seo = json.loads(seo_raw) if seo_raw else {}
    # =========================
    # EXTRACT SEO DATA
    # =========================
    latitude = seo.get("geo", {}).get("latitude")
    longitude = seo.get("geo", {}).get("longitude")
    return latitude, longitude



def extract_complete_foodpanda_data(api_json, html_text, hash_id):
    rows = []
    vendor_info = {}
    # =========================
    # PARSE HTML (XPath only)
    # =========================
    sel = Selector(text=html_text)
    # Get script content
    script_text = sel.xpath('//script[contains(text(),"__PRELOADED_STATE__")]/text()').get()
    main_vendor_id = None
    if script_text:
        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*\})',script_text,re.DOTALL)
        if match:
            raw_json = match.group(1)
            # FIX INVALID JAVASCRIPT VALUES
            raw_json = raw_json.replace(':undefined', ':null')
            try:
                data = json.loads(raw_json)
                vendor_data = data.get("vendor") or {}
                vendor_data = vendor_data.get("data") or {}
                chain_data = vendor_data.get("chain") or {}
                main_vendor_id = chain_data.get("main_vendor_id")
            except Exception as e:
                print("JSON error:", e)
                data = {}
        # # Extract JSON safely
        # match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*\})', script_text, re.DOTALL)
        # if match:
        #     raw_json = match.group(1)
        #     try:
        #         data = json.loads(raw_json)
        #         main_vendor_id = (
        #             data.get("vendor", {})
        #             .get("data", {})
        #             .get("chain", {})
        #             .get("main_vendor_id")
        #         )
        #     except Exception as e:
        #         print("JSON error:", e)
    print("main_vendor_id:", main_vendor_id)
    # ---------- SEO JSON ----------
    seo_raw = sel.xpath('//script[@type="application/ld+json"]/text()').get()
    seo = json.loads(seo_raw) if seo_raw else {}

    # ---------- PROVIDER PROPS ----------
    script_text = sel.xpath('//script[contains(text(),"__PROVIDER_PROPS__")]/text()').get()
    provider_data = {}

    if script_text:
        match = re.search(r'window\.__PROVIDER_PROPS__\s*=\s*(\{.*\})', script_text, re.DOTALL)
        if match:
            raw_json = match.group(1)
            # FIX invalid JS values
            raw_json = raw_json.replace(':undefined', ':null')
            try:
                provider_data = json.loads(raw_json)
            except Exception as e:
                print("Parse error:", e)
    print(provider_data.get("brand"))

    # =========================
    # EXTRACT SEO DATA
    # =========================

    url = seo.get("url")
    vendor_name = seo.get("name")
    phone = seo.get("telephone")
    latitude = seo.get("geo", {}).get("latitude")
    longitude = seo.get("geo", {}).get("longitude")
    address_data = seo.get("address", {})
    address = address_data.get("streetAddress", "N/A")
    post_code = address_data.get("postalCode", "N/A")
    city = address_data.get("addressLocality", "N/A")
    rating = seo.get("aggregateRating", {}).get("ratingValue")
    rating_count = seo.get("aggregateRating", {}).get("ratingCount")
    # cuisines = ", ".join(seo.get("servesCuisine", []))
    cuisines = ", ".join(seo.get("servesCuisine") or [])
    vendor_image = (seo.get("image") or [None])[0]

    # ---------- Opening Hours ----------
    opening_hours = {}
    for spec in (seo.get("openingHoursSpecification") or []):
        days = spec.get("dayOfWeek") or []
        if isinstance(days, str):
            days = [days]
        opens = spec.get("opens")
        closes = spec.get("closes")
        for d in days:
            opening_hours[str(d).lower()] = f"{opens}-{closes}"
    # opening_hours = {}
    # for spec in seo.get("openingHoursSpecification", []):
    #     days = spec.get("dayOfWeek", [])
    #     opens = spec.get("opens")
    #     closes = spec.get("closes")
    #     for d in days:
    #         opening_hours[d.lower()] = f"{opens}-{closes}"

    # =========================
    # PROVIDER PROPS DATA
    # =========================
    brand = provider_data.get("brand")
    country_code = provider_data.get("countryConfig")
    platform = provider_data.get("platform")

    # =========================
    # API DATA
    # =========================
    # d = api_json.get("data", {})
    d = (api_json or {}).get("data") or {}
    vendor_chain_id = (d.get("chain") or {}).get("main_vendor_id")
    review_count = d.get("review_number")
    try:
        # minimum_order_value = d.get("discounts", [])[0].get("minimum_order_value")
        discounts = d.get("discounts") or []
        if discounts and isinstance(discounts, list):
            minimum_order_value = discounts[0].get("minimum_order_value")
        else:
            minimum_order_value = None
    except:
        minimum_order_value = None
    delivery_details = d.get("delivery_provider")
    customer_phone = d.get("customer_phone")
    scraped_date = datetime.now().strftime("%Y-%m-%d")
    scraped_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    delivery_date = scraped_date

    # =========================
    # FINAL VENDOR INFO
    # =========================
    vendor_info = {
        "vendor_id": main_vendor_id,
        "url": url,
        "vendor_name": vendor_name,
        "cuisine": cuisines,
        "vendor_image": vendor_image,
        "vendor_description": None,

        "opening_hours": json.dumps(opening_hours),
        "phone_number": phone or customer_phone,
        "address": address,
        "post_code": post_code,
        "city": city,
        "latitude": latitude,
        "longitude": longitude,

        "rating": rating,
        "rating_count": rating_count or review_count,

        "brand": brand,
        "country_code": country_code,
        "platform": platform,

        "minimum_order_value": minimum_order_value,
        "delivery_details": delivery_details,
        "hash_id": hash_id,
        "scraped_date": scraped_date,
        "scraped_time": scraped_time,
        "delivery_date": delivery_date
    }
    # =========================
    # IF API FAILED
    # =========================
    if not api_json:
        row = {
            "vendor_id": vendor_info["vendor_id"],
            "url": vendor_info["url"],
            "category_name": None,
            "item_code": None,
            "menu_name": None,
            "regular_price": None,
            "discounted_price": None,
            "discount": None,
            "saved_price": None,
            "menu_image": None,
            "description": None,
            "tags": None,
            "scraped_date": scraped_date,
            "country_code": country_code,
            "delivery_date": delivery_date
        }

        rows.append(row)

        return vendor_info, rows
    # =========================
    # MENU EXTRACTION
    # =========================
    # menus = d.get("menus", [])
    # for menu in menus:
    #     for category in menu.get("menu_categories", []):
    #         category_name = category.get("name")
    #         for product in category.get("products", []):
    menus = d.get("menus") or []
    for menu in menus:
        categories = menu.get("menu_categories") or []
        for category in categories:
            category_name = category.get("name")
            products = category.get("products") or []
            for product in products:
                # ✅ SAFE TAG HANDLING
                tags_list = product.get("tags") or []
                # keep only useful tags (exclude system/internal ones)
                clean_tags = [t for t in tags_list if not t.startswith("system:")]
                # convert to string
                tags = ", ".join(clean_tags) if clean_tags else None
                menu_name = product.get("name")
                item_code = product.get("code")
                description = product.get("description")
                image = product.get("file_path")
                for var in (product.get("product_variations") or []):
                # for var in product.get("product_variations", []):
                    price = var.get("price") or 0

                    row = {
                        "vendor_id": vendor_info["vendor_id"],
                        "url": vendor_info["url"],
                        "category_name": category_name,
                        "item_code": item_code,
                        "menu_name": menu_name,
                        "regular_price": price,
                        "discounted_price": price,
                        "discount": 0,
                        "saved_price": 0,

                        "menu_image": image,
                        "description": description,
                        "tags": tags,

                        "scraped_date": scraped_date,
                        "country_code": country_code,
                        "delivery_date": delivery_date
                    }

                    rows.append(row)

    return vendor_info, rows


def generate_hash_id(url):
    hash_object = hashlib.md5(url.encode("utf-8"))
    hash_hex = hash_object.hexdigest()
    # Convert hex → integer
    hash_int = int(hash_hex, 16)
    # Keep only 12 digits
    hash_id = str(hash_int)[:12]
    return hash_id

def get_pdp_page(link, code, name):
    hash_id = generate_hash_id(link)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': link,
        'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    }
    try:
        print(f"🚀 Processing: {name} ({code}) || {hash_id}")
        # session = tls_client.Session(
        #     client_identifier="chrome_142",
        #     random_tls_extension_order=True
        # )
        # proxy = get_random_proxy()
        # print("Using Proxy:", proxy)

        # request_url = f'https://api.scraperapi.com?api_key={api_key}&url={link}'
        # html_res = requests.get(request_url)
        # ---------------- HTML ----------------
        folder_path = os.path.join(db.PDP_PAGESAVE, "html_pages")
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{hash_id}.html")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                html_text = f.read()
        else:
            time.sleep(6)
            html_res = requests.get(link,
                                    headers=headers,
                                    proxies = proxy,
                                    verify=False,
                                    timeout=600,
                                    # cookies=cookies,
                                    impersonate=random.choice(IMPERSONATE_LIST)
                                   )

            print(f"html_res ::{html_res} ")
            if html_res.status_code != 200:
                print("❌ HTML failed")
                return ("failed", code, link, None, [])

            html_text = html_res.text
            with open(file_path, "w", encoding='utf-8') as f:
                f.write(html_res.text)
        lat, long = extract_lat_lang(html_text)
        # ---------------- API ----------------
        api_url = f"https://my.fd-api.com/api/v5/vendors/{code}"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'api-version': '7',
            'authorization': '',
            'dps-session-id': '***HIDDEN***',
            'origin': 'https://www.foodpanda.my',
            'perseus-client-id': '1779089708061.278774752923091213.6ijfojp1et',
            'perseus-session-id': '1779109940599.854408966781338307.t25d2p70st',
            'priority': 'u=1, i',
            'referer': 'https://www.foodpanda.my/',
            'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
            'x-fp-api-key': 'volo',
            'x-pd-language-id': '1',
        }
        params = {
            "include": "menus,bundles,multiple_discounts",
            "language_id": "1",
            "opening_type": "delivery",
            "basket_currency": "MYR",
            # "latitude" : "3.1568055",
            # "longitude" : "101.7132345"
            # "latitude": str(lat),
            # # "latitude": "3.1568055",
            # "longitude": str(long)
        }

        folder_path = os.path.join(db.PDP_PAGESAVE, "json_pages")
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{hash_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                api_json = json.load(f)
        else:
            # from urllib.parse import urlencode
            #
            # base_api_url = f"https://my.fd-api.com/api/v5/vendors/{code}"
            # query_string = urlencode(params)
            #
            # full_api_url = f"{base_api_url}?{query_string}"
            # request_url = f'https://api.scraperapi.com?api_key={api_key}&url={full_api_url}'
            # api_res = requests.get(request_url)
            time.sleep(8)
            api_res = requests.get(
                api_url,
                headers=headers,
                params=params,
                proxies=proxy,
                verify=False,
                timeout=600,
                # impersonate=random.choice(IMPERSONATE_LIST)
            )
            print(f"api_res :: {api_res}")

            if api_res.status_code != 200:
                print("❌ API failed")
                return ("failed", code, link, None, [])

            api_json = api_res.json()
            with open(file_path, "w", encoding='utf-8') as f:
                json.dump(api_json, f, ensure_ascii=False, indent=4)
        # ---------------- EXTRACT ----------------
        if not api_json:
            vendor_info, menu_rows = extract_complete_foodpanda_data(
                api_json=None,
                html_text=html_text,
                hash_id=hash_id
            )
        else:
            vendor_info, menu_rows = extract_complete_foodpanda_data(
                api_json=api_json,
                html_text=html_text,
                hash_id=hash_id
            )

        # ---------------- SAVE ----------------
        # import pandas as pd
        #
        # pd.DataFrame([vendor_info]).to_excel(f"vendor_{code}.xlsx", index=False)
        # pd.DataFrame(menu_rows).to_excel(f"menu_{code}.xlsx", index=False)
        #
        # print(f"✅ Done: {code}")

        # return ("done", code, link)
        return ("done", code, link, vendor_info, menu_rows)
    except Exception as e:
        print(f"❌ Error in {code}: {e}")
        return ("error", code, link, None, [])

def process_product(row):
    try:
        link = row["link"]
        code = row["code"]
        name = row["name"]
        status, code, link, vendor_info, menu_rows = get_pdp_page(link, code, name)
        return (status, link, code, vendor_info, menu_rows)
    except Exception as e:
        print(f"❌ Error: {e}")
        return ("error", row["link"], row["code"], None, [])
    #     status, code, link = get_pdp_page(link, code, name)
    #     return (status, link, code)
    # except Exception as e:
    #     print(f"❌ Error: {e}")
    #     return ("error", rows["link"], rows["code"])

def clean_dataframe(df):
    # Fill NaN / None with "N/A"
    df = df.fillna("N/A")

    # Strip spaces + normalize multiple spaces
    for col in df.columns:
        if df[col].dtype == "object":  # only string columns
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()                     # remove leading/trailing
                .str.replace(r"\s+", " ", regex=True)  # remove extra spaces
            )

    return df

def main():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = f""" 
        SELECT * FROM {db.link_table} 
        WHERE status = 'failed'
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        print("No pending product found.")
        return
    # =========================
    # THREAD EXECUTION
    # =========================
    all_vendor_data = []
    all_menu_data = []
    db_updates = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        results = list(executor.map(process_product, rows))
    # =========================
    # PROCESS RESULTS
    # =========================
    # for result in results:
    #     status, link, code, vendor_info, menu_rows = result
    #     # ✅ DB update tuple (ONLY 3 VALUES)
    #     db_updates.append((status, link, code))
    #     # SAVE INTO DATABASE
    #     if vendor_info and menu_rows:
    #         insert_master_data(vendor_info, menu_rows)
    #     # collect vendor data
    #     if vendor_info:
    #         all_vendor_data.append(vendor_info)
    #     # collect menu data
    #     if menu_rows:
    #         all_menu_data.extend(menu_rows)
    #     # ✅ collect vendor data
    #     # if vendor_info:
    #     #     all_vendor_data.append(vendor_info)
    #     # # ✅ collect menu data
    #     # if menu_rows:
    #     #     all_menu_data.extend(menu_rows)
    for result in results:
        status, link, code, vendor_info, menu_rows = result
        try:
            # SAVE INTO DATABASE
            # if vendor_info and menu_rows:
            if vendor_info:
                insert_master_data(vendor_info, menu_rows)
                # UPDATE STATUS AFTER SUCCESS
                conn = db.get_db_connection(db.db_name)
                cursor = conn.cursor()
                update_query = f"""
                    UPDATE `{db.link_table}`
                    SET status = %s
                    WHERE link = %s AND code = %s
                """
                cursor.execute(update_query, ("done", link, code))
                conn.commit()
                cursor.close()
                conn.close()
                print(f"✅ Updated: {link}")
            else:
                conn = db.get_db_connection(db.db_name)
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                    UPDATE `{db.link_table}`
                    SET status = %s
                    WHERE link = %s AND code = %s
                    """,
                    ("failed", link, code)
                )
                conn.commit()
                cursor.close()
                conn.close()
        except Exception as e:
            print(f"❌ Error: {e}")
            conn = db.get_db_connection(db.db_name)
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE `{db.link_table}`
                SET status = %s
                WHERE link = %s AND code = %s
                """,
                ("failed", link, code)
            )
            conn.commit()
            cursor.close()
            conn.close()
        # collect vendor data
        if vendor_info:
            all_vendor_data.append(vendor_info)
        # collect menu data
        if menu_rows:
            all_menu_data.extend(menu_rows)
    # # =========================
    # # SAVE FILES (3 FILES)
    # # =========================
    # if all_vendor_data:
    #     df_vendor = pd.DataFrame(all_vendor_data)
    #     df_vendor = clean_dataframe(df_vendor)
    #
    #     with pd.ExcelWriter(
    #             "vendors_all.xlsx",
    #             engine="xlsxwriter",
    #             engine_kwargs={"options": {"strings_to_urls": False}}
    #     ) as writer:
    #         df_vendor.to_excel(writer, index=False)
    #
    # if all_menu_data:
    #     df_menu = pd.DataFrame(all_menu_data)
    #     df_menu = clean_dataframe(df_menu)
    #
    #     with pd.ExcelWriter(
    #             "menus_all.xlsx",
    #             engine="xlsxwriter",
    #             engine_kwargs={"options": {"strings_to_urls": False}}
    #     ) as writer:
    #         df_menu.to_excel(writer, index=False)
    #
    # if all_vendor_data and all_menu_data:
    #     df_merged = df_menu.merge(pd.DataFrame(all_vendor_data), on="vendor_id", how="left")
    #     df_merged = clean_dataframe(df_merged)
    #
    #     with pd.ExcelWriter(
    #             "merged_all.xlsx",
    #             engine="xlsxwriter",
    #             engine_kwargs={"options": {"strings_to_urls": False}}
    #     ) as writer:
    #         df_merged.to_excel(writer, index=False)
    # # if all_vendor_data:
    # #     df_vendor = pd.DataFrame(all_vendor_data)
    # #     df_vendor.to_excel("vendors_all.xlsx", index=False)
    # # if all_menu_data:
    # #     df_menu = pd.DataFrame(all_menu_data)
    # #     df_menu.to_excel("menus_all.xlsx", index=False)
    # # # ✅ MERGED FILE
    # # if all_vendor_data and all_menu_data:
    # #     df_vendor = pd.DataFrame(all_vendor_data)
    # #     df_menu = pd.DataFrame(all_menu_data)
    # #     df_merged = df_menu.merge(df_vendor, on="vendor_id", how="left")
    # #     df_merged.to_excel("merged_all.xlsx", index=False)
    # print("✅ Files saved")
    # # # =========================
    # # # DB UPDATE
    # # # =========================
    # # conn = db.get_db_connection(db.db_name)
    # # cursor = conn.cursor()
    # # update_query = f"""
    # #     UPDATE `{db.link_table}`
    # #     SET status = %s
    # #     WHERE link = %s AND code = %s
    # # """
    # # cursor.executemany(update_query, db_updates)
    # # conn.commit()
    # # cursor.close()
    # # conn.close()
    # # print("✅ DB updated")

# def main():
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor(pymysql.cursors.DictCursor)
#     query = f"""
#         SELECT * FROM {db.link_table}
#         WHERE status = 'pending' limit 1
#     """
#     cursor.execute(query)
#     rows = cursor.fetchall()
#     cursor.close()
#     conn.close()
#     if not rows:
#         print("No pending product found.")
#         return
#     # 🔥 THREAD EXECUTION
#     results = []
#     with ThreadPoolExecutor(max_workers=4) as executor:
#         results = list(executor.map(process_product, rows))
#     # 🔥 BATCH DB UPDATE (IMPORTANT)
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor()
#     update_query = f"""
#         UPDATE `{db.link_table}`
#         SET status = %s
#         WHERE link = %s AND code = %s
#     """
#     cursor.executemany(update_query, results)
#     conn.commit()
#     cursor.close()
#     conn.close()
#     print("✅ All updates done")


if __name__ == '__main__':
    # PROXY_FILE = r"D:\CODE\food_panda\iproyal-proxies.txt"
    # PROXIES = load_proxies(PROXY_FILE)
    # print("Loaded proxies:", len(PROXIES))
    main()