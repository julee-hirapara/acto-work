import json
import copy
import requests
import time
import os
import db_config_1 as db

URL = "https://my.fd-api.com/graphql"

HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'apollographql-client-name': 'web',
    'apollographql-client-version': 'VENDOR-LIST-MICROFRONTEND.26.20.0021',
    'app-version': 'VENDOR-LIST-MICROFRONTEND.26.20.0021',
    'authorization': '',
    'content-type': 'application/json;charset=UTF-8',
    'customer-code': 'undefined',
    'customer-latitude': '3.1568055',
    'customer-longitude': '101.7132345',
    'display-context': 'rlp',
    'dps-session-id': '***HIDDEN***',
    'locale': 'en_MY',
    'origin': 'https://www.foodpanda.my',
    'perseus-client-id': '1779089708061.278774752923091213.6ijfojp1et',
    'perseus-session-id': '1779089708062.491562324727246210.a44cs2a9f5',
    'platform': 'web',
    'priority': 'u=1, i',
    'referer': 'https://www.foodpanda.my/',
    'request-id': '7dedd5db-edc6-4c6b-ae82-b704bbc7cef7',
    'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'x-apollo-operation-name': 'GetVendorListPage',
    'x-fp-api-key': 'volo',
}


BASE_PAYLOAD = {
    'extensions': {
        'persistedQuery': {
            'sha256Hash': '***HIDDEN***',
            'version': 1,
        },
    },
    'variables': {
        'input': {
            'expeditionType': 'DELIVERY',
            'latitude': 3.14789,
            'longitude': 101.69405,
            'locale': 'en_MY',
            'customerType': 'B2C',
            'languageId': 1,
            'page': 'RESTAURANT_LANDING_PAGE',
        },
    },
}

def extract_entities(page):
    """Handles BOTH structures safely"""
    entities = []

    for comp in page.get("components", []):

        # Case 1: entities list
        if isinstance(comp.get("entities"), list):
            entities.extend(comp["entities"])

        # Case 2: single vendorData
        if isinstance(comp.get("vendorData"), dict):
            entities.append(comp["vendorData"])

    return entities


def fetch_and_save_pages():
    next_token = None
    page_number = 1
    all_seen_urls = set()  # avoid duplicates

    os.makedirs("pages", exist_ok=True)

    BASE_URL = "https://www.foodpanda.my/restaurant/"

    while True:
        payload = copy.deepcopy(BASE_PAYLOAD)

        if next_token:
            payload['variables']['input']['tokenPagination'] = {
                'token': next_token
            }

        response = requests.post(URL, headers=HEADERS, json=payload)

        print(f"\nPage {page_number} | Status: {response.status_code}")

        if response.status_code != 200:
            print("Request failed")
            break

        data = response.json()

        # Save RAW page
        file_path = os.path.join(db.PL_PAGESAVE, f"page_{page_number}.json")
        # raw_path = f"pages/page_{page_number}_raw.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        try:
            page = data['data']['vendorListingPage']
        except:
            print("Invalid structure, stopping.")
            break

        # ✅ Extract entities dynamically
        entities = extract_entities(page)

        clean_data = []

        for v in entities:
            url_key = v.get("urlKey")
            if not url_key:
                continue
            name = v.get("name")
            # 🔥 fallback logic
            vendor_data = v.get("vendorChainData") or {}
            code = v.get("code") or vendor_data.get("mainVendorCode")
            # skip if still missing
            if not code:
                continue
            full_url = f"{BASE_URL}{code}/{url_key}"
            # avoid duplicates across pages
            if full_url in all_seen_urls:
                continue
            all_seen_urls.add(full_url)
            print(f"{name} -> {full_url}")
            # clean_data.append({
            #     "name": name,
            #     "url": full_url,
            #     "vendor_code": code,
            # })
            clean_data.append({
                "name": name,
                "link": full_url,
                "code": code,
                "slug": url_key
            })

        # Save CLEAN page
        clean_file_path = os.path.join(db.PL_PAGESAVE, "Clean_json")
        os.makedirs(clean_file_path, exist_ok=True)
        clean_path = os.path.join(clean_file_path, f"page_{page_number}_clean.json")
        with open(clean_path, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)

        print(f"Saved: {clean_path} | Items: {len(clean_data)}")
        if clean_data:
            insert_links(clean_data)
        token_data = page.get('tokenPagination')
        if not token_data:
            print("\n✅ No tokenPagination found → End reached")
            break
        next_token = token_data.get('token')
        if not next_token:
            print("\n✅ No next token → Crawling finished")
            break

        # # Get next token
        # next_token = page.get('tokenPagination', {}).get('token')
        #
        # if not next_token:
        #     print("\n✅ Crawling finished (no more pages)")
        #     break

        page_number += 1
        time.sleep(1)  # prevent blocking

def insert_links(data_list):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    insert_query = f"""
        INSERT IGNORE INTO {db.link_table} (link, slug, code, name, status)
        VALUES (%s, %s, %s, %s, %s)
    """
    values = []
    for item in data_list:
        values.append((
            item["link"],
            item["slug"],
            item["code"],
            item["name"],
            "pending"
        ))
    cursor.executemany(insert_query, values)
    conn.commit()
    print(f"Inserted {cursor.rowcount} new records")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    fetch_and_save_pages()


# if __name__ == "__main__":
#     fetch_and_save_pages()

# def fetch_all_restaurants():
#     all_restaurants = []
#     next_token = None
#     while True:
#         payload = copy.deepcopy(BASE_PAYLOAD)
#         if next_token:
#             payload['variables']['input']['tokenPagination'] = {'token': next_token}
#         response = requests.post(URL, headers=HEADERS, json=payload)
#         print("Status:", response.status_code)
#         if response.status_code != 200:
#             print("Request failed")
#             break
#         data = response.json()
#         # DEBUG SAVE
#         with open("data.json", "w", encoding='utf-8') as f:
#             json.dump(data, f, ensure_ascii=False, indent=2)
#         try:
#             page = data['data']['vendorListingPage']
#             # 👇 IMPORTANT: components[2]
#             entities = page['components'][2]['entities']
#             # 👇 TOKEN PATH
#             next_token = page.get('tokenPagination', {}).get('token')
#         except Exception as e:
#             print("Parsing error:", e)
#             break
#         # Extract required fields
#         for v in entities:
#             restaurant = {
#                 "name": v.get("name"),
#                 "vendor_code": v.get("vendorChainData", {}).get("mainVendorCode"),
#                 "url": v.get("urlKey"),
#             }
#             all_restaurants.append(restaurant)
#         print(f"Fetched {len(entities)} | Total: {len(all_restaurants)}")
#         if not next_token:
#             print("No more pages")
#             break
#         time.sleep(1)
#     return all_restaurants
#
#
# if __name__ == "__main__":
#     restaurants = fetch_all_restaurants()
#     print("\nTotal:", len(restaurants))
#     for r in restaurants[:5]:
#         print(r)