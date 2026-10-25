import traceback
import pymysql
import os
import logging
from datetime import datetime


# # === PATH CONFIG ===
# today_date_str = datetime.today().strftime("%d_%m_%Y")
today_date_str = '09_01_2026'
file_server_path = f"Z:\\julee\\PAGESAVES\\flipkart_grocery\\{today_date_str}\\"
os.makedirs(file_server_path, exist_ok=True)
PINCODE_PAGESAVE = f'{file_server_path}pincode_pages'
os.makedirs(PINCODE_PAGESAVE, exist_ok=True)
COMP_PINCODE_PAGESAVE = f'{file_server_path}comp_pincode_pages'
os.makedirs(COMP_PINCODE_PAGESAVE, exist_ok=True)
DATA_PAGESAVE = f'{file_server_path}availability_data'
os.makedirs(DATA_PAGESAVE, exist_ok=True)
C_DATA_PAGESAVE = f'{file_server_path}competitor_data'
os.makedirs(C_DATA_PAGESAVE, exist_ok=True)
input_file_path = f'D:\\Julee\\flipkart_grocery\\CODE\\INPUT\\'
# # pagesave_path = f"D:\\PAGESAVES\\flipkart_grocery\\{today_date_str}\\"
# # os.makedirs(pagesave_path, exist_ok=True)
# PINCODE_PAGESAVE = f'{pagesave_path}pincode_pages'
# os.makedirs(PINCODE_PAGESAVE, exist_ok=True)
# DATA_PAGESAVE = f'{pagesave_path}availability_data'
# os.makedirs(DATA_PAGESAVE, exist_ok=True)
# C_DATA_PAGESAVE = f'{pagesave_path}competitor_data'
# os.makedirs(C_DATA_PAGESAVE, exist_ok=True)
# input_file_path = f"D:\\FILES\\flipkart_grocery\\{today_date_str}\\INPUT\\"
# os.makedirs(input_file_path, exist_ok=True)

# today_date = datetime.today().strftime("%Y%m%d")
today_date = '20260109'
MASTER_DB_PINCODE = "all_india_pincode"
MASTER_PINCODE_TABLE = "data"
db_name = f"flipkart_grocery"
link_table = f"input_links_{today_date}"
pincode_table = f"cities_pincode"
availability_data_table = f"product_availability_{today_date}"
comp_availability_data_table = f"comp_price_analysis_{today_date}"


# # === DATABASE CONNECTION ===
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

    logging.info("Starting database and table creation process...")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # --- Create Database ---
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE `{db_name}`;")
        logging.info(f"Database `{db_name}` created or already exists.")

        # # --- Create tables ---
        # --- Create pincode table ---
        create_pincode_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{pincode_table}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                city VARCHAR(255),
                pincode VARCHAR(15),
                post_office VARCHAR(255),
                state VARCHAR(255),
                district VARCHAR(255),
                taluk VARCHAR(255),

                latitude DECIMAL(10,6),
                longitude DECIMAL(10,6),
                cookies TEXT,
                status VARCHAR(150),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                
                INDEX idx_city (city),
                INDEX idx_pincode (pincode)
            );
            """
        cursor.execute(create_pincode_table_query)
        conn.commit()
        reset_status_query = f"""
        UPDATE `{pincode_table}`
        SET status = 'PENDING'
        """
        cursor.execute(reset_status_query)
        conn.commit()
        affected_rows = cursor.rowcount
        logging.info(
            f"Table `{pincode_table}` ready. {affected_rows} rows reset to PENDING."
        )
        logging.info(f"Table `{pincode_table}` checked/created successfully.")
        create_availability_data_table_query = f"""
                    CREATE TABLE IF NOT EXISTS `{availability_data_table}` (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        -- product fields
                        brand VARCHAR(255),
                        targeted_sku VARCHAR(255),
                        product_name TEXT,
                        url TEXT,
                        sku VARCHAR(255),
                        gramage VARCHAR(255),
                        stock_availability_status VARCHAR(100),
                        description TEXT,
                        image_url TEXT,
                        mrp DECIMAL(10,2),
                        price DECIMAL(10,2),
                        discount_percent DECIMAL(10,2),
                        
                        -- location fields
                        city VARCHAR(255),
                        pincode VARCHAR(50),

                        -- operational fields
                        hash_key VARCHAR(255),        -- SHA hash
                        cookies TEXT,
                        status VARCHAR(200),          -- PENDING / SUCCESS / FAILED
                        INDEX idx_sku (targeted_sku)
                    );
                    """
        cursor.execute(create_availability_data_table_query)
        conn.commit()
        logging.info(f"Table `{availability_data_table}` checked/created successfully.")

        create_competitor_data_table_query = f"""
        CREATE TABLE IF NOT EXISTS `{comp_availability_data_table}` (
            id INT AUTO_INCREMENT PRIMARY KEY,

            -- BASE PRODUCT FIELDS
            base_product_id VARCHAR(100),
            base_brand VARCHAR(255),
            base_targeted_sku VARCHAR(255),
            base_product_name TEXT,
            base_url TEXT,
            base_sku VARCHAR(255),
            base_gramage VARCHAR(100),
            description TEXT,
            image_url TEXT,
            mrp DECIMAL(10,2),
            price DECIMAL(10,2),
            discount_percent DECIMAL(5,2),
            client_hash_id VARCHAR(255),
            client_stock_availability_status VARCHAR(100),

            -- COMPETITOR PRODUCT FIELDS
            competitor_brand VARCHAR(255),
            competitor_targeted_sku VARCHAR(255),
            competitor_product_name TEXT,
            competitor_url TEXT,
            competitor_sku VARCHAR(255),
            competitor_gramage VARCHAR(100),
            competitor_price DECIMAL(10,2),
            competitor_mrp DECIMAL(10,2),
            competitor_discount DECIMAL(5,2),
            competitor_hash_id VARCHAR(255),                   -- SHA256 hash
            comp_stock_availability_status VARCHAR(100),  -- IN_STOCK / OUT_OF_STOCK
            
            price_difference VARCHAR(150),
            discount_difference VARCHAR(150),

            -- LOCATION FIELDS
            city VARCHAR(255),
            pincode VARCHAR(50),

            -- OPERATIONAL FIELDS
            cookies TEXT,
            status VARCHAR(255),                     -- PENDING / SUCCESS / FAILED

            -- INDEXES & CONSTRAINTS
            INDEX idx_base_targeted_sku (base_targeted_sku),
            INDEX idx_competitor_targeted_sku (competitor_targeted_sku),
            INDEX idx_pincode (pincode)
        );
        """
        cursor.execute(create_competitor_data_table_query)
        conn.commit()
        logging.info(f"Table `{comp_availability_data_table}` checked/created successfully.")

        logging.info("All database setup operations completed successfully!")

    except Exception as e:
        logging.error("Error occurred during database setup!")
        logging.error(f"Exception Type: {type(e).__name__}")
        logging.error(f"Error Message: {e}")
        logging.error("Traceback:")
        logging.error(traceback.format_exc())

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logging.info("Database connection closed.")


# # === MAIN EXECUTION ===
if __name__ == '__main__':
    create_table()
