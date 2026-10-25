# import db_config as db
#
# variation_col = db.mongo_db[db.variation_table_name]
# pdp_col = db.mongo_db[db.pdp_table_name]
#
# count = 0
#
# cursor = pdp_col.find(
#     {"Image URL": "N/A"},
#     {"Link URL": 1}
# )
#
# for doc in cursor:
#     link = doc.get("Link URL")
#
#     if not link:
#         continue
#
#     result = variation_col.update_many(
#         {"Link URL": link},
#         {"$set": {"status": "pending"}}
#     )
#
#     count += result.modified_count
#
# print(f"Updated {count} variation records to pending.")


#################################################################################################

from curl_cffi import requests
from parsel import Selector
import os
import header_cookies as hc
import db_config as db
import requests
import json
import ftfy
import unicodedata
from unidecode import unidecode
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_response(record):
    sku = record['SKU']
    pdp_id = record['pid']
    file_dir = f"{db.pagesSave_path}\\PDP"
    os.makedirs(file_dir, exist_ok=True)
    file_name = f"{file_dir}\\{pdp_id}_{sku}.html.gz"
    # if os.path.exists(file_name):
        # return Selector(db.read_page(file_name))
    # else:
    response = requests.get(
        record['Link URL'],
        cookies=hc.data_cookies,
        headers=hc.data_headers,
    )
    if response.status_code == 200:
        db.save_page(file_name, response.text)
        return Selector(response.text)
    else:
        print("Incorrect pdp response", response.status_code)
        return None

def get_reviews(json_data):
    rev = {
        "Average Ratings":"N/A",
        "Num Ratings":"N/A",
        'Name':'N/A'
    }
    try:
        for pdp_sec in json_data['modules']:
            if pdp_sec['type'] == 'ProductInformation':
                rev['Name'] = pdp_sec['productName']
                rev['Average Ratings'] = pdp_sec['rating']
                rev['Num Ratings'] = pdp_sec['reviewCount']
    except Exception as e:
        print("Error from reviews", e)
    return rev


def get_images(json_data):
    images = []
    try:
        for pdp_sec in json_data['modules']:
            if pdp_sec['type'] == 'MediaGallery':
                images = [x['imageUrl'] for x in pdp_sec['items']]
    except Exception as e:
        print("Error from images", e)
    return images

def get_price(json_data):
    price = {}
    price['Price'] = "N/A"
    price['Sale Price'] = "N/A"
    # price['priceLabel'] = "N/A"
    price['Category'] = "N/A"
    price['short_description'] = "N/A"
    price['Brand'] = "N/A"
    price['Price Currency'] = "N/A"
    price['Final Price'] = "N/A"
    price['Discount'] = "N/A"
    price['Varint_Price'] = "N/A"
    price['IsOnSale'] = "No"
    try:
        for pdp_sec in json_data['modules']:
            if pdp_sec['type'] == 'ProductPricing':
                price['Price'] = float(pdp_sec.get('listPrice').replace("$", "").replace(",","")) if pdp_sec.get('listPrice') else "N/A"
                price['Sale Price'] = float(pdp_sec.get('salePrice').replace("$", "").replace(",","")) if  pdp_sec.get('salePrice') else "N/A"
                # price['priceLabel'] = pdp_sec.get('priceLabel', "N/A")
                price['Category'] = pdp_sec['productCategory']
                price['Brand'] = pdp_sec.get('brandName', "N/A")
                price['Price Currency'] = pdp_sec.get('afterpay', {}).get('currency', "N/A")
            if pdp_sec['type'] == 'ProductSummary':
                price['short_description'] = pdp_sec.get("message", "N/A")
    except Exception as e:
        print("Error from pricing", e)
    price['Final Price'] = price['Price']
    if price['Sale Price'] != 'N/A':
        price['Final Price'] = price['Sale Price']
        price['Discount'] = round(price['Price'] - price['Sale Price'], 2)
        price['IsOnSale'] = "Yes"
    else:price['Sale Price']=price['Price']
    price['Varint_Price'] = price['Final Price']
    return price

def get_description(json_data):
    description = "N/A"
    try:
        for pdp_sec in json_data['modules']:
            if pdp_sec['type'] == 'ProductDetail':
                description = pdp_sec['description'].replace("\n", "").replace("####", "|").strip("|").replace("Features-", "Features: ").replace("Benefits-", "Benefits: ").replace("Research Results-", "Research Results: ").replace("Key Ingredients-", "Key Ingredients: ").strip()
    except Exception as e:
        print("Error from description", e)
    return description

def clean_text(text: str) -> str:
    try:
        text = ftfy.fix_text(text)
        text = unicodedata.normalize("NFC", text)
        text = unidecode(str(text))
        return text.strip()
    except Exception as e:
        print(e)
        return text

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
                unique_url = record['Link URL'].split("?")[0]
                item['MPN'] = db.hash12(f"{record['pid']}{record['SKU']}")
                item['SKU'] = record['SKU']
                item['hash_id'] = db.hash12(unique_url)
                item['Size'] = record['size']
                item['IsInStock'] = record['isinstock']
                item['Color'] = record['color']
                item['Other'] = record['other']
                item['Website'] = 'Ulta Beauty'
                item['Keywords'] = "N/A"
                item['Gender'] = "N/A"
                item['UPC or EAN'] = "N/A"
                item['Manufacturer'] = "N/A"
                item['Link URL'] = record['Link URL']
                item['PID'] = record['pid']
                item['Name'] = record['name']
                item['Description'] = clean_text(get_description(pdp_data_json))
                item.update(get_price(pdp_data_json))
                item['Image URL'] = get_images(pdp_data_json)
                if item['Image URL']:
                    item['Alternate Image URLs'] = " | ".join(item['Image URL'][1:]) if len(item['Image URL']) > 2 else "N/A"
                    item['Image URL'] = item['Image URL'][0]
                else:
                    item['Image URL'] = "N/A"
                    item['Alternate Image URLs'] = "N/A"
                item.update(get_reviews(pdp_data_json))
                item['Category'] = item['Category'].replace(":", "/")

                # data_collection.insert_one(item)
                result = data_collection.update_one(
                    {"Link URL": record["Link URL"]},
                    {"$set": item}
                )
                if result.matched_count:
                    print(f"Updated: {record['pid']} {record['SKU']}")
                else:
                    print(f"No existing record found for {record['Link URL']}")
                input_col.update_one({'Link URL':record['Link URL']}, {'$set':{'status':'done'}})
                print("Inserted", record['pid'] , record['SKU'])
    except Exception as e:
        print(e)

def main(record):
    response = fetch_response(record)
    if response:
        extract_metadata(record, response)


if __name__ == "__main__":
    main_data = []
    input_col = db.mongo_db[db.variation_table_name]
    records = input_col.find({'status':'pending'})
    data_collection = db.mongo_db[db.pdp_table_name]
    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = {executor.submit(main, rec): rec for rec in records}
        for future in as_completed(futures):
            result = future.result()