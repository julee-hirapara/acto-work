import hashlib
import json
import pymysql
import pandas as pd
import db_config_1 as db
from datetime import datetime
import re


# CLEAN TEXT
def clean_text(value):
    if value is None or value == "":
        return "N/A"
    if not isinstance(value, str):
        return value
    text = value
    # remove control chars
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)
    # remove invisible unicode chars
    text = re.sub(r"[\u200B-\u200F\u202A-\u202E\u2060-\u206F]", " ", text)
    # remove emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub(" ", text)
    # remove escaped chars
    # remove REAL line breaks/tabs
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    # remove escaped chars
    text = text.replace("\\n", " ")
    text = text.replace("\\r", " ")
    text = text.replace("\\t", " ")
    # remove backslashes
    text = text.replace("\\", "")
    # remove extra spaces
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text if text else "N/A"

# GENERATE MPN HASH
def generate_hash_key(pid, color):
    pid = pid if pid else ""
    color = color if color else ""
    raw = f"{pid}+{color}".encode()
    h = hashlib.sha256(raw).hexdigest()
    num = int(h, 16)
    return str(num)[0:12]

# NORMALIZE REVIEW TEXT
def normalize_review_text(review_text):
    try:
        if not review_text:
            return {"reviews": []}
        # string -> json
        if isinstance(review_text, str):
            data = json.loads(review_text)
        else:
            data = review_text
        # list
        if isinstance(data, list):
            reviews = data
        # dict
        elif isinstance(data, dict):
            if "reviews" in data:
                if isinstance(data["reviews"], list):
                    reviews = data["reviews"]
                else:
                    reviews = []
            else:
                reviews = [data]
        else:
            reviews = []
        # replace all nulls with N/A
        cleaned_reviews = []
        for review in reviews:
            cleaned_review = {}
            for k, v in review.items():
                if v is None or v == "":
                    cleaned_review[k] = "N/A"
                else:
                    cleaned_review[k] = clean_text(v)
            cleaned_reviews.append(cleaned_review)
        return {"reviews": cleaned_reviews}
    except Exception as e:
        print("Review normalize error:", e)
        return {"reviews": []}

