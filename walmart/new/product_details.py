from db_config import *
from parsel import Selector
import traceback
import re
from set_store import get_store_cookies, timestamp


def remove_extra_spaces(input_string):
    cleaned_string = re.sub(r'\s+', ' ', input_string.strip())
    return cleaned_string


def get_product_urls_from_db():
    urls = []
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT MIN(id) AS id, product_url FROM product_urls WHERE STATUS = 'pending' AND id BETWEEN 151579 AND 176846 GROUP BY product_url")
            # cursor.execute("SELECT MIN(id) AS id, product_url FROM product_urls WHERE STATUS = 'pending' AND id BETWEEN 170912 AND 177071 GROUP BY product_url")
            # cursor.execute("SELECT MIN(id) AS id, product_url FROM product_urls WHERE STATUS = 'pending' AND id BETWEEN 126481 AND 151776 GROUP BY product_url")

            rows = cursor.fetchall()
            for row in rows:
                # print(row)
                # urls.append({'category_name': row['category_name'], 'product_url': row['product_url']})
                urls.append({'parent_id': row[0], 'product_url': row[1]})
                # urls.append({'product_url': row[0]})
    except Exception as e:
        print(f"[ERROR] Failed to fetch product_url from DB → {e}")
    return urls


def get_store_urls_from_db():
    urls = []
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT storeid, url FROM store_urls WHERE status = 'pending' and state='New York'")
            rows = cursor.fetchall()
            # print(rows)
            for row in rows:
                # urls.append({'storeid': row['storeid'], 'url': row['url']})
                urls.append({'storeid': int(row[0]), 'url': row[1]})
    except Exception as e:
        traceback.print_exc()
        print(f"[ERROR] Failed to fetch store_url from DB → {e}")
    return urls


