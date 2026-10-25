import db_config_1 as db
import gzip
import re
import os
import pymysql
from concurrent.futures import ThreadPoolExecutor, as_completed


def main(record):
    file_name = os.path.join(
        db.DATA_PAGESAVE,
        f"{record['hash_id']}.html.gz"
    )

    if not os.path.exists(file_name):
        return {
            "pid": record["pid"],
            "hash_id": record["hash_id"],
            "size_guide": None,
            "status": "PageSave not found"
        }

    try:
        with gzip.open(file_name, "rt", encoding="utf-8") as f:
            html_text = f.read()

        # Extract sizeGuide from normal or escaped JSON
        match = re.search(
            r'\\?"sizeGuide\\?"\s*:\s*\\?"([^"\\]*)',
            html_text
        )

        size_guide = match.group(1) if match else None

        return {
            "pid": record["pid"],
            "hash_id": record["hash_id"],
            "size_guide": size_guide,
            "status": "Extracted" if size_guide else "Not found"
        }

    except Exception as e:
        return {
            "pid": record["pid"],
            "hash_id": record["hash_id"],
            "size_guide": None,
            "status": f"Error: {e}"
        }


if __name__ == "__main__":

    con = pymysql.connect(
        user="root",
        host="***HIDDEN***",
        database="urban_outfitters",
        password="***HIDDEN***",
        autocommit=True
    )

    try:
        with con.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(f"""
                SELECT DISTINCT main_url, pid, hash_id
                FROM {db.data_table}
                WHERE size_chart_present = 'Yes'
                  AND size_chart IS NULL
                LIMIT 100
            """)

            records = cur.fetchall()


        print(f"Total records: {len(records)}")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(main, record)
                for record in records
            ]

            for future in as_completed(futures):
                try:
                    result = future.result()

                    if result is None:
                        continue

                    print(
                        f"{result['status']} | "
                        f"PID: {result['pid']} | "
                        f"Size Guide: {result['size_guide']}"
                    )

                except Exception as e:
                    print("THREAD ERROR:", repr(e))

    finally:
        con.close()