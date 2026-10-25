import traceback

import pymysql
import gzip

db_name = "walmart"
token = "***HIDDEN***"
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

pincode = "78064"
page_save_path = rf"D:\PAGESAVES\walmart\{pincode}"

link_table = f"pl_data"
# link_table = f"pl_data_{pincode}"
# data_table = f"pdp_data_{pincode}"
data_table = f"pdp_data"

def create_tables():
    conn = None
    cursor = None

    print("Starting database and table creation process...")

    try:
        con = get_db_connection()
        cur = con.cursor()

        # --- Create Database ---
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cur.execute(f"USE `{db_name}`;")
        print(f"Database `{db_name}` created or already exists.")

        cur.execute(F"""
           CREATE TABLE IF NOT EXISTS {link_table} (
           brand VARCHAR(255),
           product_id VARCHAR(255) NOT NULL UNIQUE,
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
           search_keyword VARCHAR(255) 
           );
       """)
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {data_table} (
            brand VARCHAR(100),
            product_id VARCHAR(50) NOT NULL UNIQUE,
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
            product_description TEXT
        );
        """)
        con.commit()

    except Exception as e:
        print("Error occurred during database setup!")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print("Traceback:")
        print(traceback.format_exc())

    finally:
        if cur:
            cur.close()
        if con:
            con.close()
        print("Database connection closed.")

def save_page(file_name, response):
    with gzip.open(file_name, 'wb') as f:
        f.write(response.encode('utf-8'))

def read_page(file_name):
    with gzip.open(file_name, 'rb') as f:
        return f.read().decode('utf-8')


if __name__ == '__main__':
    create_tables()