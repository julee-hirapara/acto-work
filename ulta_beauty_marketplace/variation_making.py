import re

from curl_cffi import requests
from parsel import Selector
import os
import header_cookies as hc
import db_config as db
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_response(url):
    sku = url.split("sku=")[-1]
    pdp_id = url.split("?")[0].split("-")[-1]
    file_dir = f"{db.pagesSave_path}\\PDP"
    os.makedirs(file_dir, exist_ok=True)
    file_name = f"{file_dir}\\{pdp_id}_{sku}.html.gz"
    if os.path.exists(file_name):
        return Selector(db.read_page(file_name))
    else:
        response = requests.get(
            url,
            cookies=hc.data_cookies,
            headers=hc.data_headers,
        )
        if response.status_code == 200:
            db.save_page(file_name, response.text)
            return Selector(response.text)
        else:
            print("Incorrect pdp response", response.status_code)
            return None

def get_color(json_data):
    t = "N/A"
    try:
        for pdp_sec in json_data['modules']:
            if pdp_sec['type'] == 'ProductReviews':
                if pdp_sec['variantType'] == "color":
                    t = pdp_sec["variantName"]
    except Exception as e:
        print("error from main info", e)
    return t

def clean_sku(text):
    text = text.replace("(", "-").replace(")", "-").replace("/", "-").replace(",", "-").replace("||", "-").replace(" ", "-").strip(" - ")
    text = re.sub(r'\-+', '-', text)
    return text


def get_variation(record, json_data):
    variants = []
    try:
        for pdp_sec in json_data['modules']:
            if pdp_sec['type'] == 'ProductVariant':
                try:
                    type_of_variant = pdp_sec['variantType']
                except:
                    type_of_variant = "N/A"
                if pdp_sec['variants']:
                    for variant in pdp_sec['variants']:
                        item = {}
                        item['type'] = type_of_variant
                        short_var_desc = variant.get("shadeDescription", "N/A") if variant.get("shadeDescription") else "N/A"
                        if "color" in type_of_variant.lower():
                            item['color'] = f"{variant['name']} ({short_var_desc})" if short_var_desc != "N/A" else variant['name']
                            item['size'] = record['size']
                            item['other'] = "N/A"
                        elif "size" in type_of_variant.lower():
                            item['color'] = record['color']
                            item['size'] = variant['name']
                            item['other'] = "N/A"
                        elif "N/A" in type_of_variant:
                            item['color'] = record['color']
                            item['size'] = record['size']
                            item['other'] = "N/A"
                        else:
                            item['color'] = record['color']
                            item['size'] = record['size']
                            try:
                                item['other'] = variant['name']
                            except:
                                item['other'] = "N/A"
                        if not item['size']:
                            item['size'] = "N/A"
                        if not item['color']:
                            item['color'] = "N/A"
                        item['SKU']  = variant['skuId']
                        item['name'] = record['name']
                        item['pid'] = record['pdp_id']
                        item['Link URL'] = f"{record['unique_url']}?sku={item['SKU']}"
                        item['isinstock'] = 'TRUE' if not variant['outofStockLabel'] else "FALSE"
                        item['status'] = 'pending'
                        item['MPN'] = db.hash12(f"{item['pid']}")
                        # if item['color'] == 'N/A' and item['size'] == "N/A":
                        #     item['sku_id'] = record['pdp_id']
                        # else:
                        #     if item['color'] == 'N/A' and item['size'] != "N/A":
                        #         item['sku_id'] = f"{record['pdp_id']}-{item['size']}"
                        #     elif item['color'] != 'N/A' and item['size'] == "N/A":
                        #         item['sku_id'] = f"{record['pdp_id']}-{item['color']}"
                        #     else:
                        #         item['sku_id'] = f"{record['pdp_id']}-{item['color']}-{item['size']}"
                        # item['sku_id'] = clean_sku(item['sku_id'])
                        variants.append(item)
    except Exception as e:
        print(e)
    return variants

def get_size(json_data):
    try:
        for pdp_sec in json_data['modules']:
            if pdp_sec['type'] == 'ProductVariant':
                if pdp_sec['dimensionsLabel'] == 'Size':
                    return pdp_sec['dimensionsValue']
    except Exception as e:
        print("Error from reviews", e)
        return "N/A"


def extract_metadata(record, response):
    try:
        item = {}
        raw_data = response.xpath("//script[@id='apollo_state']//text()").get()
        if raw_data:
            raw_data = json.loads(raw_data.split("window.__APOLLO_STATE__ =")[-1].split("window.__AUTH0_CALLBACK__")[0].strip())
            key_to_data = [x for x in list(raw_data['ROOT_QUERY'].keys()) if "Page(" in x][0]
            data = raw_data['ROOT_QUERY'][key_to_data]['content']
            pdp_data_json = None
            for module in data['modules']:
                if module['moduleName'] == "MainWrapper":
                    for sub_modules in module['modules']:
                        if sub_modules['type'] == 'ProductHero':
                            pdp_data_json = sub_modules
            if pdp_data_json:
                size = get_size(pdp_data_json)
                color = get_color(pdp_data_json)
                record['size'] = size
                record['color'] = color
                item['variants'] = get_variation(record, pdp_data_json)
                if item['variants']:
                    variation_collection.insert_many(item['variants'])
                    print("inserted Variation: ", len(item['variants']))
                    try:
                        input_col.update_one({"pdp_id": record['pdp_id']}, {"$set": {"status": "done"}})
                    except Exception as e:
                        print(e)
    except Exception as e:
        print(e)

def main(record):
    response = fetch_response(record["url"])
    if response:
        extract_metadata(record, response)


if __name__ == "__main__":
    main_data = []
    input_col = db.mongo_db[db.link_table_name]
    records = input_col.find({'status':'pending'})
    # records = input_col.find({'pdp_id':"mkt77000554"})
    variation_collection = db.mongo_db[db.variation_table_name]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(main, rec): rec for rec in records}
        for future in as_completed(futures):
            result = future.result()
