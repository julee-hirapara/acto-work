import json
import traceback
import pymysql
import os
from datetime import datetime, timedelta

now = datetime.now()
# current_date = "20_07_2026"
# current_date = (datetime.now()+ timedelta(days=1)).strftime("%d_%m_%Y")
# current_date = (datetime.now()).strftime("%d_%m_%Y")

project_name = 'ConstructionWeekOnline'
country = 'UAE'
current_date_for_file = (datetime.now()).strftime("%Y_%m_%d")
# Determine the slot
hour = now.hour
if 0 <= hour < 6:
    slot = "12_00_AM"
elif 6 <= hour < 12:
    slot = "06_00_AM"
elif 12 <= hour < 18:
    slot = "12_00_PM"
else:  # 18 <= hour < 24
    slot = "06_00_PM"
# Folder name
run_folder = f"{current_date_for_file}_{slot}"
# run_folder = f"2026_08_06_12_00_AM"
# for_share = f"\\***HIDDEN***\\temp-storage\\SynologyBackup"
for_share = f"\\***HIDDEN***\\SynologyBackup"
# file_base_path = f"J:\\News\\{project_name}\\{country}\\Web\\Partial run\\Data\\File\\{current_date_for_file}\\{slot}\\"
file_base_path = f"Z:\\News\\{project_name}\\{country}\\Web\\Partial run\\Data\\File\\{current_date_for_file}\\{slot}\\"
devlivery_file_path = f"{file_base_path}Delivery\\"
qa_file_path = f"{file_base_path}QA\\"
# pagesave_base_path = f"J:\\News\\{project_name}\\{country}\\Web\\Partial run\\Data\\Page save\\{current_date_for_file}\\{slot}\\"
pagesave_base_path = f"Z:\\News\\{project_name}\\{country}\\Web\\Partial run\\Data\\Page save\\{current_date_for_file}\\{slot}\\"
PL_pagesave_path = f"{pagesave_base_path}PL\\"
PDP_pagesave_path = f"{pagesave_base_path}PDP\\"
os.makedirs(devlivery_file_path, exist_ok=True)
os.makedirs(qa_file_path, exist_ok=True)
os.makedirs(PL_pagesave_path, exist_ok=True)
os.makedirs(PDP_pagesave_path, exist_ok=True)


db_name = f"{project_name}"
current_day = (datetime.now()).strftime("%d%m%Y")
print(current_day)
# input_table = f"input_table_{current_day}"
input_table = f"input_table"
# link_table = f"links_{current_day}"
link_table = f"master_links_table"
# data_table = f"data_{current_day}"
data_table = f"master_data_table"

# === DATABASE CONNECTION ===
def get_db_connection(db_name=None):
    if not db_name:
        db_name = db_name
    conn = pymysql.connect(
        host="***HIDDEN***",
        # host="localhost",
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
        create_input_table_query = f"""
                CREATE TABLE IF NOT EXISTS `{input_table}` (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        keyword VARCHAR(500),
                        status VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_keyword (keyword)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                    """
        cursor.execute(create_input_table_query)
        conn.commit()
        print(f"Table `{input_table}` checked/created successfully.")

        # --- Create links table ---
        create_link_table_query = f"""
                CREATE TABLE IF NOT EXISTS `{link_table}` (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        keyword_id VARCHAR(255),
                        keyword VARCHAR(500),
                        article_id VARCHAR(255),
                        title TEXT,
                        article_url VARCHAR(500),
                        image_url TEXT,
                        category VARCHAR(255),
                        publisher VARCHAR(255),
                        published_date VARCHAR(255),
                        hash_key VARCHAR(255),
                        file_name TEXT,
                        status VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE KEY uk_article (article_url),
                        UNIQUE KEY uk_article_id (article_id),
                        INDEX idx_keyword (keyword),
                        INDEX idx_keyword_id (keyword_id),
                        INDEX idx_category (category),
                        INDEX idx_published_date (published_date)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                    """
        cursor.execute(create_link_table_query)
        #  UNIQUE KEY uk_article (keyword_id, article_url),
        conn.commit()
        print(f"Table `{link_table}` checked/created successfully.")

        # --- Create links table ---
        create_data_table_query = f"""
            CREATE TABLE IF NOT EXISTS {data_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT NOT NULL,           
                subtitle TEXT,            
                message LONGTEXT NOT NULL,
                created_time VARCHAR(50),
                modified_time VARCHAR(50),
                source VARCHAR(50),
                domain VARCHAR(255),
                publication_name VARCHAR(255),
                journalist VARCHAR(255),
                country VARCHAR(10),
                media_title TEXT,
                conversation_stream LONGTEXT,
                permalink VARCHAR(500),
                article_id VARCHAR(255),
                keyword VARCHAR(500),
                description TEXT,
                category VARCHAR(255),
                tags TEXT,
                reading_time VARCHAR(100),
                image_urls LONGTEXT,
                video_urls LONGTEXT,
                audio_urls LONGTEXT,
                reach VARCHAR(255),
                web_shares VARCHAR(255),
                engagement TEXT,
                hash_key VARCHAR(255),
                search_hash_key VARCHAR(255),
                scrape_status VARCHAR(50) DEFAULT 'done',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_article_id(article_id),
                UNIQUE KEY uk_article_id (article_id),
                INDEX idx_keyword(keyword(255)),
                INDEX idx_created_time(created_time),
                INDEX idx_domain(domain(100)),
                INDEX idx_country(country),
                INDEX idx_publication(publication_name(100))
            );"""
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