# CREATE CSV
def create_csv_output():
    # DB CONNECTION
    con = db.get_db_connection(db.db_name)
    cur = con.cursor(pymysql.cursors.DictCursor)

    cur.execute(f"""
        SELECT *
        FROM {db.data_table}
    """)
    # """WHERE pid IN (
    #             'UO-104476908-000',
    #             'UO-98452881-000',
    #             'UO-106672280-000',
    #             'UO-95147914-000',
    #             'UO-100290162-000',
    #             'UO-107178394-000',
    #             'UO-76010537-000',
    #             'UO-91367490-000',
    #             'UO-89297493-000',
    #             'UO-96651559-000'
    #         )        ORDER BY id ASC"""
    rows = cur.fetchall()
    final_data = []
    # LOOP ROWS
    serial_no = 1
    for index, row in enumerate(rows, start=1):
        category = clean_text(row.get("category"))
        category_lower = str(category).lower()
        # skip home/lifestyle
        if category_lower.startswith(("home", "lifestyle")):
            continue
        # PRICE
        listprice = row.get("price") if row.get("price") else "N/A"
        saleprice = row.get("sale_price") if row.get("sale_price") else "N/A"
        # discount
        try:
            if listprice != "N/A" and saleprice != "N/A":
                discount = round(float(listprice) - float(saleprice), 2)
                if discount == 0:
                    discount = "N/A"
            else:
                discount = "N/A"
        except:
            discount = "N/A"
        # HASH
        mpn = generate_hash_key(
            row.get("pid"),
            row.get("colour")
        )
        # REVIEW TEXT
        review_text = row.get("review_text")
        normalized_reviews = normalize_review_text(review_text)
        if normalized_reviews.get("reviews"):
            review_output = json.dumps(
                normalized_reviews,
                separators=(',', ':'),
                ensure_ascii=False
            )
        else:
            review_output = "N/A"
        # SIZE CHART
        size_chart = row.get("size_chart")
        try:
            if size_chart:
                size_chart_output = json.dumps(
                    json.loads(size_chart),
                    separators=(',', ':'),
                    ensure_ascii=False
                )
            else:
                size_chart_output = "N/A"
        except:
            size_chart_output = "N/A"

        # ROW DATA
        instock = clean_text(row.get("is_in_stock"))
        if instock == "1":
            instock = "TRUE"
        elif instock == "0":
            instock = "FALSE"
        row_data = {
            "S.No.": serial_no,
            "Website": clean_text(row.get("website")),
            "PID": clean_text(row.get("pid")),
            "Name": clean_text(row.get("name")),
            "Short Description": clean_text(row.get("short_description")),
            "Description": clean_text(row.get("description")),
            "Category": clean_text(row.get("category")),
            "Image URL": clean_text(row.get("image_url")),
            "Price": listprice,
            "Price Currency": clean_text(row.get("price_currency")),
            "Sale Price": saleprice,
            "Final Price": row.get("final_price") if row.get("final_price") else "N/A",
            "Discount": discount,
            "IsOnSale": clean_text(row.get("is_on_sale")),
            "IsInStock": instock,
            "Keywords": clean_text(row.get("keywords")),
            "Brand": clean_text(row.get("brand")),
            "Manufacturer": clean_text(row.get("manufacturer")),
            "MPN": str(mpn),
            "UPC or EAN": clean_text(row.get("upc_ean")),
            "SKU": clean_text(row.get("sku")),
            "Colour": clean_text(row.get("colour")),
            "Gender": clean_text(row.get("gender")),
            "Size": clean_text(row.get("size_type")),
            "Size Chart": size_chart_output,
            "Varint_Price": row.get("variant_price") if row.get("variant_price") else "N/A",
            "Alternate Image URLs": clean_text(row.get("alternate_image_urls")),
            "Link URL": clean_text(row.get("link_url")),
            "Num Ratings": row.get("num_ratings") if row.get("num_ratings") else "N/A",
            "Average Ratings": round(row.get("avg_ratings"), 1) if row.get("avg_ratings") else "N/A",
            "Reviews": review_output,
            "hash_id": str(row.get("hash_id"))
        }
        final_data.append(row_data)
        serial_no += 1
    
    # CREATE DATAFRAME
    # df = pd.DataFrame(final_data)
    columns = [
        "S.No.",
        "Website",
        "PID",
        "Name",
        "Short Description",
        "Description",
        "Category",
        "Image URL",
        "Price",
        "Price Currency",
        "Sale Price",
        "Final Price",
        "Discount",
        "IsOnSale",
        "IsInStock",
        "Keywords",
        "Brand",
        "Manufacturer",
        "MPN",
        "UPC or EAN",
        "SKU",
        "Colour",
        "Gender",
        "Size",
        "Size Chart",
        "Varint_Price",
        "Alternate Image URLs",
        "Link URL",
        "Num Ratings",
        "Average Ratings",
        "Reviews",
        "hash_id"
    ]
    df = pd.DataFrame(final_data, columns=columns)
    # CLEAN EXTRA COLUMNS
    df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
    df = df.loc[:, df.columns.notna()]  
    # REPLACE NULLS  
    df = df.fillna("N/A")   
    # OUTPUT FILE   
    current_date = datetime.now().strftime("%Y%m%d")
    output_file = f"{db.RESULT_PAGE}/Urban_outfitter_{current_date}.csv"  
    # EXPORT CSV
    import csv
    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_ALL
        # quoting=1
    )
    # CLOSE DB
    cur.close()
    con.close()
    print(f"✅ CSV file created successfully: {output_file}")

# MAIN
if __name__ == "__main__":
    create_csv_output()




