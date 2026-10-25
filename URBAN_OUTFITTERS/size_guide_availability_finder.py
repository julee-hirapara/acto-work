import gzip
import os

import pymysql
from concurrent.futures import ThreadPoolExecutor
import db_config_1 as db
from parsel import Selector

positive = 0
negitive = 0

def extract_size_slug_data(url, hash_id):
    file_path = f"{db.DATA_PAGESAVE}\\{hash_id}.html.gz"
    if not os.path.exists(file_path):
        print(f"❌ Missing file: {file_path}")
        return None
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        html_content = f.read()
    sel = Selector(text=html_content)
    size_guide_available_not = sel.xpath("//button[contains(@class, 'pwa-size-guide-link')]").get()
    if not size_guide_available_not:
        print("size guide not available on this page....")
        return False
    else:
        print("available")
        return True

def main(record):
    t = extract_size_slug_data(record['main_url'], record['hash_id'])
    if not t:
        with db.get_db_connection(db.db_name) as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute(f"update {db.data_table} set status_size='N/A' where hash_id=%s", (record['hash_id'],))
                conn.commit()
if __name__ == '__main__':
    with db.get_db_connection(db.db_name) as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(f"SELECT  DISTINCT main_url, hash_id FROM {db.data_table} WHERE status_size='pending'")
            # cur.execute(f"SELECT  DISTINCT pid, hash_id FROM {db.data_table} WHERE pid='UO-57537995-000'")
            records = cur.fetchall()
    print("Total records: ", len(records))
    with ThreadPoolExecutor(max_workers=20) as f:
        f.map(main, records)