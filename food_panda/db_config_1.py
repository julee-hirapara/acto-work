import traceback
import pymysql
import os
from datetime import datetime
import sys
sys.stdout.reconfigure(encoding='utf-8')

current_month = datetime.now().strftime("%m%Y")

project_name = "food_panda"

base_directory = f"D:\\Julee\\"
# base_directory = f"D:\\"

# file_server_path = f"Z:\\Team_Neela\\Projects\\plaund-6084-hotel-pricing-data-from-6-platforms-poc\\agoda\\"
# file_server_PDP_PAGESAVE = f'{file_server_path}Pagesave\\{current_date}\\PDP'
# file_server_PDP_json_PAGESAVE = f'{file_server_path}Pagesave\\{current_date}\\PDP_JSON'
# os.makedirs(file_server_PDP_PAGESAVE, exist_ok=True)
# os.makedirs(file_server_PDP_json_PAGESAVE, exist_ok=True)
# output_file_path = f'{file_server_path}file'
# os.makedirs(output_file_path, exist_ok=True)


# === PATH CONFIG ===
current_date = datetime.now().strftime("%m_%Y")
PAGESAVE_PATH = f"{base_directory}PAGESAVES\\{project_name}\\{current_date}\\"
os.makedirs(PAGESAVE_PATH, exist_ok=True)
RESULT_PATH = f"{base_directory}FILES\\{project_name}\\{current_date}\\"
os.makedirs(RESULT_PATH, exist_ok=True)
PDP_PAGESAVE = f'{PAGESAVE_PATH}PDP'
PL_PAGESAVE = f'{PAGESAVE_PATH}PL'
os.makedirs(PL_PAGESAVE, exist_ok=True)
os.makedirs(PDP_PAGESAVE, exist_ok=True)


db_name = f"food_panda"
link_table = f"links_{current_month}"
data_table = f"data_{current_month}"



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
    cursor = None

    print("Starting database and table creation process...")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # --- Create Database ---
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE `{db_name}`;")
        print(f"Database `{db_name}` created or already exists.")

        create_category_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{link_table}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                link TEXT,
                slug VARCHAR(500) NOT NULL UNIQUE,
                code VARCHAR(50),
                name VARCHAR(255) NOT NULL UNIQUE,
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        cursor.execute(create_category_table_query)
        conn.commit()
        print(f"Table `{link_table}` checked/created successfully.")
        data_table_query = f"""CREATE TABLE IF NOT EXISTS `{data_table}` (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                url TEXT,
                restaurant_name VARCHAR(255),
                restaurant_image TEXT,
                cuisines TEXT,
                currency VARCHAR(20),
                country_code VARCHAR(20),
                opening_hours TEXT,
                phone_number VARCHAR(100),
                address TEXT,
                post_code VARCHAR(50),
                city VARCHAR(255),
                latitude VARCHAR(50),
                longitude VARCHAR(50),
                rating VARCHAR(20),
                rating_count VARCHAR(20),
                brand VARCHAR(255),
                minimum_order_value VARCHAR(50),
                category_name VARCHAR(255),
                menu_name VARCHAR(255),
                price VARCHAR(15),
                mrp VARCHAR(15),
                discount VARCHAR(15),
                menu_image TEXT,
                description TEXT,
                tags TEXT,
                hash_id VARCHAR(150),
                extra_data TEXT,
                scraped_date DATE,  
                scraped_time DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_menu (
                    url(255),
                    menu_name(255),
                    category_name(255)
                )
            );
            """
        cursor.execute(data_table_query)
        conn.commit()
        print(f"Table `{data_table}` checked/created successfully.")

        # create_product_link_table_query = f"""
        #     CREATE TABLE IF NOT EXISTS `{product_link_table}` (
        #         id INT AUTO_INCREMENT PRIMARY KEY,
        #         item_code VARCHAR(255),
        #         images TEXT,
        #         product_name VARCHAR(255),
        #         brand_name VARCHAR(255),
        #         weight VARCHAR(255),
        #         net_quantity VARCHAR(255),
        #         country_of_origin VARCHAR(255),
        #         store_id VARCHAR(100),
        #         mrp VARCHAR(15),
        #         rrp VARCHAR(15),
        #         discount VARCHAR(15),
        #         city VARCHAR(100),
        #         pincode VARCHAR(10),
        #         category_name VARCHAR(255),
        #         cat_slug VARCHAR(255),
        #         state_code VARCHAR(10),
        #         state VARCHAR(255),
        #         type VARCHAR(255),
        #         product_slug VARCHAR(500) NOT NULL,
        #         uid VARCHAR(100),
        #         in_stock VARCHAR(100),
        #         minimum_quantity VARCHAR(100),
        #         maximum_quantity VARCHAR(100),
        #         hash_key VARCHAR(255) NOT NULL UNIQUE,
        #         json_dict text,
        #         status VARCHAR(50),
        #         pagesave TEXT,
        #         quantity_price_tiers TEXT,
        #         price_pagesave TEXT,
        #         pdp_data TEXT,
        #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        #     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        #     """
        # cursor.execute(create_product_link_table_query)
        # conn.commit()
        # print(f"Table `{product_link_table}` checked/created successfully.")

        # create_data_table_query = f"""
        #     CREATE TABLE IF NOT EXISTS `{data_table}` (
        #         id INT AUTO_INCREMENT PRIMARY KEY,
        #         website VARCHAR(255),
        #         pid VARCHAR(255),
        #         name VARCHAR(500),
        #         short_description TEXT,
        #         description LONGTEXT,
        #         category VARCHAR(500),
        #         image_url TEXT,
        #         price DECIMAL(10,2),
        #         price_currency VARCHAR(50),
        #         sale_price DECIMAL(10,2),
        #         final_price DECIMAL(10,2),
        #         discount VARCHAR(50),
        #         is_on_sale VARCHAR(10),
        #         is_in_stock VARCHAR(10),
        #         keywords TEXT,
        #         brand VARCHAR(255),
        #         manufacturer VARCHAR(255),
        #         mpn VARCHAR(255),
        #         upc_ean VARCHAR(255),
        #         sku VARCHAR(255) NOT NULL UNIQUE,
        #         colour VARCHAR(150),
        #         gender VARCHAR(50),
        #         size VARCHAR(255),
        #         variant_price DECIMAL(10,2),
        #         alternate_image_urls LONGTEXT,
        #         link_url VARCHAR(600),
        #         num_ratings INT,
        #         avg_ratings DECIMAL(5,2),
        #         hash_id VARCHAR(255),
        #         main_url VARCHAR(600),
        #         size_type VARCHAR(255),
        #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        #     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        # """
        # cursor.execute(create_data_table_query)
        # conn.commit()
        # print(f"Table `{data_table}` checked/created successfully.")
        print("All database setup operations completed successfully!")

    except Exception as e:
        print("Error occurred during database setup!")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print("Traceback:")
        print(traceback.format_exc())

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("Database connection closed.")


# # === MAIN EXECUTION ===
if __name__ == '__main__':
    create_table()
