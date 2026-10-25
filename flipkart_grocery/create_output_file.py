# import csv
# import pymysql
# import db_config as db
#
#
# OUTPUT_FILE = "product_availability.csv"
#
#
# def get_hash_key(db_status, hash_key):
#     status = normalize_status(db_status)
#     # if status in ("NOT_AVAILABLE_PINCODE", "TEMPORARILY_UNAVAILABLE"):
#     if status in ("NO_PINCODE", "NOT_AVAILABLE"):
#         return "N/A"
#     return hash_key if hash_key else "N/A"
#
# def map_stock_status(db_status, product_status):
#     product_status = product_status.strip().upper()
#     if product_status == "NOT_AVAILABLE":
#         return "No"
#     if db_status is None:
#         return None
#     status = db_status.strip().lower()
#     if status == "current":
#         return "Yes"
#     if status in ("ready", "out of stock", "out_of_stock", "n/a"):
#         return "No"
#     return "No"
#
#
# def normalize_status(db_status):
#     if db_status is None:
#         return None
#     return db_status.strip().upper()
#
#
# def export_to_csv():
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor(pymysql.cursors.DictCursor)
#
#     query = f"""
#         SELECT
#             id,
#             pincode,
#             city,
#             targeted_sku,
#             url,
#             product_name,
#             brand,
#             stock_availability_status,
#             status,
#             hash_key
#         FROM {db.availability_data_table} WHERE status != 'NO_PINCODE' AND status !='NO_PINCODE_NOT_AVAILABLE';
#     """
#     cursor.execute(query)
#     rows = cursor.fetchall()
#     print(f"📦 Rows fetched: {len(rows)}")
#     with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as csvfile:
#         writer = csv.writer(csvfile)
#         # CSV header
#         writer.writerow([
#             "id",
#             "zipcode",
#             "city",
#             "sku",
#             "url",
#             "product_name",
#             "brand",
#             "stock_avaliblity_status",
#             "hash_id",
#         ])
#
#         for row in rows:
#             if row["stock_availability_status"] is None:
#                 "No"
#             writer.writerow([
#                 row["id"],
#                 row["pincode"],
#                 row["city"],
#                 row["targeted_sku"] if row["targeted_sku"] else "N/A",
#                 row["url"] if row["url"] else "N/A",
#                 row["product_name"] if row["product_name"] else "N/A",
#                 row["brand"] if row["brand"] else "N/A",
#                 map_stock_status(row["stock_availability_status"], row['status']),
#                 # get_hash_key(
#                 #     row["status"],
#                 #     row["hash_key"]
#                 # ),
#                 row["hash_key"] if row["hash_key"] else "N/A",
#             ])
#
#     cursor.close()
#     conn.close()
#
#     print(f"✅ CSV created successfully: {OUTPUT_FILE}")
#
# def update_not_available_with_no_pincode():
#     conn = db.get_db_connection(db.db_name)
#     cur = conn.cursor()
#
#     cur.execute(f"""
#         UPDATE {db.availability_data_table} a
#         JOIN (
#             SELECT DISTINCT pincode
#             FROM {db.availability_data_table}
#             WHERE status = 'NO_PINCODE'
#         ) b ON a.pincode = b.pincode
#         SET a.status = 'NO_PINCODE_NOT_AVAILABLE'
#         WHERE a.status = 'NOT_AVAILABLE'
#     """)
#
#     affected = cur.rowcount
#     conn.commit()
#
#     cur.close()
#     conn.close()
#
#     print(f"🚫 Updated {affected} NOT_AVAILABLE rows to NO_PINCODE_NOT_AVAILABLE")
#
# if __name__ == "__main__":
#     # update_not_available_with_no_pincode()
#     export_to_csv()
#     import pandas as pd
#
#     # File paths
#     csv_file = r"product_availability.csv"
#     excel_file = r"product_availability.xlsx"
#
#     # Read CSV
#     df = pd.read_csv(csv_file)
#     df.fillna("N/A", inplace=True)
#     # Write to Excel
#     df.to_excel(excel_file, index=False)
#
#     print("✅ CSV successfully converted to Excel")
#

# # *********************************  competitor price analysis ***********************************
import csv
import pymysql
import pandas as pd
import math
import db_config as db

# ===============================
# File paths
# ===============================
OUTPUT_CSV = "comp_price_analysis.csv"
OUTPUT_EXCEL = "comp_price_analysis.xlsx"

# ===============================
# COLUMN ORDER (AS REQUESTED)
# ===============================
COLUMN_ORDER = [
    "id",
    "targeted_sku_name",
    "brand_name",
    "zipcode",
    # "city",
    "product_url",
    "product_id",
    "product_name",
    "quantity",
    "description",
    "image_url",
    "mrp",
    "price",
    "discount_percent",
    "competitor_brand_name",
    "competitor_product_name",
    "competitor_url",
    "competitor_price",
    "competitor_mrp",
    "competitor_discount",
    "price_difference",
    "discount_difference",
    "clint_hash_id",
    "competitor_hash_id"
]

# ===============================
# NORMALIZERS
# ===============================

