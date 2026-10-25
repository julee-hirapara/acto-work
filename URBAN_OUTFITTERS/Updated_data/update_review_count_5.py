import orjson
from parsel import Selector
import json
import re
import os
import pymysql
from concurrent.futures import ThreadPoolExecutor
import db_config_1 as db
import gzip

def main(record):
    file_name = os.path.join(db.REVIEW_PAGESAVE, f"{record['pid']}.json.gz")
    # file_name = fr"D:\Julee\PAGESAVES\URBAN_OUTFITTERS\07_2026\review\{record['pid']}.json"
    if not os.path.exists(file_name):
        return None
    if os.path.exists(file_name):
        try:
            with gzip.open(file_name, "rt", encoding="utf-8") as f:
                data = json.load(f)
        except (EOFError, gzip.BadGzipFile, json.JSONDecodeError) as e:
            print(f"{record['pid']} -> Invalid gzip/json: {e}")
            return
    review_count = data.get("totalResults", "N/A")
    if review_count == 0:
        review_count = None

    try:
        # #  pip install DBUtils
        # from dbutils.pooled_db import PooledDB
        #
        # pool = PooledDB(
        #     creator=pymysql,
        #     maxconnections=20,
        #     host='localhost',
        #     user='root',
        #     password='***HIDDEN***',
        #     database='urban_outfitters'
        # )
        # con = pool.connection()
        # cur = con.cursor()
        con = pymysql.connect(user='root', host='localhost', database='urban_outfitters', password='***HIDDEN***',
                              autocommit=True)
        cur = con.cursor(pymysql.cursors.DictCursor)
        updates = []
        cur.execute(
            """
            UPDATE data_072026
            SET num_ratings=%s,
                status='done'
            WHERE pid=%s
            """,
            (review_count, record['pid'])
        )
        # updates.append((review_count, record['pid']))
        # cur.executemany(
        #     """
        #     UPDATE data_072026
        #     SET num_ratings=%s,
        #         status='done'
        #     WHERE pid=%s
        #     """,
        #     updates
        # )
        # con.commit()
    except Exception as e:
        print(f"PID {record['pid']} ERROR:", e)

    finally:
        if cur:
            cur.close()
        if con:
            con.close()
    # cur.execute("update data_062026 set size_chart=%s, status='done' where pid=%s",
    #             (json.dumps(final_output, ensure_ascii=False), record['pid']))
    # con.commit()
    print("Updated: ", record['pid'])


if __name__ == "__main__":
    # main()
    con = pymysql.connect(user='root', host='localhost', database='urban_outfitters', password='***HIDDEN***', autocommit=True)
    cur = con.cursor(pymysql.cursors.DictCursor)
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM data_062026 where status='done' AND pid='UO-107304768-000'")
    cur.execute(f"SELECT  DISTINCT main_url, pid FROM data_072026 where status='pending'")
    records = cur.fetchall()
    print(len(records))
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(main, record) for record in records]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("THREAD ERROR:", repr(e))
