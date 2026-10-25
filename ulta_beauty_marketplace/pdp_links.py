from curl_cffi import requests
from parsel import Selector
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import header_cookies as hc
import db_config as db


def fetch_response(url, page, name):
    name = name.replace("/", "")
    file_dir = f"{db.pagesSave_path}\\Links"
    os.makedirs(file_dir, exist_ok=True)
    file_name = f"{file_dir}\\{name}_{page}.html.gz"
    if os.path.exists(file_name):
        return Selector(db.read_page(file_name))
    else:
        response = requests.get(
            url,
            cookies=hc.links_cookies,
            headers=hc.links_headers,
        )
        db.save_page(file_name, response.text)
        if response.status_code == 200:
            return Selector(response.text)
        else:
            print("Incorrect response", response.status_code)
            return None
    

def extract_metadata(record, response):
    for product in response.xpath("//li[@class='ProductListingResults__productCard']"):
        try:
            url = product.xpath(".//a[contains(@class, 'pal-c-Link--primary')]//@href").get()
            if url:
                item = {}
                item['url'] = url
                item['unique_url'] = url.split("?")[0] if "?" in url else url
                item['pdp_id'] = item['unique_url'].split("/")[-1].split("-")[-1]
                item['name'] = product.xpath(".//a[contains(@class, 'pal-c-Link--primary')]//span//text()").get()
                item['cat_name'] = record['name']
                item['cat_url'] = record['url']
                item['status'] = 'pending'
                link_collection.insert_one(item)
                print("Inserted Links:", item['pdp_id'])
        except Exception as e:
            if "duplicate key" in str(e):
                pass
            else:
                print(e)


def main(record):
    page_counter = 1
    url = record['url']
    name = record['name']
    while True:
        print("sending request on:", url)
        response = fetch_response(url, page_counter, name)
        next_page_link = response.xpath("//div[@class='ProductListingWrapper__LoadContent']//a[contains(text(), 'Load More')]//@href").get()
        if not response:
            break
        extract_metadata(record, response)
        if not next_page_link:
            break
        url = next_page_link
        page_counter+=1
    try:
        input_col.update_one({"url": record['url']}, {"$set": {"status": "done"}})
    except Exception as e:
        print(e)


if __name__ == "__main__":
    input_col = db.mongo_db[db.category_table_name]
    records = input_col.find({'status':'pending'})
    link_collection = db.mongo_db[db.link_table_name]
    link_collection.create_index('unique_url', unique=True)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(main, rec): rec for rec in records}
        for future in as_completed(futures):
            result = future.result()
