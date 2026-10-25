import json
import os
import urllib

import pymysql.cursors
from parsel import Selector
import re
import headers_cookies as hc
import requests
import db_config as db
from glom import glom

proxy = {
   "http": f'http://{db.token}:super=true@proxy.scrape.do:8080',
   "https": f'http://{db.token}:super=true@proxy.scrape.do:8080',
}

def save_data_db(item):
    for k, v in item.items():
        if not v:
            item[k] = "N/A"
    cols = ", ".join(item.keys()).strip(', ')
    values = tuple(item.values())
    try:
        with db.get_db_connection(db.db_name) as con:
            with con.cursor() as cur:
                insert_active = f"""INSERT IGNORE INTO {db.data_table} ({cols}) VALUES {values}"""
                cur.execute(insert_active)
                # cur.execute(f"UPDATE {db.link_table}_copy SET status='Done' WHERE product_id=%s", (item['product_id'],))
                con.commit()

                print('inserted', item['product_name'])
    except Exception as e:
        print(e)


def gallery_image(json_data):
    images = []
    try:
        for im in json_data['product']['imageInfo']['allImages']:
            try:
                if im['url'] not in images:
                    images.append(im['url'])
            except:
                pass
    except:
        pass
    return images


def get_bulletpoints(json_data):
    try:
        desc = json_data.get('idml', {}).get('longDescription', "N/A")
    except:
        desc = "N/A"
    if desc == "N/A":
        return "N/A"
    else:
        try:
            if "<" in desc and "</" in desc:
                desc = Selector(desc)
                return " ".join([x.strip() for x in desc.xpath("//li//text()").getall()]).strip()
            else:
                return desc
        except:
            return "N/A"


def get_specifications(json_data):
    specifications = {}
    if json_data.get("idml", {}).get("specifications", []):
        for hg in json_data.get("idml", {}).get("specifications", []):
            try:
                specifications[hg.get("name")] = hg.get("value", "N/A")
            except:
                pass
    return specifications


def get_highlights(json_data):
    hig = {}
    try:
        highlight_data = json_data.get("idml", {}).get("productHighlights", [])
        if highlight_data:
            for hg in highlight_data:
                try:
                    hig[hg.get("name")] = hg.get("value", "N/A")
                except:
                    pass
    except:
        pass
    return hig


def get_brand(json_data):
    try:
        return json_data.get("seoItemMetaData", {}).get("brand", "N/A")
    except:
        return "N/A"