def normalize_text(val):
    if val is None:
        return "N/A"
    if isinstance(val, float) and math.isnan(val):
        return "N/A"
    if isinstance(val, str) and val.strip().lower() in ("", "nan", "null", "none"):
        return "N/A"
    return val

def normalize_number(val):
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return val

# def calculate_discount_diff(base_price, base_discount, comp_price, comp_discount):
#     # -------- PRICE MUST EXIST --------
#     if (
#         base_price in (None, "N/A") or base_price == 0 or
#         comp_price in (None, "N/A") or comp_price == 0
#     ):
#         return "N/A"
#
#     # -------- DISCOUNT MUST EXIST (0 IS VALID) --------
#     if (
#         base_discount in (None, "N/A") or
#         comp_discount in (None, "N/A")
#     ):
#         return "N/A"
#
#     # -------- VALID CASE --------
#     return base_discount - comp_discount
#
# def calculate_price_diff(base_price, comp_price):
#     if (
#         base_price in (None, "N/A") or base_price == 0 or
#         comp_price in (None, "N/A") or comp_price == 0
#     ):
#         return "N/A"
#
#     return base_price - comp_price

# ===============================
# ROW MAPPING (CORRECT LOGIC)
# ===============================
def map_row(row):
    # product_url = normalize_text(row.get("base_url"))
    if not row.get("base_url"):
        product_url = "N/A"
    else:
        product_url = row.get("base_url")

    # competitor_url = normalize_text(row.get("competitor_url"))
    if not row.get("competitor_url"):
        competitor_url = "N/A"
    else:
        competitor_url = row.get("competitor_url")

    # =====================
    # CLIENT SIDE
    # =====================
    if product_url == "N/A":
        mrp = "N/A"
        price = "N/A"
        discount = "N/A"
    else:
        if not row.get("mrp"):
            mrp = 0
        else:
            mrp = row.get("mrp")
        # mrp = normalize_number(row.get("mrp"))
        # price = normalize_number(row.get("price"))
        if not row.get("price"):
            price = 0
        else:
            price = row.get("price")
        # discount = normalize_number(row.get("discount_percent"))
        if not row.get("discount_percent"):
            discount = 0
        else:
            discount = row.get("discount_percent")

    # =====================
    # COMPETITOR SIDE
    # =====================
    if competitor_url == "N/A":
        comp_price = "N/A"
        comp_mrp = "N/A"
        comp_discount = "N/A"
    else:
        # comp_price = normalize_number(row.get("competitor_price"))
        if not row.get("competitor_price"):
            comp_price = 0
        else:
            comp_price = row.get("competitor_price")
        # comp_mrp = normalize_number(row.get("competitor_mrp"))
        if not row.get("competitor_mrp"):
            comp_mrp = 0
        else:
            comp_mrp = row.get("competitor_mrp")
        # comp_discount = normalize_number(row.get("competitor_discount"))
        if not row.get("competitor_discount"):
            comp_discount = 0
        else:
            comp_discount = row.get("competitor_discount")

    # discount_diff = calculate_discount_diff(price, discount, comp_price, comp_discount)
    # price_diff = calculate_price_diff(price, comp_price)
    if price == "N/A":
        price_diff = "N/A"
    elif comp_price == "N/A":
        price_diff = "N/A"
    else:
        price_diff = price - comp_price

    if discount == "N/A":
        discount_diff = "N/A"
    elif comp_discount == "N/A":
        discount_diff = "N/A"
    else:
        discount_diff = discount - comp_discount
    return [
        normalize_text(row.get("id")),
        normalize_text(row.get("base_targeted_sku")),
        normalize_text(row.get("base_brand")),
        normalize_text(row.get("pincode")),
        # row.get("city"),
        product_url,
        normalize_text(row.get("base_sku")),
        normalize_text(row.get("base_product_name")),
        normalize_text(row.get("base_gramage")),
        normalize_text(row.get("description")),
        normalize_text(row.get("image_url")),

        mrp,
        price,
        discount,

        normalize_text(row.get("competitor_brand")),
        normalize_text(row.get("competitor_product_name")),
        competitor_url,

        comp_price,
        comp_mrp,
        comp_discount,

        price_diff,
        discount_diff,

        normalize_text(row.get("client_hash_id")),
        normalize_text(row.get("competitor_hash_id")),
    ]


# ===============================
# EXPORT FUNCTION
# ===============================
def export_comp_price_analysis():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    query = f"SELECT * FROM {db.comp_availability_data_table}"
    cursor.execute(query)
    rows = cursor.fetchall()
    print(f"📦 Rows fetched: {len(rows)}")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMN_ORDER)
        for row in rows:
            writer.writerow(map_row(row))

    cursor.close()
    conn.close()

    print(f"✅ CSV created: {OUTPUT_CSV}")

    df = pd.read_csv(OUTPUT_CSV)
    df.fillna("N/A", inplace=True)
    df.to_excel(OUTPUT_EXCEL, index=False)

    print(f"✅ Excel created: {OUTPUT_EXCEL}")

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    export_comp_price_analysis()
