import gzip
import traceback

# import mysql.connector
import pymysql
from glom import glom
import os

pincode = '78064'
PAGESAVE_PATH = rf"D:\\julee\\PAGESAVES\\walmart\\{pincode}\\"
CAT_PAGESAVE = f'{PAGESAVE_PATH}category_page'
# PL_PAGESAVE = f'{PAGESAVE_PATH}PL'
os.makedirs(CAT_PAGESAVE, exist_ok=True)
# os.makedirs(PDP_PAGESAVE, exist_ok=True)

db_name = "walmart_category"
input_table = "walmart_category_master"
data_table = "pdp_data"

# === DATABASE CONNECTION ===
def get_db_connection(db_name=None):
    conn = pymysql.connect(
        # host="***HIDDEN***",
        host="localhost",
        user="root",
        password="***HIDDEN***",
        database=db_name,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

def create_table():
    conn = None
    cur = None

    print("Starting database and table creation process...")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # --- Create Database ---
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cur.execute(f"USE `{db_name}`;")
        print(f"Database `{db_name}` created or already exists.")

        create_input_table_query = f"""CREATE TABLE IF NOT EXISTS {input_table} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        main_cat VARCHAR(255),
                        sub_cat VARCHAR(255),        
                        item_count VARCHAR(255),            
                        category_name VARCHAR(500),           
                        pl_url TEXT,
                        sub_category_url TEXT,           
                        final_url TEXT,           
                        url_type ENUM('browse', 'cp', 'shop', 'other') DEFAULT 'other', 
                        status VARCHAR(255),          
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,           
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,           
                        UNIQUE KEY unique_final_url (final_url(255))
                    ); """
        cur.execute(create_input_table_query)
        create_link_table = f"""
               CREATE TABLE IF NOT EXISTS {link_table} (
               brand VARCHAR(255),
               product_id VARCHAR(255) UNIQUE,
               product_url VARCHAR(700),
               product_name TEXT,
               sponsored VARCHAR(50),
               page_num VARCHAR(100),
               num_review VARCHAR(255),
               avg_rating VARCHAR(255),
               price_discount VARCHAR(255),
               product_price VARCHAR(255),
               product_mrp VARCHAR(255),
               price_per_unit VARCHAR(255),
               main_image TEXT,
               category_name VARCHAR(255),
               pl_url TEXT,
               cat_id VARCHAR(500)
               );
           """
        cur.execute(create_link_table)
        conn.commit()

        query = """
            CREATE TABLE IF NOT EXISTS category_links (
                id INT AUTO_INCREMENT PRIMARY KEY,
                main_url VARCHAR(255) NOT NULL,
                main_category VARCHAR(500),
                subcategory_url TEXT,
                category_id VARCHAR(255) NOT NULL ,
                title Text,
                total_count VARCHAR(15),
                type varchar(255),
                sub_cat_count VARCHAR(15),
                status ENUM('pending', 'completed', 'failed') ,
                UNIQUE KEY unique_product (subcategory_url(255),main_url(255),category_id(255))
            )
            """
        cur.execute(query)
        conn.commit()
        cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {data_table} (
                    brand VARCHAR(100),
                    product_id VARCHAR(50) UNIQUE,
                    product_name TEXT,
                    sponsored VARCHAR(50),
                    page_num VARCHAR(50),
                    num_review VARCHAR(100),
                    avg_rating VARCHAR(100),
                    price_discount VARCHAR(50),
                    product_price VARCHAR(100),
                    product_mrp VARCHAR(100),
                    price_per_unit VARCHAR(100),
                    main_image TEXT,
                    source_url TEXT,
                    location VARCHAR(100),

                    product_pdf_urls JSON,
                    product_image_urls JSON,
                    product_specifications JSON,
                    product_description TEXT,

                    -- ✅ NEW CHECKLIST FIELDS ADDED
                    breadcrumbs TEXT,
                    store_id VARCHAR(100),
                    ingredients TEXT,
                    allergens TEXT,
                    net_weight VARCHAR(255),
                    calories VARCHAR(255),
                    pack_size VARCHAR(255),
                    pickup_available VARCHAR(255),
                    nutritional_data JSON,
                    category_name VARCHAR(255)
                );
                """)
        conn.commit()
        cur.close()
        conn.close()

        print("Table created successfully")
    except Exception as e:
        print("Error occurred during database setup!")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print("Traceback:")
        print(traceback.format_exc())

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        print("Database connection closed.")

# def insert_category_data(main_url, main_category, subcategory_url, category_id, title=None, type=None, total_count=None, status='pending'):
#     try:
#         conn = get_db_connection(db_name)
#         cursor = conn.cursor()
#
#         query = """
#         INSERT INTO category_links
#         (main_url, main_category, subcategory_url,category_id, title, type, total_count, status)
#         VALUES (%s, %s, %s, %s, %s,%s, %s, %s)
#         """
#
#         values = (main_url, main_category ,subcategory_url, category_id, title, type, total_count, status)
#         cursor.execute(query, values)
#         conn.commit()
#
#         print("Data inserted successfully")
#
#     except pymysql.MySQLError as e:
#         print(f"Error: {e}")
#
#     finally:
#         conn.close()
#

# def extract_data(json_data, page_no, category_name):
#     scraped_data = []
#     if not json_data:
#         return scraped_data
#     try:
#         item_stacks = glom(
#             json_data,
#             "data.search.searchResult.itemStacks",
#             default=[]
#         )
#         for products in item_stacks:
#             for product in products.get('itemsV2', []):
#                 if "Product" not in product.get('__typename', ''):
#                     continue
#                 try:
#                     item = {}
#                     price = glom(product, "priceInfo.currentPrice.price", default="N/A")
#                     mrp = glom(product, "priceInfo.listPrice.price", default="N/A")
#                     if mrp == "N/A":
#                         mrp = price
#                     price_discount = "N/A"
#                     if isinstance(price, (int, float)) and isinstance(mrp, (int, float)):
#                         if mrp > price:
#                             price_discount = round(mrp - price, 2)
#                     item['main_image'] = glom(
#                         product,
#                         "imageInfo.thumbnailUrl",
#                         default="N/A"
#                     )
#                     if "jpeg?" in str(item['main_image']):
#                         item['main_image'] = (
#                             item['main_image'].split("jpeg?")[0] + "jpeg"
#                         )
#                     item['product_name'] = product.get('name', "N/A")
#                     item['product_price'] = price
#                     item['price_per_unit'] = glom(
#                         product,
#                         "priceInfo.unitPrice.priceString",
#                         default="N/A"
#                     )
#                     item['price_discount'] = price_discount
#                     item['avg_rating'] = product.get("averageRating", "N/A")
#                     item['num_review'] = product.get("numberOfReviews", "N/A")
#                     item['page_num'] = page_no
#                     item['sponsored'] = (
#                         "Yes" if product.get("sponsoredProduct") else "No"
#                     )
#                     item['product_url'] = (
#                         f"https://www.walmart.com{product['canonicalUrl']}"
#                     )
#                     item['product_id'] = (
#                         product['canonicalUrl']
#                         .split("?")[0]
#                         .split("/")[-1]
#                         .strip()
#                     )
#                     item['product_mrp'] = mrp
#                     item['category_name'] = category_name
#                     scraped_data.append(item)
#                 except Exception as e:
#                     print(e)
#     except Exception as e:
#         print(e)
#     return scraped_data


# def get_db_connection():
#     conn = pymysql.connect(
#     host="localhost",
#     user="root",
#     password="***HIDDEN***",
#     database="walmart_category",
#     charset="utf8mb4"
#     )
#     return conn

link_table = "links"
def save_data_db(items):
    try:
        con = get_db_connection(db_name)
        cur = con.cursor()

        for item in items:
            for k, v in item.items():
                if v in [None, "", [], {}]:
                    item[k] = "N/A"

            cols = ", ".join(item.keys()).strip(', ')
            values = tuple(item.values())

            try:
                insert_active = f"""INSERT IGNORE INTO {link_table} ({cols}) VALUES {values}"""
                cur.execute(insert_active)
                con.commit()
                print('inserted', item['product_url'])

            except Exception as e:
                print(e)

    except Exception as e:
        print(e)

    finally:
        cur.close()
        con.close()


# def main():
#     category_name = "soda_pop"
#     page_no = 1
#     while True:
#         print(f"sending request on page: {page_no}")
#         json_data = fetch_response(
#             page_no=page_no,
#             category_name=category_name
#         )
#         if not json_data:
#             break
#         items = extract_data(
#             json_data=json_data,
#             page_no=page_no,
#             category_name=category_name
#         )
#
#         if not items:
#             print("No more products found")
#             break
#         save_data_db(items)
#         print(f"saved page: {page_no} | items: {len(items)}")
#         page_no += 1

def save_page(file_name, response):
    with gzip.open(file_name, 'wb') as f:
        f.write(response.encode('utf-8'))

def read_page(file_name):
    with gzip.open(file_name, 'rb') as f:
        return f.read().decode('utf-8')


if __name__ == '__main__':
    create_table()