# import hashlib
# import json
# import pymysql
# import db_config_1 as db
# from datetime import datetime
# from openpyxl import Workbook
# from openpyxl.styles import Font
# import re
#
#
# def normalize_review_text(review_text):
#     try:
#         # if already dict/list
#         if isinstance(review_text, (dict, list)):
#             data = review_text
#         else:
#             data = json.loads(review_text)
#         # CASE 1:
#         # [
#         #   {...}
#         # ]
#         if isinstance(data, list):
#             return {
#                 "reviews": data
#             }
#         # CASE 2:
#         # {
#         #   "reviews": [...]
#         # }
#         elif isinstance(data, dict):
#             # if already correct format
#             if "reviews" in data:
#                 # ensure reviews is list
#                 if isinstance(data["reviews"], list):
#                     return data
#                 else:
#                     return {"reviews": []}
#             # single review object
#             return {
#                 "reviews": [data]
#             }
#         return {"reviews": []}
#     except Exception as e:
#         print(f"Review normalize error: {e}")
#         return {"reviews": []}
#
#
# def clean_text(value):
#     """Clean text: remove None, extra spaces, junk characters, control chars."""
#     if value is None:
#         return "N/A"
#     if not isinstance(value, str):
#         return value
#     text = value
#     # Remove control characters (ASCII 0–31 + DEL)
#     text = re.sub(r"[\x00-\x1F\x7F]", " ", text)
#     # Remove invisible Unicode characters (zero-width, bidi control, etc.)
#     text = re.sub(r"[\u200B-\u200F\u202A-\u202E\u2060-\u206F]", " ", text)
#     # Remove emoji + pictographs
#     emoji_pattern = re.compile(
#         "["
#         "\U0001F600-\U0001F64F"  # emoticons
#         "\U0001F300-\U0001F5FF"  # symbols & pictographs
#         "\U0001F680-\U0001F6FF"  # transport & map symbols
#         "\U0001F1E0-\U0001F1FF"  # flags
#         "\U00002500-\U00002BEF"  # Chinese/Japanese symbols
#         "]+", flags=re.UNICODE
#     )
#     text = emoji_pattern.sub(" ", text)
#     # Replace multiple whitespaces (tabs, newlines, 2+ spaces) with a single space
#     text = re.sub(r"\s+", " ", text)
#     # Trim
#     text = text.strip()
#
#     return text if text else "N/A"
#
#
# def remove_duplicate_skus(connection):
#     """
#     Finds duplicate SKUs in the 'products' table.
#     Keeps oldest ID (smallest) and deletes the rest.
#     """
#     try:
#         with connection.cursor(pymysql.cursors.DictCursor) as cursor:
#             # -----------------------------------
#             # Step 1: Find duplicate SKUs
#             # -----------------------------------
#             cursor.execute(f"""
#                 SELECT sku, COUNT(*) AS cnt
#                 FROM {db.data_table}
#                 GROUP BY sku
#                 HAVING cnt > 1
#             """)
#             duplicates = cursor.fetchall()
#             print("Duplicate SKUs found:", duplicates)
#             # -----------------------------------
#             # Step 2: For each duplicate:
#             # Keep 1 record (oldest id) and delete others
#             # -----------------------------------
#             for row in duplicates:
#                 sku = row["sku"]
#                 cursor.execute(f"""
#                     SELECT id
#                     FROM {db.data_table}
#                     WHERE sku = %s
#                     ORDER BY id ASC
#                 """, (sku,))
#                 ids = [r["id"] for r in cursor.fetchall()]
#                 keep_id = ids[0]
#                 delete_ids = ids[1:]
#                 print(f"SKU {sku}: keeping ID {keep_id}, deleting IDs {delete_ids}")
#                 if delete_ids:
#                     placeholders = ",".join(["%s"] * len(delete_ids))
#                     # cursor.execute(
#                     #     f"DELETE FROM products WHERE id IN ({placeholders})",
#                     #     delete_ids
#                     # )
#             connection.commit()
#             print("Duplicate cleanup completed successfully.")
#     except Exception as e:
#         print("Error:", e)
#
# def normalize_rating(value):
#     if value in (0, 0.0, "0", "0.0", "", None):
#         return "N/A"
#     # try:
#     #     num = float(value)
#     #     if num == 0:
#     #         return "N/A"
#     #     return num
#     # except:
#     #     return "N/A"
#
# def url_to_id(url):
#     h = hashlib.sha256(url.encode()).hexdigest()
#     num = int(h, 16)
#     short_id = str(num)[0:12]
#     return short_id
#
# import hashlib
# def clean_row(row_data):
#     cleaned = []
#     for item in row_data:
#         if item is None or item == "":
#             cleaned.append("N/A")
#         elif isinstance(item, str):
#             cleaned.append(clean_text_data(item))
#         else:
#             cleaned.append(item)
#     return cleaned
#
# def clean_text_data(value):
#     if value is None:
#         return "N/A"
#     if not isinstance(value, str):
#         return value
#     text = value
#     # remove control chars
#     text = re.sub(r"[\x00-\x1F\x7F]", " ", text)
#     # remove invisible unicode chars
#     text = re.sub(r"[\u200B-\u200F\u202A-\u202E\u2060-\u206F]", " ", text)
#     # remove emojis
#     emoji_pattern = re.compile(
#         "["
#         "\U0001F600-\U0001F64F"
#         "\U0001F300-\U0001F5FF"
#         "\U0001F680-\U0001F6FF"
#         "\U0001F1E0-\U0001F1FF"
#         "]+",
#         flags=re.UNICODE
#     )
#     text = emoji_pattern.sub(" ", text)
#     # replace escaped chars
#     text = text.replace("\\n", " ")
#     text = text.replace("\\r", " ")
#     text = text.replace("\\t", " ")
#     # remove backslashes
#     text = text.replace("\\", "")
#     # OPTIONAL: remove forward slashes
#     # text = text.replace("/", "")
#     # remove extra spaces/newlines/tabs
#     text = re.sub(r"\s+", " ", text)
#     # trim
#     text = text.strip()
#     return text if text else "N/A"
#
# def generate_hash_key(pid, color):
#     if pid is None: pid = ""
#     if color is None: color = ""
#     raw = f"{pid}+{color}".encode()
#     h = hashlib.sha256(raw).hexdigest()
#     num = int(h, 16)
#     hash_id = str(num)[0:12]
#     return hash_id
#
# def create_excel_output():
#     # DB connection
#     con = db.get_db_connection(db.db_name)
#     cur = con.cursor(pymysql.cursors.DictCursor)
#
#     cur.execute(f"SELECT * FROM `{db.data_table}` ORDER BY id ASC")
#     rows = cur.fetchall()
#     # Column headers
#     headers = [
#         "S.No.", "Website", "PID", "Name", "Short Description", "Description",
#         "Category", "Image URL", "Price", "Price Currency", "Sale Price",
#         "Final Price", "Discount", "IsOnSale", "IsInStock", "Keywords", "Brand",
#         "Manufacturer", "MPN", "UPC or EAN", "SKU", "Colour", "Gender", "Size", "Size Chart",
#         "Varint_Price", "Alternate Image URLs", "Link URL", "Num Ratings",
#         "Average Ratings", "Reviews", "hash_id", "main_url"
#     ]
#     wb = Workbook()
#     ws = wb.active
#     ws.title = "data"
#     # Write headers
#     ws.append(headers)
#     # Make bold
#     for cell in ws[1]:
#         cell.font = Font(bold=True)
#     # Insert data rows
#     for index, row in enumerate(rows, start=1):
#         category = clean_text(row.get("category"))
#         category_lower = category.lower()
#         if category_lower.startswith(("home", "lifestyle")):
#             continue
#         listprice = row.get("price") if row.get("price") else "N/A"
#         saleprice = row.get("sale_price") if row.get("sale_price") else "N/A"
#         discount  = round(listprice - saleprice, 2)
#         if discount == 0:
#             discount = "N/A"
#         if discount == "N/A":
#             listprice = saleprice
#         hash_id = url_to_id(row.get("main_url"))
#         mpn = generate_hash_key(row.get("pid"), row.get("colour"))
#         review_text = row.get("review_text")
#         if review_text:
#             normalized_reviews = normalize_review_text(review_text)
#             # if reviews empty -> N/A
#             if not normalized_reviews.get("reviews"):
#                 review_output = "N/A"
#             else:
#                 review_output = json.dumps(normalized_reviews,separators=(',', ':'),ensure_ascii=False).replace('\\"', '"').replace('\n', ' ')
#         else:
#             review_output = "N/A"
#
#         row_data =[
#             index,
#             clean_text(row.get("website")),                         # *** Override website ***
#             clean_text(row.get("pid")),
#             clean_text(row.get("name")),
#             clean_text(row.get("short_description")),
#             clean_text(row.get("description")),         # *** Clean extra spaces ***
#             clean_text(row.get("category")),
#             clean_text(row.get("image_url")),
#             listprice,
#             clean_text(row.get("price_currency")),
#             row.get("sale_price") if row.get("sale_price") else "N/A",
#             row.get("final_price") if row.get("final_price") else "N/A",
#             clean_text(discount),
#             clean_text(row.get("is_on_sale")),
#             clean_text(row.get("is_in_stock")),
#             clean_text(row.get("keywords")),
#             clean_text(row.get("brand")) if row.get("brand") else "N/A",
#             clean_text(row.get("manufacturer")),
#             str(mpn),
#             clean_text(row.get("upc_ean")),
#             clean_text(row.get("sku")),
#             clean_text(row.get("colour")),
#             clean_text(row.get("gender")),
#             clean_text(row.get("size_type")),
#             json.dumps(
#                 json.loads(row.get("size_chart")),
#                 separators=(',', ':'), ensure_ascii=False
#             ) if row.get("size_chart") else "N/A",
#             # json.dumps(row.get("size_chart"), ensure_ascii=False) if row.get("size_chart") else "N/A",
#             row.get("variant_price") if row.get("variant_price") else "N/A",
#             clean_text(row.get("alternate_image_urls")),
#             clean_text(row.get("link_url")),
#             row.get("num_ratings") if row.get("num_ratings") else "N/A",
#             round(row.get("avg_ratings"),1) if row.get("avg_ratings") else "N/A",
#             # json.dumps(row.get("review_text"), ensure_ascii=False) if row.get("review_text") else "N/A",
#             review_output,
#             str(hash_id),
#             clean_text(row.get("main_url")),
#             # json.dumps(
#             #     json.loads(row.get("size_chart")),
#             #     separators=(',', ':'), ensure_ascii=False
#             # ) if row.get("size_chart") else "N/A",
#             #
#             # # json.dumps(
#             # #     json.loads(row.get("review_text")),
#             # #     separators=(',', ':'),ensure_ascii=False
#             # # ) if row.get("review_text") else "N/A"
#             # # row.get("size_chart"),
#             # # row.get("review_text")
#         ]
#         # ws.append(clean_text_data(row_data))
#         ws.append(clean_row(row_data))
#     # Save Excel
#     current_date = datetime.now().strftime("%Y%m%d")
#     output_file = f"{db.RESULT_PAGE}/Urban_outfitter_{current_date}.xlsx"
#     wb.save(output_file)
#     cur.close()
#     con.close()
#     print(f"✅ Excel file created successfully: {output_file}")
#
# # def delete_cat_link_table():
# #     conn = db.get_db_connection(db.db_name)
# #     cur = conn.cursor(pymysql.cursors.DictCursor)
# #     cur.execute(f"DROP TABLE IF EXISTS {db.cat_links_table};")
# #     conn.commit()
# #     conn.close()
# #     print("cat_links table dropped successfully!")
#
#
# def main():
#     # Get DB connection from db_config module
#     conn = db.get_db_connection(db.db_name)
#     # Run duplicate cleaning
#     remove_duplicate_skus(conn)
#     # Close connection
#     conn.close()
#     create_excel_output()
#     # delete_cat_link_table()
#
#
#
# if __name__ == '__main__':
#     main()
#
#
#
# # import sys
# # print("Python path:", sys.executable)
# # print("Python version:", sys.version)