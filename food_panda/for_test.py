# https://www.foodpanda.my/adventure-map/adventure-map-index-restaurant.xml

# import requests
# import json
# headers = {
#     'accept': 'application/json, text/plain, */*',
#     'accept-language': 'en-US,en;q=0.9',
#     'apollographql-client-name': 'web',
#     'apollographql-client-version': 'VENDOR-LIST-MICROFRONTEND.26.17.0017',
#     'app-version': 'VENDOR-LIST-MICROFRONTEND.26.17.0017',
#     'authorization': '',
#     'content-type': 'application/json;charset=UTF-8',
#     'customer-code': 'undefined',
#     'customer-latitude': '3.14789',
#     'customer-longitude': '101.69405',
#     'display-context': 'rlp',
#     # 'dps-session-id': '***HIDDEN***',
#     'locale': 'en_MY',
#     'origin': 'https://www.foodpanda.my',
#     'perseus-client-id': '1777874806175.306314031362213428.yva1tod3yd',
#     'perseus-session-id': '1777874806175.759377700660563418.1s6ky1yzww',
#     'platform': 'web',
#     'priority': 'u=1, i',
#     'referer': 'https://www.foodpanda.my/',
#     # 'request-id': 'f30dc9e1-28f6-4b73-80b9-b69e5f059ac7',
#     'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'empty',
#     'sec-fetch-mode': 'cors',
#     'sec-fetch-site': 'cross-site',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
#     'x-apollo-operation-name': 'GetVendorListPage',
#     'x-fp-api-key': 'volo',
# }
#
# json_data = {
#     'extensions': {
#         'persistedQuery': {
#             'sha256Hash': '***HIDDEN***',
#             'version': 1,
#         },
#     },
#     'variables': {
#         'input': {
#             'expeditionType': 'DELIVERY',
#             'latitude': 3.14789,
#             'locale': 'en_MY',
#             'longitude': 101.69405,
#             'customerType': 'B2C',
#             'featureFlags': [
#                 {
#                     'name': 'dynamic-pricing-indicator',
#                     'value': 'Variant',
#                 },
#                 {
#                     'name': 'saver-delivery-upper-funnel',
#                     'value': 'Variation1',
#                 },
#                 {
#                     'name': 'pd-mp-homescreen-full-federation-listing',
#                     'value': 'Control',
#                 },
#                 {
#                     'name': 'vdp_citadel-tech-integration',
#                     'value': 'Control',
#                 },
#                 {
#                     'name': 'pd-mp-slp-replatform-federated',
#                     'value': 'Variation1',
#                 },
#             ],
#             'languageId': 1,
#             'page': 'RESTAURANT_LANDING_PAGE',
#         },
#     },
# }
#
# response = requests.post('https://my.fd-api.com/graphql',
#                          headers=headers,
#                          json=json_data)
# print(response)
# with open("data.json", "w", encoding='utf-8') as f:
#     json.dump(response.json(), f, ensure_ascii=False, indent=4)
import json

###############################################################################################################


import requests
import json
import re
from datetime import datetime
from parsel import Selector


def extract_complete_foodpanda_data(api_json, html_text):
    """
    Extracts:
    - Vendor info (SEO + API + PROVIDER_PROPS)
    - Menu data (products, pricing)
    """

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
        # Extract JSON safely
        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*\})', script_text, re.DOTALL)
        if match:
            raw_json = match.group(1)
            try:
                data = json.loads(raw_json)
                main_vendor_id = (
                    data.get("vendor", {})
                    .get("data", {})
                    .get("chain", {})
                    .get("main_vendor_id")
                )
            except Exception as e:
                print("JSON error:", e)
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

    rating = seo.get("aggregateRating", {}).get("ratingValue")
    rating_count = seo.get("aggregateRating", {}).get("ratingCount")

    cuisines = ", ".join(seo.get("servesCuisine", []))
    vendor_image = (seo.get("image") or [None])[0]

    # ---------- Opening Hours ----------
    opening_hours = {}
    for spec in seo.get("openingHoursSpecification", []):
        days = spec.get("dayOfWeek", [])
        opens = spec.get("opens")
        closes = spec.get("closes")

        for d in days:
            opening_hours[d.lower()] = f"{opens}-{closes}"

    # =========================
    # PROVIDER PROPS DATA
    # =========================
    brand = provider_data.get("brand")
    country_code = provider_data.get("countryConfig")
    platform = provider_data.get("platform")

    # =========================
    # API DATA
    # =========================
    d = api_json.get("data", {})

    vendor_chain_id = (d.get("chain") or {}).get("main_vendor_id")

    review_count = d.get("review_number")

    try:
        minimum_order_value = d.get("discounts", [])[0].get("minimum_order_value")
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

        "latitude": latitude,
        "longitude": longitude,

        "rating": rating,
        "rating_count": rating_count or review_count,

        "brand": brand,
        "country_code": country_code,
        "platform": platform,

        "minimum_order_value": minimum_order_value,
        "delivery_details": delivery_details,

        "scraped_date": scraped_date,
        "scraped_time": scraped_time,
        "delivery_date": delivery_date
    }

    # =========================
    # MENU EXTRACTION
    # =========================
    menus = d.get("menus", [])

    for menu in menus:
        for category in menu.get("menu_categories", []):

            category_name = category.get("name")

            for product in category.get("products", []):
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

                for var in product.get("product_variations", []):

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

