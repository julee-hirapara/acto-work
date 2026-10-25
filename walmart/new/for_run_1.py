import json
import os
import pymysql.cursors
from parsel import Selector
import re
import headers_cookies as hc
import requests
import db_config as db
from glom import glom
import time
from datetime import datetime
from headers_cookies import cookies_pdp, headers_pdp


def save_data_db(item):
    for k, v in item.items():
        if not v:
            item[k] = "N/A"
    cols = ", ".join(item.keys()).strip(', ')
    values = tuple(item.values())
    try:
        with db.get_db_connection(db.db_name) as con:
            with con.cursor() as cur:
                insert_active = f"""INSERT INTO {db.data_table} ({cols}) VALUES {values}"""
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
    try:
        idml_data = json_data.get("idml") or {}
        specs = idml_data.get("specifications", [])
        if specs:
            for hg in specs:
                try:
                    specifications[hg.get("name")] = hg.get("value", "N/A")
                except:
                    pass
    except Exception as e:
        print("Specification Error:", e)
    return specifications

# def get_specifications(json_data):
#     specifications = {}
#     if json_data.get("idml", {}).get("specifications", []):
#         for hg in json_data.get("idml", {}).get("specifications", []):
#             try:
#                 specifications[hg.get("name")] = hg.get("value", "N/A")
#             except:
#                 pass
#     return specifications


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
    # item.pop("category_name", None)
    item.pop("pl_url", None)
    item.pop("cat_id", None)
    item.pop("status", None)
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
    file_loc = f"{db.PAGESAVE_PATH}\\CATEGORY\\{record['category_name']}\\PDP\\"
    os.makedirs(file_loc, exist_ok=True)
    file_name = f"{file_loc}\\{record['product_id']}.html.gz"
    if os.path.exists(file_name):
        return db.read_page(file_name)
    else:
        # p_url = product['product_url']
        # product_id = extract_product_id(p_url)
        # print('[FETCH]', p_url)
        # targetUrl = urllib.parse.quote(p_url, safe="")
        # print("[ENCODED URL]", targetUrl)
        # scrape_url = (
        #     f"http://api.scrape.do/?token={token}"
        #     f"&url={targetUrl}"
        #     f"&customHeaders=true"
        #     f"&super=true"
        # )
        # print("[REQ]", scrape_url)
        # # response = requests.get(scrape_url, headers=headers, timeout=120)

        proxy = {
            "http": f'http://***HIDDEN***:super=true@proxy.scrape.do:8080',
            "https": f'http://***HIDDEN***:super=true@proxy.scrape.do:8080',
        }
        # response = requests.get(record['product_url'], proxies=proxy, cookies=cookies_pdp ,verify=False,timeout=60)
        try:
            response = requests.get(
                record['product_url'],
                proxies=proxy,
                cookies=cookies_pdp,
                headers=headers_pdp,
                verify=False,
                timeout=60
            )
            print(response)
            if response.status_code == 200:
                db.save_page(
                    file_name,
                    response=response.text
                )
                return response.text
            else:
                print(f"Wrong response -> {response.status_code}")
                return None
        except requests.exceptions.ProxyError as e:
            print("Proxy Error:", e)
            return None
        except requests.exceptions.SSLError as e:
            print("SSL Error:", e)
            return None
        except requests.exceptions.Timeout as e:
            print("Timeout Error:", e)
            return None
        except requests.exceptions.RequestException as e:
            print("Request Error:", e)
            return None
        except Exception as e:
            print("Unknown Error:", e)
            return None



if __name__ == "__main__":
    with db.get_db_connection(db.db_name) as con:
        with con.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(
                f"""
                SELECT * 
                FROM {db.link_table} 
                WHERE status='pending' 
                AND category_name='rice' 
                LIMIT 700
                """
            )
            records = cur.fetchall()
    for record in records:
        response = fetch_response(record)
        if not response:
            continue
        response = Selector(response)
        raw_json = response.xpath(
            "//script[@id='__NEXT_DATA__']//text()"
        ).get()
        if not raw_json:
            print("No __NEXT_DATA__ Found")
            continue
        try:
            json_data = json.loads(raw_json)
        except Exception as e:
            print("JSON LOAD ERROR:", e)
            product_id = record.get("product_id", "unknown")
            error_file = f"json_error_{product_id}.txt"
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(raw_json)
            continue
        data = extract_data(json_data, record)
        if not data:
            continue
        # SAVE DATA
        save_data_db(data)
        # UPDATE STATUS AFTER SUCCESS
        try:
            with db.get_db_connection(db.db_name) as con:
                with con.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE {db.link_table}
                        SET status='done'
                        WHERE product_id=%s
                        """,
                        (record["product_id"],)
                    )
                    con.commit()
            print(f"Updated status to done : {record['product_id']}")
        except Exception as e:
            print(f"Status update failed for {record['product_id']} : {e}")
