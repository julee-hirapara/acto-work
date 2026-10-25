import traceback
import pymysql
import os
from datetime import datetime
import sys

sys.stdout.reconfigure(encoding='utf-8')

proxy_token = "***HIDDEN***"

current_month = datetime.now().strftime("%m%Y")

project_name = "pet_supermarket"

# === PATH CONFIG ===
# current_date = datetime.now().strftime("%m_%Y")
PAGESAVE_PATH = f"D:\\Julee\\PAGESAVES\\{project_name}\\{current_month}\\"
os.makedirs(PAGESAVE_PATH, exist_ok=True)
RESULT_PATH = f"D:\\Julee\\FILES\\{project_name}\\{current_month}\\"
os.makedirs(RESULT_PATH, exist_ok=True)
PDP_PAGESAVE = f'{PAGESAVE_PATH}PDP'
PL_PAGESAVE = f'{PAGESAVE_PATH}PL'
variation_folder = os.path.join(PDP_PAGESAVE, "variation_pagesave")
review_folder = os.path.join(PDP_PAGESAVE, "review_pagesave")
os.makedirs(variation_folder, exist_ok=True)
os.makedirs(review_folder, exist_ok=True)
os.makedirs(PL_PAGESAVE, exist_ok=True)
os.makedirs(PDP_PAGESAVE, exist_ok=True)


today_date = datetime.now().strftime("%d%m%Y")
db_name = f"pet_supermarket"
current_month = datetime.now().strftime("%m%Y")
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

        # --- Create links table ---
        create_input_data_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{link_table}` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            url VARCHAR(500) NOT NULL UNIQUE,
            status VARCHAR(50) DEFAULT 'pending',
            hash_key VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_input_data_table_query)
        conn.commit()
        print(f"Table `{link_table}` checked/created successfully.")

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
                reviews LONGTEXT DEFAULT NULL,
                hash_id VARCHAR(255),
                main_url VARCHAR(600),
                size_type VARCHAR(255),
                coupons_and_offers LONGTEXT DEFAULT NULL,
                delivery_ETA TEXT DEFAULT NULL,
                shipping_cost DECIMAL(5,2) DEFAULT NULL,
                return_fee DECIMAL(5,2) DEFAULT NULL,
                tags VARCHAR(255) DEFAULT NULL, 
                review_summary LONGTEXT DEFAULT NULL,	
                return_policy LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_data_table_query)
        conn.commit()
        print(f"Table `{data_table}` checked/created successfully.")
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
