from pymongo import MongoClient
import os
from datetime import datetime
import gzip
import hashlib


today_crawling_date = datetime.today().strftime('%Y-%m')


cwd = os.getcwd().split("\\")
cwd.pop()
cwd = "\\".join(cwd).strip("\\")

pagesSave_path = f"{cwd}\\pagesave\\ulta_beauty_market_place\\{today_crawling_date}"
os.makedirs(pagesSave_path, exist_ok=True)

db_name = "ulta_market_place"
category_table_name = f"category_{today_crawling_date}"
link_table_name = f"links_{today_crawling_date}"
variation_table_name = f"combination_{today_crawling_date}"
pdp_table_name = f"data_{today_crawling_date}"

mongo_client = MongoClient(f"mongodb://localhost:27017/")
mongo_db = mongo_client[db_name]


def save_page(file_name, response):
    with gzip.open(file_name, "wb") as f:
        f.write(response.encode('utf-8'))

def read_page(file_name):
    with gzip.open(file_name, "rb") as f:
        text = f.read().decode('utf-8')
    return text

def hash12(text):
    text = str(text)
    h = hashlib.sha256(text.encode()).hexdigest()
    num = int(h, 16)
    return "1" + str(num % 10**11).zfill(11)