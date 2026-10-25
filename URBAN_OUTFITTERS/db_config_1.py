import json
import traceback
import pymysql
import os
from datetime import datetime
p_token = "***HIDDEN***"
# proxy_token = "***HIDDEN***"
proxy_token = "***HIDDEN***"

# current_date = datetime.now().strftime("%Y_%m_%d")
# === PATH CONFIG ===
# PAGESAVE_PATH = "D:\\Julee\\PAGESAVES\\URBAN_OUTFITTERS\\"
# RESULT_PATH = "D:\\Julee\\FILES\\URBAN_OUTFITTERS\\"

# for_rear_path = "D:\\PAGESAVES\\URBAN_OUTFITTERS\\PAGESAVES\\URBAN_OUTFITTERS\\"
# PAGESAVE_PATH = f"D:\\PAGESAVES\\URBAN_OUTFITTERS\\{current_date}\\"
current_date = datetime.now().strftime("%m_%Y")
base_path = f'Z:\\Team_Neela\\Hiren\\Pagesaves'
base_path_result = f'Z:\\Team_Neela\\Hiren\\Files'
# base_path = f"D:\\Julee\\PAGESAVES"
# current_date = "06_2026"
# PAGESAVE_PATH = f"D:\\Julee\\PAGESAVES\\URBAN_OUTFITTERS\\{current_date}\\"
PAGESAVE_PATH = f"{base_path}\\URBAN_OUTFITTERS\\{current_date}\\"
os.makedirs(PAGESAVE_PATH, exist_ok=True)

RESULT_PATH = f"{base_path_result}\\URBAN_OUTFITS\\{current_date}\\"
os.makedirs(RESULT_PATH, exist_ok=True)

LINK_PAGESAVE = f'{PAGESAVE_PATH}links'
CAT_LINK_PAGESAVE = f'{PAGESAVE_PATH}cat_links'
DATA_PAGESAVE = f'{PAGESAVE_PATH}data'
SIZE_PAGESAVE = f'{PAGESAVE_PATH}size_chart'
REVIEW_PAGESAVE = f'{PAGESAVE_PATH}review'
RESULT_PAGE = f'{RESULT_PATH}results'
# LOG_FOLDER = f'{PAGESAVE_PATH}log'

os.makedirs(LINK_PAGESAVE, exist_ok=True)
os.makedirs(SIZE_PAGESAVE, exist_ok=True)
os.makedirs(REVIEW_PAGESAVE, exist_ok=True)
os.makedirs(CAT_LINK_PAGESAVE, exist_ok=True)
os.makedirs(DATA_PAGESAVE, exist_ok=True)
os.makedirs(RESULT_PAGE, exist_ok=True)
# os.makedirs(LOG_FOLDER, exist_ok=True)


today_date = datetime.now().strftime("%d%m%Y")
db_name = f"urban_outfitters"
# current_month = "062026"
current_month = datetime.now().strftime("%m%Y")
cat_links_table = f"cat_links_{current_month}"
link_table = f"links_{current_month}"
data_table = f"data_{current_month}"

# === DATABASE CONNECTION ===
def get_db_connection(db_name=None):
    if not db_name:
        db_name = db_name
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

        # --- Create links table ---
        create_link_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{cat_links_table}` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url VARCHAR(500) NOT NULL UNIQUE,
            displayname VARCHAR(255),
            slug TEXT,
            type VARCHAR(50),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_link_table_query)
        conn.commit()
        print("Table `cat_links` checked/created successfully.")

        # --- Create links table ---
        create_link_table_query = f"""
                CREATE TABLE IF NOT EXISTS `{link_table}` (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    url VARCHAR(500) NOT NULL UNIQUE,
                    name VARCHAR(255),
                    category TEXT,
                    slug VARCHAR(255),
                    product_id VARCHAR(255),
                    brand VARCHAR(255),
                    avg_rating DECIMAL(2,1), 
                    review_count INT,
                    hash_id VARCHAR(255),
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """
        cursor.execute(create_link_table_query)
        conn.commit()
        print("Table `links` checked/created successfully.")

        # --- Create restaurant_data table ---
        create_data_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{data_table}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                website VARCHAR(255),
                pid VARCHAR(255),
                name VARCHAR(500),
                short_description TEXT,
                description LONGTEXT,
                category VARCHAR(500),
                image_url TEXT,
                price DECIMAL(10,2),
                price_currency VARCHAR(50),
                sale_price DECIMAL(10,2),
                final_price DECIMAL(10,2),
                discount VARCHAR(50),
                is_on_sale VARCHAR(10),
                is_in_stock VARCHAR(10),
                keywords TEXT,
                brand VARCHAR(255),
                manufacturer VARCHAR(255),
                mpn VARCHAR(255),
                upc_ean VARCHAR(255),
                sku VARCHAR(255) NOT NULL UNIQUE,
                colour VARCHAR(150),
                gender VARCHAR(50),
                size VARCHAR(255),
                variant_price DECIMAL(10,2),
                alternate_image_urls LONGTEXT,
                link_url VARCHAR(600),
                num_ratings INT,
                avg_ratings DECIMAL(5,2),
                hash_id VARCHAR(255),
                main_url VARCHAR(600),
                size_type VARCHAR(255),
                fit_type VARCHAR(255),
                status VARCHAR(50),
                size_chart LONGTEXT,
                review_text LONGTEXT,
                size_chart_present VARCHAR(100),
                size_chart_response LONGTEXT,
                coupons_and_offers LONGTEXT DEFAULT NULL,
                delivery_ETA LONGTEXT DEFAULT NULL,
                shipping_cost LONGTEXT DEFAULT NULL,
                return_fee DECIMAL(5,2) DEFAULT NULL,
                tags VARCHAR(255) DEFAULT NULL, 
                review_summary LONGTEXT DEFAULT NULL,	
                return_policy LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_data_table_query)
        conn.commit()
        print("Table `data` checked/created successfully.")
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
