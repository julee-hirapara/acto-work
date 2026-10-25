import os

import requests
import json
from parsel import Selector
import header_cookies as hc
import db_config as db


def fetch_response():
    file_dir = f"{db.pagesSave_path}\\category"
    os.makedirs(file_dir, exist_ok=True)
    file_name = f"{file_dir}\\{db.today_crawling_date}_cat.html.gz"
    response = requests.get('https://www.ulta.com/', cookies=hc.cat_cookies, headers=hc.cat_headers)
    if response.status_code == 200:
        db.save_page(file_name, response.text)
        html_obj = Selector(response.text)
        raw_data = html_obj.xpath("//script[@id='apollo_state']//text()").get()
        if raw_data:
            raw_data = json.loads(raw_data.split("window.__APOLLO_STATE__ =")[-1].split("window.__AUTH0_CALLBACK__")[0].strip())
            return raw_data
        else:
            return None
    else:
        print("Incorrect Response: ", response.status_code)
        return None

def get_cat(module_list):
    extracted_cats = []
    if not module_list:
        return extracted_cats

    for module in module_list:
        action = module.get('action', {})
        label_condition = action.get("dataCaptureData", {}).get("dataLayer", {}).get("Tealium", {}).get(
            "navigation_group")
        if label_condition and "shop" in label_condition.lower():
            label = action.get("label")
            if label and not any(skip in label for skip in ["Current Ad", "Gift Cards"]):
                if action.get("url"):
                    extracted_cats.append({
                        "name": label,
                        "url": action.get("url"),
                        "id": module.get('id', "N/A"),
                        "status":"pending"
                    })
        nested_modules = module.get("modules", [])
        if nested_modules:
            extracted_cats.extend(get_cat(nested_modules))
    return extracted_cats

def main():
    response = fetch_response()
    if response:
        root_data = response.get('ROOT_QUERY').get('Page({"moduleParams":{},"url":{"path":"/"}})').get('content').get(
            "modules")
        cat_data = get_cat(root_data)
        if cat_data:
            cat_collection = db.mongo_db[db.category_table_name]
            cat_collection.create_index('url', unique=True)
            for item in cat_data:
                try:
                    cat_collection.insert_one(item)
                except:
                    pass
            print("Successfully saved category data")
if __name__ == '__main__':
    main()