cookies = {
    '_pxhd': '***HIDDEN***',
    '_pxvid': '***HIDDEN***',
    'dhhPerseusGuestId': '1777874806175.306314031362213428.yva1tod3yd',
    'dhhPerseusSessionId': '1777874806175.759377700660563418.1s6ky1yzww',
    'hl': 'en',
    'ld_key': '1777874806175.306314031362213428.yva1tod3yd',
    '_gcl_au': '1.1.336513244.1777874807',
    '_ga': 'GA1.1.677724357.1777874808',
    '_fbp': 'fb.1.1777874809588.411484642667452959',
    '__ssid': '19350db8-4f29-4efa-a78c-538dad29ba14',
    'locationGeoLocatorTrackedStatus': 'true',
    'user-address-model': '%7B%22longitude%22%3A101.69405%2C%22latitude%22%3A3.14789%2C%22countryCode%22%3A%22MY%22%7D',
    'dps-session-id': '3.14789_101.69405_1777874806175.306314031362213428.yva1tod3yd_1777875282_1777877082',
    '__cf_bm': '91ExVsV9jjw8o8ybelF.RBFQaADnUjYVkBKkGxaL5XU-1777875754.4598088-1.0.1.1-KJBiiGH5fcwc5bDIpceTDN7aiZCbm4zkKk6Ji0isJfpQAtcWYillgdytTJEFzJYv06oy0HJ.hkz6toP55N0tn6kKnMkrhfFmmxSCld71hJmpyh7MFlmeCseDMHS7fyCJ25p8xv2V9K1MmTLTLs5SZg',
    'ViewContentStatus': 'true',
    'fbaddtocart': 'true',
    '_twpid': 'tw.1777876098107.407972965420875107',
    '_tq_id.TV-81365445-1.cf54': '1383ad25aae41ceb.1777874809.0.1777876428..',
    'g_state': '{"i_l":0,"i_ll":1777876428889,"i_b":"H18UkXuG3Z9ZVudOItYI2XelL5BhqVnaSXEuWqfCwGM","i_e":{"enable_itp_optimization":1},"i_et":1777874809506}',
    '_ga_HCJXSZSZBP': 'GS2.1.s1777874807$o1$g1$t1777876443$j41$l0$h0',
    'dhhPerseusHitId': '1777876443841.020187518486226243.okxs32xfxp',
    '_px3': '***HIDDEN***',
    'pxcts': '***HIDDEN***',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'referer': 'https://www.foodpanda.my/restaurant/bkwq/sushi-kazoku-sunway-putra-mall',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    # 'cookie': '***HIDDEN***',
}

html_content = requests.get(
    'https://www.foodpanda.my/restaurant/bkwq/sushi-kazoku-sunway-putra-mall',
    cookies=cookies,
    headers=headers,
)
print(html_content)

with open("data.html", "w", encoding='utf-8') as f:
    f.write(html_content.text)

import pandas as pd

def save_to_excel(data, filename="foodpanda_data.xlsx"):
    if not data:
        print("No data to save")
        return

    df = pd.DataFrame(data)

    # Optional: reorder columns
    columns_order = [
        "vendor_id", "vendor_name", "url", "cuisines","address","post_code",
        "phone", "latitude", "longitude",
        "rating", "review_count", "minimum_order_value",
        "category_name", "menu_name",
        "regular_price", "discounted_price", "discount", "saved_price",
        "menu_image", "description",
        "modifier_group_name", "modifier_name", "modifier_price",
        "scraped_date", "country_code", "delivery_date"
    ]

    # keep only available columns
    df = df[[col for col in columns_order if col in df.columns]]

    df.to_excel(filename, index=False)
    print(f"✅ Saved to {filename}")
from datetime import datetime

