# # import pandas as pd
# # import pymysql
# # import db_config as db
# # import os
# #
# # EXCEL_FILE = os.path.join(db.input_file_path, "sample_fkgrocery_product_data.xlsx")
# #
# # # -----------------------
# # # DB CONNECTION
# # # -----------------------
# # conn = db.get_db_connection(db.db_name)
# # cursor = conn.cursor(pymysql.cursors.DictCursor)
# #
# # # -----------------------
# # # 1. READ EXCEL (NO FILTERS)
# # # -----------------------
# # products_df = pd.read_excel(EXCEL_FILE)
# #
# # # -----------------------
# # # 2. READ PINCODES
# # # -----------------------
# # cursor.execute(f"""
# #     SELECT city, pincode
# #     FROM {db.pincode_table}
# # """)
# # pincodes = cursor.fetchall()
# #
# # # -----------------------
# # # 3. INSERT QUERY
# # # -----------------------
# # insert_sql = f"""
# # INSERT IGNORE INTO {db.availability_data_table} (
# #     brand,
# #     targeted_sku,
# #     product_name,
# #     url,
# #     sku,
# #     gramage,
# #     city,
# #     pincode,
# #     cookies,
# #     status
# # ) VALUES (
# #     %s, %s, %s, %s, %s, %s,
# #     %s, %s, %s, %s
# # )
# # """
# #
# # # -----------------------
# # # 4. PREPARE DATA
# # # -----------------------
# # batch_data = []
# #
# # for _, product in products_df.iterrows():
# #     for pincode in pincodes:
# #
# #         is_available = product["client_available"] == "AVAILABLE"
# #
# #         batch_data.append((
# #             product["brand"],
# #             product["targeted_sku"],
# #             product["product_name"],
# #             product["url"] if is_available else "N/A",
# #             product["sku"] if is_available else "N/A",
# #             product["gramage"] if is_available else "N/A",
# #             pincode["city"],
# #             pincode["pincode"],
# #             None,
# #             "PENDING" if is_available else "NOT_AVAILABLE"
# #         ))
# #
# # # -----------------------
# # # 5. BULK INSERT
# # # -----------------------
# # cursor.executemany(insert_sql, batch_data)
# # conn.commit()
# #
# # print(f"✅ Inserted {cursor.rowcount} rows into {db.availability_data_table}")
# #
# # # -----------------------
# # # CLEANUP
# # # -----------------------
# # cursor.close()
# # conn.close()
#
#
# import pandas as pd
# import pymysql
# import hashlib
# from datetime import datetime
# import db_config as db
# import os
#
# EXCEL_FILE = os.path.join(db.input_file_path, "sample_fkgrocery_product_data.xlsx")
#
# # -----------------------
# # DB CONNECTION
# # -----------------------
# conn = db.get_db_connection(db.db_name)
# cursor = conn.cursor(pymysql.cursors.DictCursor)
#
# # -----------------------
# # 1. READ EXCEL (PRODUCTS)
# # -----------------------
# products_df = pd.read_excel(EXCEL_FILE)
#
# # keep only valid products
# products_df = products_df[
#     (products_df["client_available"] == "AVAILABLE") &
#     (products_df["scrape_required"] == "YES")
# ]
#
# # -----------------------
# # 2. READ PINCODES FROM DB
# # -----------------------
# cursor.execute(f"""
#     SELECT
#         city,
#         pincode
#     FROM {db.pincode_table}
# """)
# pincodes = cursor.fetchall()
#
# # -----------------------
# # 3. INSERT QUERY
# # -----------------------
# insert_sql = f"""
# INSERT IGNORE INTO {db.availability_data_table} (
#     brand,
#     targeted_sku,
#     product_name,
#     url,
#     sku,
#     gramage,
#     city,
#     pincode,
#     cookies,
#     status
# ) VALUES (
#     %s, %s, %s, %s, %s, %s,
#     %s, %s, %s, %s
# )
# """
# # -----------------------
# # 4. CREATE MATRIX & INSERT
# # -----------------------
# batch_data = []
#
# for _, product in products_df.iterrows():
#     for pincode in pincodes:
#         # raw_key = (
#         #     product["product_name"]+product["sku"]+pincode["pincode"]
#         # )
#         # hash_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
#         batch_data.append((
#             product["brand"],
#             product["targeted_sku"],
#             product["product_name"],
#             product["url"],
#             product["sku"],
#             product["gramage"],
#             pincode["city"],
#             pincode["pincode"],
#             None,                 # cookies
#             "PENDING"          # status
#         ))
#
# # -----------------------
# # 5. BULK INSERT
# # -----------------------
# cursor.executemany(insert_sql, batch_data)
# conn.commit()
#
# print(f"✅ Inserted {cursor.rowcount} rows into {db.availability_data_table}")
#
# # -----------------------
# # CLEANUP
# # -----------------------
# cursor.close()
# conn.close()


import pandas as pd
import pymysql
import db_config as db
import os

EXCEL_FILE = os.path.join(db.input_file_path, "sample_fkgrocery_product_data.xlsx")

# -----------------------
# DB CONNECTION
# -----------------------
conn = db.get_db_connection(db.db_name)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# -----------------------
# 1. READ EXCEL
# -----------------------
products_df = pd.read_excel(EXCEL_FILE)

# -----------------------
# 2. FILTER ONLY NOT_AVAILABLE
# -----------------------
products_df = products_df[
    products_df["client_available"] == "NOT_AVAILABLE"
]
products_df = products_df.fillna("N/A")
print(f"📦 NOT_AVAILABLE products: {len(products_df)}")

# -----------------------
# 3. READ PINCODES
# -----------------------
cursor.execute(f"""
    SELECT city, pincode
    FROM {db.pincode_table}
""")
pincodes = cursor.fetchall()

# -----------------------
# 4. INSERT QUERY
# -----------------------
insert_sql = f"""
INSERT IGNORE INTO {db.availability_data_table} (
    brand,
    targeted_sku,
    product_name,
    url,
    sku,
    gramage,
    city,
    pincode,
    cookies,
    status
) VALUES (
    %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s
)
"""

# -----------------------
# 5. PREPARE DATA
# -----------------------
batch_data = []

for _, product in products_df.iterrows():
    for pincode in pincodes:
        batch_data.append((
            str(product.get("brand", "N/A")),
            str(product.get("targeted_sku", "N/A")),
            str(product.get("product_name", "N/A")),
            "N/A",                 # url
            "N/A",                 # sku
            "N/A",                 # gramage
            str(pincode.get("city", "N/A")),
            str(pincode.get("pincode", "N/A")),
            None,                  # cookies
            "NOT_AVAILABLE"        # status
        ))


# -----------------------
# 6. BULK INSERT
# -----------------------
cursor.executemany(insert_sql, batch_data)
conn.commit()

print(f"✅ Inserted {cursor.rowcount} NOT_AVAILABLE rows")

# -----------------------
# CLEANUP
# -----------------------
cursor.close()
conn.close()
