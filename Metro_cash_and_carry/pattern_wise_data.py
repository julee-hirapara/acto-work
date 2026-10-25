import os
import re
import json
import time
import string
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import db_config_1 as db


# 🔗 API URL
URL = "https://www.metrorrl.com/ext/catalogueDiscovery/api/search/v1.0/products/"

# ⚡ Use Session (faster)
session = requests.Session()

# 🍪 COOKIES
cookies = {
    'app_location_details': '%7B%22country%22%3A%22INDIA%22%2C%22country_iso_code%22%3A%22IN%22%2C%22pincode%22%3A%22700001%22%2C%22state_code%22%3A%2219%22%2C%22city%22%3A%22Kolkata%22%2C%22state%22%3A%22West%20Bengal%22%7D',
}

# 🔐 HEADERS
headers = {
    'Accept': 'application/json, text/plain, */*',
    'Authorization': 'Bearer ***HIDDEN***',
    'User-Agent': 'Mozilla/5.0',
    'x-currency-code': 'INR',
    'x-location-detail': '{"country":"INDIA","country_iso_code":"IN","pincode":"700001","state_code":"19","city":"Kolkata","state":"West Bengal"}',
}


# 📁 Create folder
def ensure_folder(path):
    os.makedirs(path, exist_ok=True)


# 🧹 Clean filename
def clean_name(name):
    return re.sub(r'[^a-zA-Z0-9]+', '_', name).strip('_')


# 🚀 Pagination function
def search_with_pagination(query, save_folder):
    all_items = []
    page_id = None
    page_no = 1

    clean_query = clean_name(query) if query else "empty"

    while True:
        params = {
            "f": "display:AAAA:::type:product:::source:suggestion:::search:true:::app_user_id:69d759119a8fb019a6c5b65d",
            "page_size": 100,
            "q": query
        }

        if page_id:
            params["page_id"] = page_id

        file_path = os.path.join(save_folder, f"{clean_query}_page_{page_no}.json")

        # 📂 Load cached
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        else:
            try:
                response = session.get(
                    URL,
                    headers=headers,
                    params=params,
                    cookies=cookies,
                    timeout=10
                )

                if response.status_code != 200:
                    print(f"❌ {query} failed: {response.status_code}")
                    break

                data = response.json()

                # 💾 Save
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)

            except Exception as e:
                print(f"❌ Error {query}: {e}")
                break

        items = data.get("items", [])
        if not items:
            break

        all_items.extend(items)

        page_info = data.get("page", {})
        if not page_info.get("has_next"):
            break

        next_id = page_info.get("next_id")
        if not next_id:
            break

        page_id = next_id
        page_no += 1

        time.sleep(0.1)  # small delay per page

    return all_items


# 🔥 Worker function
def process_query(q, save_folder):
    items = search_with_pagination(q, save_folder)
    return q, items


# 🧠 Main runner
def run_full_search():
    save_folder = os.path.join(db.PL_PAGESAVE, "search_pages")
    ensure_folder(save_folder)

    all_results = []
    seen_uids = set()

    # 🔤 Queries (AAA — ⚠️ heavy)
    queries = []
    for c1 in string.ascii_uppercase:
        for c2 in string.ascii_uppercase:
            for c3 in string.ascii_uppercase:
                queries.append(c1 + c2 + c3)

    print(f"🚀 Total queries: {len(queries)}")

    MAX_WORKERS = 5  # ⚠️ safe limit

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_query, q, save_folder) for q in queries]

        for future in as_completed(futures):
            try:
                q, items = future.result()

                for item in items:
                    uid = item.get("uid")
                    if uid and uid not in seen_uids:
                        seen_uids.add(uid)
                        all_results.append(item)

                print(f"✅ {q} done | Total unique: {len(all_results)}")

            except Exception as e:
                print(f"❌ Thread error: {e}")

    # 💾 Save final
    output_path = os.path.join(db.PL_PAGESAVE, "all_products_combined.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 DONE! Total unique products: {len(all_results)}")
    print(f"📁 Saved at: {output_path}")


# ▶️ RUN
if __name__ == "__main__":
    run_full_search()