def extract_full_data(data, country_code="MY"):
    rows = []

    base_url = "https://www.foodpanda.my"
    d = data.get("data", {})

    # ---------------- VENDOR INFO ----------------
    vendor_id = (d.get("chain") or {}).get("main_vendor_id")

    url = base_url + (d.get("web_path") or "")

    vendor_name = (d.get("vendor_legal_information") or {}).get("legal_name")

    cuisines_list = d.get("cuisines", [])
    cuisines = ", ".join([c.get("name") for c in cuisines_list if c.get("name")])
    address = d.get("address")
    post_code = d.get("post_code")
    phone = d.get("customer_phone")
    latitude = d.get("latitude")
    longitude = d.get("longitude")

    rating = d.get("rating")
    review_count = d.get("review_number")

    try:
        minimum_order_value = d.get("discounts", [])[0].get("minimum_order_value")
    except:
        minimum_order_value = None

    scraped_date = datetime.now().strftime("%Y-%m-%d")
    delivery_date = scraped_date

    # ---------------- MENU ----------------
    menus = d.get("menus", [])

    for menu in menus:
        for category in menu.get("menu_categories", []):

            category_name = category.get("name")

            for product in category.get("products", []):

                menu_name = product.get("name")
                description = product.get("description")
                image = product.get("file_path")

                variations = product.get("product_variations", [])

                if not variations:
                    continue

                for var in variations:

                    price = var.get("price") or 0

                    # ---------- PRICE LOGIC ----------
                    regular_price = price
                    discounted_price = price
                    discount = 0
                    saved_price = 0

                    # ---------- MODIFIERS ----------
                    modifier_group_name = None
                    modifier_name = None
                    modifier_price = None

                    # (optional advanced parsing later)

                    # ---------- FINAL ROW ----------
                    row = {
                        "vendor_id": vendor_id,
                        "vendor_name": vendor_name,
                        "url": url,
                        "cuisines": cuisines,
                        "address": address,
                        "post_code": post_code,
                        "phone": phone,
                        "latitude": latitude,
                        "longitude": longitude,
                        "rating": rating,
                        "review_count": review_count,
                        "minimum_order_value": minimum_order_value,

                        "category_name": category_name,
                        "menu_name": menu_name,

                        "regular_price": regular_price,
                        "discounted_price": discounted_price,
                        "discount": discount,
                        "saved_price": saved_price,

                        "menu_image": image,
                        "description": description,

                        "modifier_group_name": modifier_group_name,
                        "modifier_name": modifier_name,
                        "modifier_price": modifier_price,

                        "scraped_date": scraped_date,
                        "country_code": country_code,
                        "delivery_date": delivery_date,
                    }

                    rows.append(row)

    return rows
# import requests
from curl_cffi import requests
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'api-version': '7',
    'authorization': '',
    # 'dps-session-id': '***HIDDEN***',
    'origin': 'https://www.foodpanda.my',
    'perseus-client-id': '1777874806175.306314031362213428.yva1tod3yd',
    'perseus-session-id': '1777885697900.941756962097197298.t527doellv',
    'priority': 'u=1, i',
    'referer': 'https://www.foodpanda.my/',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'x-fp-api-key': 'volo',
    'x-pd-language-id': '1',
}

params = {
        "include": "menus,bundles,multiple_discounts",
        "language_id": "1",
        "opening_type": "delivery",
        "basket_currency": "MYR",
        "latitude": "3.14789",
        "longitude": "101.69405"
    }

response = requests.get(
    'https://my.fd-api.com/api/v5/vendors/bkwq',
    headers=headers,
    params=params,
    impersonate="chrome99"
)
print(response)
with open("data.json", "w", encoding='utf-8') as f:
    json.dump(response.json(), f, ensure_ascii=False, indent=4)
data = extract_full_data(response.json())
# print("data ::\n ", json.dumps(data))

vendor_info, menu_rows = extract_complete_foodpanda_data(
    api_json=response.json(),
    html_text=html_content.text
)

print("Vendor Info:")
print(json.dumps(vendor_info, indent=2))

print("\nMenu Rows:")
print(len(menu_rows))
# save_to_excel(data, "foodpanda_menu.xlsx")

import pandas as pd

# Vendor
df_vendor = pd.DataFrame([vendor_info])
df_vendor.to_excel("vendor.xlsx", index=False)

# Menu
df_menu = pd.DataFrame(menu_rows)
df_menu.to_excel("menu.xlsx", index=False)




import os
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


IMPERSONATE_LIST = [
    "chrome99",
    "chrome110",
    "edge99",
    "safari15_3",
    "chrome120"
]
random.choice(IMPERSONATE_LIST)