def extract_data(json_data, record):
    item = {}
    item.update(record)
    item['source_url'] = item['product_url']
    del item['product_url']
    # del item['status']

    item['location'] = db.pincode
    item['product_pdf_urls'] = json.dumps([])
    main_data = json_data['props']['pageProps']['initialData']['data']
    item['brand'] = get_brand(main_data)
    item['avg_rating'] = glom(main_data, "product.averageRating", default="N/A")
    item['num_review'] = glom(main_data, "product.numberOfReviews", default="N/A")
    price = glom(main_data, "product.priceInfo.currentPrice.price", default="N/A")
    mrp = glom(main_data, "product.priceInfo.wasPrice.price", default="N/A")
    price_per_unit = glom(main_data, "product.priceInfo.unitPrice.priceString", default="N/A")
    item['product_price'] = price
    item['product_mrp'] = mrp if mrp != "N/A" else price
    item['price_per_unit'] = price_per_unit
    item['price_discount'] = "N/A"
    if item['product_price'] != "N/A" and item['product_mrp'] != "N/A":
        item['product_mrp'] = float(item['product_mrp'])
        item['product_price'] = float(item['product_price'])
        item['price_discount'] = round(item['product_mrp'] - item['product_price'], 2)
    if item['num_review'] == 1:
        item['num_review'] = main_data.get('reviews', {}).get('ratingValueFiveCount', 0) + main_data.get('reviews',
                                                                                                         {}).get(
            'ratingValueFourCount', 0) + main_data.get('reviews', {}).get('ratingValueOneCount', 0) + main_data.get(
            'reviews', {}).get('ratingValueThreeCount', 0) + main_data.get('reviews', {}).get('ratingValueTwoCount', 0)
        item['avg_rating'] = main_data.get('reviews', {}).get('roundedAverageOverallRating', "N/A")
    if not item['num_review']:
        item['num_review'] = main_data.get('reviews', {}).get('ratingValueFiveCount', 0) + main_data.get('reviews',
                                                                                                         {}).get(
            'ratingValueFourCount', 0) + main_data.get('reviews', {}).get('ratingValueOneCount', 0) + main_data.get(
            'reviews', {}).get('ratingValueThreeCount', 0) + main_data.get('reviews', {}).get('ratingValueTwoCount', 0)
    if not item['avg_rating']:
        item['avg_rating'] = glom(main_data, "reviews.roundedAverageOverallRating", default="N/A")
    item['product_image_urls'] = json.dumps(gallery_image(main_data))
    bulletPoints = get_bulletpoints(main_data)
    product_specifications = get_specifications(main_data)
    product_highlights = get_highlights(main_data)
    if product_highlights:
        product_specifications.update(product_highlights)
    item['product_specifications'] = json.dumps(get_specifications(main_data))

    desc = []
    try:
        desc.append(main_data.get('product', {}).get('shortDescription'))
    except:
        pass
    if bulletPoints != "N/A":
        desc.append(bulletPoints)
    item['product_description'] = re.sub(r"<[^>]+>", "", re.sub(r'\s+', ' ', " ".join(desc).strip())) if desc else "N/A"
    return item


def fetch_response(record):
    file_loc = f"{db.page_save_path}\\PDP\\"
    os.makedirs(file_loc, exist_ok=True)
    file_name = f"{file_loc}\\{record['product_id']}.html.gz"
    if os.path.exists(file_name):
        return db.read_page(file_name)
    else:
        # # targetUrl = urllib.parse.quote(record['product_url'], safe="")
        # # scrape_url = (
        # #     f"http://api.scrape.do/?token={db.token}"
        # #     f"&url={targetUrl}"
        # #     f"&customHeaders=true"
        # #     f"&super=true"
        # # )
        # # response = requests.get(scrape_url, headers=hc.headers_pdp, timeout=120)
        # response = requests.get(record['product_url'],headers=hc.headers_pdp, proxies=proxy,  # Use the proxy if available and if need to use.
        #                                     verify=False,
        #                                     timeout=600,
        #                                     allow_redirects=False)
        # print(f"url : {record['product_url']} || response : {response}")
        # # hash_id = generate_hash(p_url)
        # # file_name = f'{product_id}_{store_id}'
        response = requests.get(
            record['product_url'],
            cookies=hc.cookies_pdp,
            headers=hc.headers_pdp,
        )
        if response.status_code == 200:
            db.save_page(file_name, response=response.text)
            return response.text
        else:
            print("Wrong response", response.status_code)
            return None


if __name__ == "__main__":
    with db.get_db_connection(db.db_name) as con:
        with con.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(f"select * from {db.link_table}")
            records = cur.fetchall()
    for record in records:
        response = fetch_response(record)
        if not response:
            continue
        response = Selector(response)
        # raw_json = response.xpath("//script[@id='__NEXT_DATA__']//text()").get()
        # json_data = json.loads(raw_json)
        raw_json = response.xpath("//script[@id='__NEXT_DATA__']//text()").get()
        if not raw_json:
            print(f"__NEXT_DATA__ not found for URL: {record['product_url']}")
            continue
        try:
            json_data = json.loads(raw_json)
        except Exception as e:
            print(f"JSON parsing failed: {e}")
            continue
        data = extract_data(json_data, record)
        if not data:
            continue
        save_data_db(data)