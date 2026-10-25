import re
import pandas as pd
import db_config_1 as db
import traceback

# ==========================
# CONFIG
# ==========================
excel_file = r"D:\Julee\CODE\ConstructionWeekOnline\CODE\INPUT\Updated_Keyword_list_02-09-2026.xlsx"
sheet_name = "Unique Keyword list"

def insert_excel_data():
    conn = None
    cursor = None
    try:
        conn = db.get_db_connection(db.db_name)
        cursor = conn.cursor()
        # Check if table already contains data
        cursor.execute(f"SELECT COUNT(*) FROM `{db.input_table}`")
        result = cursor.fetchone()
        record_count = list(result.values())[0]
        print(record_count)
        if record_count == 0:
            print("Table is empty. Inserting Excel data...")
            # Read Excel
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            # Rename columns
            df = df.rename(columns={ "Keyword Name": "keyword" })
            # Replace NaN with None
            df = df.where(pd.notna(df), None)
            # Sort: English alphabet first, then symbols/numbers
            df = df.sort_values(
                by="keyword",
                key=lambda s: s.fillna("").map(
                    lambda x: (
                        0 if re.match(r'^[A-Za-z]', str(x).strip()) else 1,
                        str(x).lower()
                    )
                )
            ).reset_index(drop=True)
            insert_query = f"""
                INSERT INTO `{db.input_table}`
                (keyword, status)
                VALUES (%s, %s)
            """
            data = []
            for _, row in df.iterrows():
                data.append((
                    str(row["keyword"]).strip() if row["keyword"] is not None else None,
                    "Pending"
                ))
            cursor.executemany(insert_query, data)
            conn.commit()
            print(f"Inserted {cursor.rowcount} records successfully.")
        else:
            print(f"Table already contains {record_count} records.")
            print("Updating all status values to 'Pending'...")
            update_query = f"""
                UPDATE `{db.input_table}`
                SET status = 'Pending'
            """
            cursor.execute(update_query)
            conn.commit()
            print(f"Updated {cursor.rowcount} records successfully.")
    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    insert_excel_data()