def extract_complete_foodpanda_data(api_json, html_text):
    """
    Extracts:
    - Vendor info (SEO + API + PROVIDER_PROPS)
    - Menu data (products, pricing)
    """
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
        # Extract JSON safely
        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*(\{.*\})', script_text, re.DOTALL)
        if match:
            raw_json = match.group(1)
            try:
                data = json.loads(raw_json)
                main_vendor_id = (
                    data.get("vendor", {})
                    .get("data", {})
                    .get("chain", {})
                    .get("main_vendor_id")
                )
            except Exception as e:
                print("JSON error:", e)
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

    rating = seo.get("aggregateRating", {}).get("ratingValue")
    rating_count = seo.get("aggregateRating", {}).get("ratingCount")

    cuisines = ", ".join(seo.get("servesCuisine", []))
    vendor_image = (seo.get("image") or [None])[0]

    # ---------- Opening Hours ----------
    opening_hours = {}
    for spec in seo.get("openingHoursSpecification", []):
        days = spec.get("dayOfWeek", [])
        opens = spec.get("opens")
        closes = spec.get("closes")

        for d in days:
            opening_hours[d.lower()] = f"{opens}-{closes}"

    # =========================
    # PROVIDER PROPS DATA
    # =========================
    brand = provider_data.get("brand")
    country_code = provider_data.get("countryConfig")
    platform = provider_data.get("platform")

    # =========================
    # API DATA
    # =========================
    d = api_json.get("data", {})

    vendor_chain_id = (d.get("chain") or {}).get("main_vendor_id")

    review_count = d.get("review_number")

    try:
        minimum_order_value = d.get("discounts", [])[0].get("minimum_order_value")
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

        "latitude": latitude,
        "longitude": longitude,

        "rating": rating,
        "rating_count": rating_count or review_count,

        "brand": brand,
        "country_code": country_code,
        "platform": platform,

        "minimum_order_value": minimum_order_value,
        "delivery_details": delivery_details,

        "scraped_date": scraped_date,
        "scraped_time": scraped_time,
        "delivery_date": delivery_date
    }

    # =========================
    # MENU EXTRACTION
    # =========================
    menus = d.get("menus", [])

    for menu in menus:
        for category in menu.get("menu_categories", []):

            category_name = category.get("name")

            for product in category.get("products", []):
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

                for var in product.get("product_variations", []):

                    price = var.get("price") or 0
                    mrp = var.get("price_before_discount") or 0
                    discount = 0
                    if mrp and price and mrp > price:
                        discount = mrp - price  # absolute discount

                    row = {
                        "vendor_id": vendor_info["vendor_id"],
                        "url": vendor_info["url"],
                        "category_name": category_name,
                        "item_code": item_code,
                        "menu_name": menu_name,
                        "regular_price": mrp,
                        "price": price,
                        "discount": discount,
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


def get_pdp_page(link, code, name):
    cookies = {
        '_pxhd': '***HIDDEN***',
        '_pxvid': '***HIDDEN***',
        'dhhPerseusGuestId': '1777874806175.306314031362213428.yva1tod3yd',
        'dhhPerseusSessionId': '1777874806175.759377700660563418.1s6ky1yzww',
        'hl': 'en',
        'ld_key': '1777874806175.306314031362213428.yva1tod3yd',
        '_gcl_au': '1.1.336513244.1777874807',
        '_ga': 'GA1.1.677724357.1777874808',
        '_fbp': 'fb.1.1777874809588.411484642667452959',
        '__ssid': '19350db8-4f29-4efa-a78c-538dad29ba14',
        'locationGeoLocatorTrackedStatus': 'true',
        'user-address-model': '%7B%22longitude%22%3A101.69405%2C%22latitude%22%3A3.14789%2C%22countryCode%22%3A%22MY%22%7D',
        'dps-session-id': '3.14789_101.69405_1777874806175.306314031362213428.yva1tod3yd_1777875282_1777877082',
        '__cf_bm': '91ExVsV9jjw8o8ybelF.RBFQaADnUjYVkBKkGxaL5XU-1777875754.4598088-1.0.1.1-KJBiiGH5fcwc5bDIpceTDN7aiZCbm4zkKk6Ji0isJfpQAtcWYillgdytTJEFzJYv06oy0HJ.hkz6toP55N0tn6kKnMkrhfFmmxSCld71hJmpyh7MFlmeCseDMHS7fyCJ25p8xv2V9K1MmTLTLs5SZg',
        'ViewContentStatus': 'true',
        'fbaddtocart': 'true',
        '_twpid': 'tw.1777876098107.407972965420875107',
        '_tq_id.TV-81365445-1.cf54': '1383ad25aae41ceb.1777874809.0.1777876428..',
        'g_state': '{"i_l":0,"i_ll":1777876428889,"i_b":"H18UkXuG3Z9ZVudOItYI2XelL5BhqVnaSXEuWqfCwGM","i_e":{"enable_itp_optimization":1},"i_et":1777874809506}',
        '_ga_HCJXSZSZBP': 'GS2.1.s1777874807$o1$g1$t1777876443$j41$l0$h0',
        'dhhPerseusHitId': '1777876443841.020187518486226243.okxs32xfxp',
        '_px3': '***HIDDEN***',
        'pxcts': '***HIDDEN***',
    }

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
        print(f"🚀 Processing: {name} ({code})")

        session = tls_client.Session(
            client_identifier="chrome_142",
            random_tls_extension_order=True
        )
        # ---------------- HTML ----------------
        html_res = session.get(link,headers=headers,cookies=cookies,
                               # impersonate=random.choice(IMPERSONATE_LIST)
                               )
        print("html_res ::", html_res)
        if html_res.status_code != 200:
            print("❌ HTML failed")
            return ("failed", code, link, None, [])

        html_text = html_res.text
        folder_path = os.path.join(db.PDP_PAGESAVE, "html_pages")
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{code}.html")
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(html_res.text)

        # ---------------- API ----------------
        api_url = f"https://my.fd-api.com/api/v5/vendors/{code}"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'api-version': '7',
            'authorization': '',
            'origin': 'https://www.foodpanda.my',
            'perseus-client-id': '1777874806175.306314031362213428.yva1tod3yd',
            'perseus-session-id': '1777885697900.941756962097197298.t527doellv',
            'priority': 'u=1, i',
            'referer': 'https://www.foodpanda.my/',
            'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
            'x-fp-api-key': 'volo',
            'x-pd-language-id': '1',
        }

        params = {
            "include": "menus,bundles,multiple_discounts",
            "language_id": "1",
            "opening_type": "delivery",
            "basket_currency": "MYR",
            "latitude": "3.14789",
            "longitude": "101.69405"
        }
        api_res = session.get(
            api_url,
            headers=headers,
            params=params,
            # impersonate=random.choice(IMPERSONATE_LIST)
        )
        print("api_res ::", api_res)

        if api_res.status_code != 200:
            print("❌ API failed")
            return ("failed", code, link, None, [])

        api_json = api_res.json()
        folder_path = os.path.join(db.PDP_PAGESAVE, "json_pages")
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{code}.json")
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(api_json, f, ensure_ascii=False, indent=4)
        # ---------------- EXTRACT ----------------
        vendor_info, menu_rows = extract_complete_foodpanda_data(
            api_json=api_json,
            html_text=html_text
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


def main():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = f""" 
        SELECT * FROM {db.link_table} 
        WHERE status = 'pending' LIMIT 150
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
    with ThreadPoolExecutor(max_workers=1) as executor:
        results = list(executor.map(process_product, rows))
    # =========================
    # PROCESS RESULTS
    # =========================
    for result in results:
        status, link, code, vendor_info, menu_rows = result
        # ✅ DB update tuple (ONLY 3 VALUES)
        db_updates.append((status, link, code))
        # ✅ collect vendor data
        if vendor_info:
            all_vendor_data.append(vendor_info)
        # ✅ collect menu data
        if menu_rows:
            all_menu_data.extend(menu_rows)
    # =========================
    # SAVE FILES (3 FILES)
    # =========================
    if all_vendor_data:
        df_vendor = pd.DataFrame(all_vendor_data)
        df_vendor.to_excel("vendors_all.xlsx", index=False)
    if all_menu_data:
        df_menu = pd.DataFrame(all_menu_data)
        df_menu.to_excel("menus_all.xlsx", index=False)
    # ✅ MERGED FILE
    if all_vendor_data and all_menu_data:
        df_vendor = pd.DataFrame(all_vendor_data)
        df_menu = pd.DataFrame(all_menu_data)
        df_merged = df_menu.merge(df_vendor, on="vendor_id", how="left")
        df_merged.to_excel("merged_all.xlsx", index=False)
    print("✅ Files saved")
    # =========================
    # DB UPDATE
    # =========================
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    update_query = f"""
        UPDATE `{db.link_table}`
        SET status = %s
        WHERE link = %s AND code = %s
    """
    cursor.executemany(update_query, db_updates)
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ DB updated")

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
    main()