def create_products_table():
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cursor:
        cursor.execute("""
    CREATE TABLE IF NOT EXISTS walmart_products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        upc VARCHAR(50),
        parent_id VARCHAR(50),
        brand VARCHAR(255),
        url TEXT,
        title TEXT,
        images JSON,
        storeId VARCHAR(50),
        state VARCHAR(50),
        nutrition JSON,
        ingredients TEXT,
        locationInfo TEXT,
        description TEXT,
        descriptionFull TEXT,
        price DECIMAL(10, 2),
        net_weight VARCHAR(100),
        pack_size VARCHAR(100),
        allergens TEXT,
        calories VARCHAR(50),
        category VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()



def insert_product_data(item):
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO walmart_products (
                upc, parent_id, brand, url, title, images, storeId, state, nutrition,
                ingredients, locationInfo, description, descriptionFull,
                price, net_weight, pack_size, allergens, calories, category
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            cursor.execute(sql, (
                item.get('upc'),
                item.get('parent_id'),
                item.get('brand'),
                item.get('url'),
                item.get('title'),
                json.dumps(item.get('images')),
                item.get('storeId'),
                item.get('state'),
                json.dumps(item.get('nutrition')),
                item.get('ingredients'),
                item.get('locationInfo'),
                item.get('description'),
                item.get('descriptionFull'),
                item.get('price'),
                item.get('net_weight'),
                item.get('pack_size'),
                item.get('allergens'),
                item.get('calories'),
                item.get('category')
            ))
        connection.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Insert failed → {e}")
        return False
    finally:
        connection.close()


def save_raw_html(product_id, html_text):
    os.makedirs(fr"D:\walmart\new_code\{store_id}\pdp\pages\html", exist_ok=True)
    with open(fr"D:\walmart\new_code\{store_id}\pdp\pages\html\{product_id}.html", "w", encoding="utf-8") as f:
        f.write(html_text)


def save_json(product_id, json_data):
    os.makedirs(fr"D:\walmart\new_code\{store_id}\pdp\pages\json", exist_ok=True)
    with open(fr"D:\walmart\new_code\{store_id}\pdp\pages\json\{product_id}.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)


def update_product_status(url, status, store_id):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            sql = """
                UPDATE product_urls 
                SET status = %s, store_id = %s
                WHERE product_url = %s
            """
            cursor.execute(sql, (status, store_id, url))
        conn.commit()
        print(f"[INFO] Updated → {url} | status={status}, store_id={store_id}")
    except Exception as e:
        print(f"[ERROR] Failed to update {url} → {e}")

def update_store_status(storeid, status):
    conn = pymysql.connect(**DB_CONFIG)
    with conn.cursor() as cursor:
        cursor.execute("UPDATE store_urls SET status = %s WHERE storeid = %s", (status, storeid))
        conn.commit()


def size_weight_model(lt):
    Model = "N/A"
    Product_Dimensions = "N/A"
    Voltage = "N/A"
    Size = "N/A"
    Color = "N/A"
    Material = "N/A"
    Manufacturer = "N/A"
    Brand = "N/A"
    Weight = "N/A"
    if lt:
        for each_in in lt:
            key = each_in.split(":")[0].strip()
            value = each_in.split(":")[1].strip()
            if "Model" in key:
                Model = value
            if "Assembled Product Dimensions" in key:
                Product_Dimensions = value
            if "Voltage" in key:
                Voltage = value
            if "Size" in key:
                Size = value
            if "Color" in key:
                Color = value
            if "Material" in key:
                Material = value
            if "Brand" in key:
                Brand = value
            if "Assembled Product Weight" in key:
                Weight = value
            if "Manufacturer" in key:
                Manufacturer = value
            if Material == "N/A" and "Fabric Content" in key:
                Material = value
    return {"Model": Model, "Material": Material, "Manufacturer": Manufacturer,
            "Product_Dimensions": Product_Dimensions,
            "Weight": Weight, "Brand": Brand, "Color": Color, "Size": Size, "Voltage": Voltage}


def extract_oz(product_name):
    match = re.search(r'(\d+(\.\d+)?)\s*oz', product_name, re.IGNORECASE)
    if match:
        return match.group(1) + ' oz'
    return 'N/A'


def extract_number(text):
    match = re.search(r'\d+', text)
    return match.group(0) if match else "N/A"


def extract_product_id(url):
    """Extract product ID from Walmart URL, handling query parameters"""
    # Split on both '/' and '?' to handle query parameters
    parts = url.split('/')[-1].split('?')
    return parts[0]  # Return the product ID before any query parameters


# def scrape_func(response, product_id):
#     try:
#         # Empty dictionary to store data further
#         item = {}
#         try:
#             selector_obj = Selector(response.text)
#         except:
#             selector_obj = Selector(response)
#         data_json = json.loads(selector_obj.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
#         save_json(product_id, data_json)
#         print(product_id)
#         print('Store id:', data_json['props']['pageProps']['initialData']['data']['contentLayout']['pageMetadata']['location'][
#                 'storeId'])
#         item['upc'] = data_json['props']['pageProps']['initialData']['data']['product']['upc']
#         item['brand'] = data_json['props']['pageProps']['initialData']['data']['product']['brand']
#         item['url'] = 'https://www.walmart.com' + \
#                       data_json['props']['pageProps']['initialData']['data']['contentLayout']['pageMetadata'][
#                           'pageContext']['itemContext']['productUrl']
#         item['title'] = data_json['props']['pageProps']['initialData']['data']['product']['name']
#         image_list = data_json['props']['pageProps']['initialData']['data']['product']['imageInfo']['allImages']
#         item['images'] = [img['url'] for img in image_list]
#         item['storeId'] = \
#             data_json['props']['pageProps']['initialData']['data']['contentLayout']['pageMetadata']['location'][
#                 'storeId']
#         nutritions_check = data_json['props']['pageProps']['initialData']['data']['idml']['nutritionFacts']
#         item['state'] = data_json['props']['pageProps']['initialData']['data']['contentLayout']['pageMetadata']['location'][
#                     'stateOrProvinceCode']
#         item['nutrition'] = nutritions_check
#         ingredients_check = data_json['props']['pageProps']['initialData']['data']['idml']['ingredients']['ingredients']
#         ingredients_content = ingredients_check.get('value')
#         item['ingredients'] = ingredients_content
#         location_info = {
#             'city': data_json['props']['pageProps']['initialData']['data']['contentLayout']['pageMetadata']['location'][
#                 'city'],
#             'state':
#                 data_json['props']['pageProps']['initialData']['data']['contentLayout']['pageMetadata']['location'][
#                     'stateOrProvinceCode'],
#             'zipcode':
#                 data_json['props']['pageProps']['initialData']['data']['contentLayout']['pageMetadata']['location'][
#                     'postalCode'],
#         }
#         item['locationInfo'] = ", ".join(location_info.values())
#         item['descriptionHtml'] = data_json['props']['pageProps']['initialData']['data']['product']['shortDescription']
#         item['description'] = " ".join(Selector(item['descriptionHtml']).xpath('//text()').getall()).strip() if item[
#             'descriptionHtml'] else None
#         item['descriptionFullHtml'] = data_json['props']['pageProps']['initialData']['data']['idml']['longDescription']
#         item['descriptionFull'] = " ".join(Selector(item['descriptionFullHtml']).xpath('//text()').getall()).strip()
#         item['price'] = data_json['props']['pageProps']['initialData']['data']['product']['priceInfo']['currentPrice'][
#             'price'] if data_json['props']['pageProps']['initialData']['data']['product']['priceInfo'][
#             'currentPrice'] else None
#         item['net_weight'] = extract_oz(
#             data_json['props']['pageProps']['initialData']['data']['product']['name']).strip("oz").strip()
#         specifications = data_json['props']['pageProps']['initialData']['data']['idml']['specifications']
#         product_highlights = data_json['props']['pageProps']['initialData']['data']['idml']['productHighlights']
#
#         allergens = 'N/A'
#         try:
#             calories = nutritions_check.get('calorieInfo', {}).get('mainNutrient', {}).get('amount', 'N/A')
#         except Exception:
#             calories = 'N/A'
#         for spec in specifications:
#             if spec.get('name') == 'Food Allergen Statements':
#                 allergens = spec.get('value')
#             if spec.get('name') == 'Calories Per Serving':
#                 calories = spec.get('value')
#                 break
#         pack_size = "1"
#         for highlight in product_highlights:
#             if highlight.get('name') == 'Count ':
#                 pack_size = highlight.get('value')
#                 break
#
#         item['allergens'] = allergens
#         item['calories'] = extract_number(calories)
#         item['pack_size'] = pack_size
#         item['category'] = "Uncategorized"
#
#         return item
#
#     except Exception as e:
#         print(e)
#         if 'initialData' in str(e):
#             return {'error_message': 'Request failed, unable to fetch response'}
#         return {'error_message': 'Internal server error'}

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

'''

def scrape_func(response, product_id, parent_id):
    def safe_get(d, path, default="N/A"):
        try:
            for key in path:
                d = d.get(key, {})
            if isinstance(default, (list, dict)):
                return d if isinstance(d, type(default)) else default
            return d if d else default
        except Exception:
            return default

    try:
        item = {}

        # print(response.text)

        try:
            selector_obj = Selector(response.text)
        except:
            selector_obj = Selector(response)
        data_json = json.loads(selector_obj.xpath('//script[@id="__NEXT_DATA__"]/text()').get())

        # Parse the JSON
        # data_json = json.loads(raw_json)
        save_json(product_id, data_json)

        # Begin extracting structured data
        product_data = safe_get(data_json, ['props', 'pageProps', 'initialData', 'data'], {})

        if not product_data:
            return {'error_message': 'Product data not found'}

        item['upc'] = safe_get(product_data, ['product', 'upc'])
        item['parent_id'] = parent_id
        item['brand'] = safe_get(product_data, ['product', 'brand'])
        item['url'] = 'https://www.walmart.com' + safe_get(
            product_data,
            ['contentLayout', 'pageMetadata', 'pageContext', 'itemContext', 'productUrl'],
            ''
        )
        item['title'] = safe_get(product_data, ['product', 'name'])
        image_list = safe_get(product_data, ['product', 'imageInfo', 'allImages'], [])
        item['images'] = [img.get('url', 'N/A') for img in image_list if isinstance(img, dict)]

        location = safe_get(product_data, ['contentLayout', 'pageMetadata', 'location'], {})

        print("Store ID -------------------------------:", location.get('storeId', 'N/A'))

        item['storeId'] = location.get('storeId', 'N/A')
        item['state'] = location.get('stateOrProvinceCode', 'N/A')
        item['nutrition'] = safe_get(product_data, ['idml', 'nutritionFacts'], {})

        ingredients_data = safe_get(product_data, ['idml', 'ingredients', 'ingredients'], {})
        item['ingredients'] = ingredients_data.get('value', 'N/A')

        location_info = {
            'city': location.get('city', 'N/A'),
            'state': item['state'],
            'zipcode': location.get('postalCode', 'N/A')
        }
        item['locationInfo'] = ", ".join(location_info.values())

        desc_html = safe_get(product_data, ['product', 'shortDescription'], '')
        item['descriptionHtml'] = desc_html
        item['description'] = " ".join(Selector(desc_html).xpath('//text()').getall()).strip() if desc_html else 'N/A'

        full_desc_html = safe_get(product_data, ['idml', 'longDescription'], '')
        item['descriptionFullHtml'] = full_desc_html
        item['descriptionFull'] = " ".join(Selector(full_desc_html).xpath('//text()').getall()).strip() if full_desc_html else 'N/A'

        current_price = safe_get(product_data, ['product', 'priceInfo', 'currentPrice'], {})
        item['price'] = safe_float(current_price.get('price'))

        item['net_weight'] = extract_oz(item['title']).strip("oz").strip() if item['title'] else 'N/A'

        specifications = safe_get(product_data, ['idml', 'specifications'], [])
        product_highlights = safe_get(product_data, ['idml', 'productHighlights'], [])

        item['allergens'] = 'N/A'
        item['calories'] = 'N/A'
        for spec in specifications:
            if spec.get('name') == 'Food Allergen Statements':
                item['allergens'] = spec.get('value', 'N/A')
            elif spec.get('name') == 'Calories Per Serving':
                item['calories'] = extract_number(spec.get('value', 'N/A'))

        item['pack_size'] = '1'
        for highlight in product_highlights:
            if highlight.get('name') == 'Count ':
                item['pack_size'] = highlight.get('value', '1')
                break

        item['category'] = "Uncategorized"

        return item

    except Exception as e:
        print(f"[ERROR] Exception while parsing → {e}")
        return {'error_message': 'Internal server error'}
'''

'''
def scrape_func(response, product_id, parent_id):
    def safe_get(d, path, default="N/A"):
        try:
            for key in path:
                d = d.get(key, {})
            if isinstance(default, (list, dict)):
                return d if isinstance(d, type(default)) else default
            return d if d else default
        except Exception:
            return default

    try:
        item = {}

        # print(response.text)

        try:
            selector_obj = Selector(response.text)
        except:
            selector_obj = Selector(response)
        iframe_info = selector_obj.xpath('//div[@data-testid="about-the-brand"]//iframe[@id="marketing-description-frame"]/@*')
        print('iframe info', iframe_info)
        data_json = json.loads(selector_obj.xpath('//script[@id="__NEXT_DATA__"]/text()').get())

        # Parse the JSON
        # data_json = json.loads(raw_json)
        save_json(product_id, data_json)

        # Begin extracting structured data
        product_data = safe_get(data_json, ['props', 'pageProps', 'initialData', 'data'], {})

        if not product_data:
            return {'error_message': 'Product data not found'}

        item['upc'] = safe_get(product_data, ['product', 'upc'])
        item['parent_id'] = parent_id
        item['brand'] = safe_get(product_data, ['product', 'brand'])
        item['url'] = 'https://www.walmart.com' + safe_get(
            product_data,
            ['contentLayout', 'pageMetadata', 'pageContext', 'itemContext', 'productUrl'],
            ''
        )
        item['title'] = safe_get(product_data, ['product', 'name'])
        image_list = safe_get(product_data, ['product', 'imageInfo', 'allImages'], [])
        item['images'] = [img.get('url', 'N/A') for img in image_list if isinstance(img, dict)]

        # ------------------- new req ------------------------------------------------------

        item['videos'] = safe_get(product_data, ['idml', 'videos'])
        item['specification'] = safe_get(product_data, ['idml', 'specifications'])
        item['directions'] = safe_get(product_data, ['idml', 'directions'])
        item['warnings'] = safe_get(product_data, ['idml', 'warnings'])
        variants_map = safe_get(product_data, ['product', 'variantsMap'])
        variants_urls = []

        for variant_id, variant_data in variants_map.items():
            url = variant_data.get("productUrl")
            if url:
                # Convert to full URL
                full_url = "https://www.walmart.com" + url
                variants_urls.append(full_url)
        print("variants_urls--------", variants_urls)
        item['variants_urls'] = variants_urls

        # ---------------------------------------------------------------------------------------

        location = safe_get(product_data, ['contentLayout', 'pageMetadata', 'location'], {})

        # print("Store ID -------------------------------:", location.get('storeId', 'N/A'))
        print("Store ID -------------------------------:", store_id)

        item['storeId'] = location.get('storeId', 'N/A')
        item['state'] = location.get('stateOrProvinceCode', 'N/A')
        item['nutrition'] = safe_get(product_data, ['idml', 'nutritionFacts'], {})

        ingredients_data = safe_get(product_data, ['idml', 'ingredients', 'ingredients'], {})
        item['ingredients'] = ingredients_data.get('value', 'N/A')

        location_info = {
            'city': location.get('city', 'N/A'),
            'state': item['state'],
            'zipcode': location.get('postalCode', 'N/A')
        }
        item['locationInfo'] = ", ".join(location_info.values())

        desc_html = safe_get(product_data, ['product', 'shortDescription'], '')
        item['descriptionHtml'] = desc_html
        item['description'] = " ".join(Selector(desc_html).xpath('//text()').getall()).strip() if desc_html else 'N/A'

        full_desc_html = safe_get(product_data, ['idml', 'longDescription'], '')
        item['descriptionFullHtml'] = full_desc_html
        item['descriptionFull'] = " ".join(Selector(full_desc_html).xpath('//text()').getall()).strip() if full_desc_html else 'N/A'

        current_price = safe_get(product_data, ['product', 'priceInfo', 'currentPrice'], {})
        item['price'] = safe_float(current_price.get('price'))

        item['net_weight'] = extract_oz(item['title']).strip("oz").strip() if item['title'] else 'N/A'

        specifications = safe_get(product_data, ['idml', 'specifications'], [])
        product_highlights = safe_get(product_data, ['idml', 'productHighlights'], [])

        item['allergens'] = 'N/A'
        item['calories'] = 'N/A'
        for spec in specifications:
            if spec.get('name') == 'Food Allergen Statements':
                item['allergens'] = spec.get('value', 'N/A')
            elif spec.get('name') == 'Calories Per Serving':
                item['calories'] = extract_number(spec.get('value', 'N/A'))

        item['pack_size'] = '1'
        for highlight in product_highlights:
            if highlight.get('name') == 'Count ':
                item['pack_size'] = highlight.get('value', '1')
                break

        item['category'] = "Uncategorized"

        return item

    except Exception as e:
        print(f"[ERROR] Exception while parsing → {e}")
        return {'error_message': 'Internal server error'}
'''

import json
from parsel import Selector


def scrape_func(response, product_id, parent_id):
    def safe_get(d, path, default="N/A"):
        """Safely get nested dict values."""
        try:
            for key in path:
                d = d.get(key, {})
            if isinstance(default, (list, dict)):
                return d if isinstance(d, type(default)) else default
            return d if d else default
        except Exception:
            return default

    def safe_float(val, default=0.0):
        try:
            return float(val)
        except:
            return default

    def extract_number(s):
        import re
        try:
            return float(re.findall(r"[\d\.]+", str(s))[0])
        except:
            return 0

    def clean_html_to_text(html):
        """Convert HTML to clean text only if HTML-like."""
        if not html or not isinstance(html, str):
            return "N/A"
        if "<" not in html or ">" not in html:  # NOT HTML → just return as-is
            return html.strip()
        try:
            sel = Selector(html)
            return " ".join(sel.xpath("//text()").getall()).strip()
        except:
            return html.strip()

    def extract_oz(title):
        import re
        try:
            oz = re.findall(r"(\d+\.?\d*)\s*oz", str(title), re.IGNORECASE)
            return oz[0] if oz else 'N/A'
        except:
            return 'N/A'

    try:
        item = {}

        # Parse response text
        raw_text = response.text if hasattr(response, 'text') else response
        selector_obj = Selector(raw_text)

        # Load JSON from __NEXT_DATA__
        data_json = {}
        try:
            data_json = json.loads(selector_obj.xpath('//script[@id="__NEXT_DATA__"]/text()').get() or '{}')
        except Exception as e:
            print(f"[WARN] Could not parse __NEXT_DATA__: {e}")

        # Save raw JSON if needed
        save_json(product_id, data_json)  # Uncomment if you have save_json

        product_data = safe_get(data_json, ['props', 'pageProps', 'initialData', 'data'], {})
        if not product_data:
            return {'error_message': 'Product data not found'}

        # Basic product info
        item['upc'] = safe_get(product_data, ['product', 'upc'])
        item['breadcrumbs'] = safe_get(product_data, ['seoItemMetaData', 'breadCrumbs'])
        item['parent_id'] = parent_id
        item['brand'] = safe_get(product_data, ['product', 'brand'])
        item['url'] = 'https://www.walmart.com' + safe_get(
            product_data,
            ['contentLayout', 'pageMetadata', 'pageContext', 'itemContext', 'productUrl'],
            ''
        )
        item['title'] = safe_get(product_data, ['product', 'name'])

        # Images
        image_list = safe_get(product_data, ['product', 'imageInfo', 'allImages'], [])
        if isinstance(image_list, list):
            item['images'] = [img.get('url', 'N/A') for img in image_list if isinstance(img, dict)]
        else:
            item['images'] = []

        # Videos
        videos_data = safe_get(product_data, ['idml', 'videos'], [])
        item['videos'] = []
        if isinstance(videos_data, list):
            for vid in videos_data:
                if isinstance(vid, dict):
                    versions = vid.get('versions', {})
                    item['videos'].append(versions.get('large', 'N/A'))

        # Specifications
        item['specification'] = safe_get(product_data, ['idml', 'specifications'], [])
        item['directions'] = safe_get(product_data, ['idml', 'directions'], 'N/A')
        item['warnings'] = safe_get(product_data, ['idml', 'warnings'], 'N/A')
        item['nutrition'] = safe_get(product_data, ['idml', 'nutritionFacts'], {})
        ingredients_data = safe_get(product_data, ['idml', 'ingredients', 'ingredients'], {})
        item['ingredients'] = ingredients_data.get('value', 'N/A') if isinstance(ingredients_data, dict) else 'N/A'

        # Variants
        variants_map = safe_get(product_data, ['product', 'variantsMap'], {})
        variants_urls = []
        if isinstance(variants_map, dict):
            for variant_id, variant_data in variants_map.items():
                if isinstance(variant_data, dict):
                    url = variant_data.get("productUrl")
                    if url:
                        full_url = "https://www.walmart.com" + url
                        variants_urls.append(full_url)
        item['variants_urls'] = variants_urls

        # Location info
        location = safe_get(product_data, ['contentLayout', 'pageMetadata', 'location'], {})
        item['storeId'] = location.get('storeId', 'N/A')
        item['state'] = location.get('stateOrProvinceCode', 'N/A')
        item['locationInfo'] = ", ".join([
            location.get('city', 'N/A'),
            location.get('stateOrProvinceCode', 'N/A'),
            location.get('postalCode', 'N/A')
        ])

        # Descriptions
        desc_html = safe_get(product_data, ['idml', 'shortDescription'], "")
        item['descriptionHtml'] = desc_html
        # item['description'] = clean_html_to_text(desc_html)
        item['description'] = desc_html

        full_desc_html = safe_get(product_data, ['idml', 'longDescription'], "")
        item['descriptionFullHtml'] = full_desc_html
        # item['descriptionFull'] = clean_html_to_text(full_desc_html)
        item['descriptionFull'] = full_desc_html
        # Price
        current_price = safe_get(product_data, ['product', 'priceInfo', 'currentPrice'], {})
        item['price'] = safe_float(current_price.get('price'))

        # Net weight
        item['net_weight'] = extract_oz(item['title']).strip("oz").strip() if item['title'] else 'N/A'

        # Allergens and calories
        item['allergens'] = 'N/A'
        item['calories'] = 'N/A'
        specifications = safe_get(product_data, ['idml', 'specifications'], [])
        product_highlights = safe_get(product_data, ['idml', 'productHighlights'], [])
        for spec in specifications:
            if spec.get('name') == 'Food Allergen Statements':
                item['allergens'] = spec.get('value', 'N/A')
            elif spec.get('name') == 'Calories Per Serving':
                item['calories'] = extract_number(spec.get('value', 'N/A'))

        # Pack size
        item['pack_size'] = '1'
        for highlight in product_highlights:
            if highlight.get('name') == 'Count ':
                item['pack_size'] = highlight.get('value', '1')
                break

        item['category'] = "Uncategorized"

        return item

    except Exception as e:
        print(f"[ERROR] Exception while parsing → {e}")
        return {'error_message': 'Internal server error'}

# create_products_table()
# store_urls = get_store_urls_from_db()
# for store in store_urls:
#     store_id = store['storeid']
#     store_url = store['url']
#     print(store_id)
#     store_cookie = get_store_cookies(store_url)
#
#     product_url = 'https://www.walmart.com/ip/Smucker-s-Uncrustables-Peanut-Butter-Grape-Jelly-Sandwiches-10-Count-2-Oz-Each-Frozen/10849748?classType=REGULAR&athbdg=L1600'
#     product_id = extract_product_id(product_url)
#
#     # response = requests.get(product_url, headers=headers, cookies=store_cookie)
#     response = requests.get(product_url, proxies=proxies, verify=False, headers=headers, cookies=store_cookie)
#     save_raw_html(product_id, response.text)
#
#     if response.status_code == 200:
#         item = scrape_func(response, product_id)
#         if item:
#             success = insert_product_data(item)
    #         if success:
    #             update_product_status(product_url, 'done')
    #         else:
    #             update_product_status(product_url, 'failed')
    #     else:
    #         update_product_status(product_url, 'failed')
    # else:
    #     print(f"[ERROR] Failed to fetch product page (Status code: {response.status_code})")
    #     update_product_status(product_url, 'failed')




# with open(f'product_res.json', 'w', encoding='utf-8') as f:
#     json.dump(result, f, indent=4, ensure_ascii=False)
