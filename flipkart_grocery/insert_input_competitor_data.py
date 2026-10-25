# -------------------------------- competitor input ---------------------------
import pandas as pd
import pymysql
import db_config as db
import os

EXCEL_FILE = os.path.join(db.input_file_path, "sample_fkgrocery_comp_data.xlsx")

# -----------------------
# DB CONNECTION
# -----------------------
conn = db.get_db_connection(db.db_name)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# -----------------------
# 1. READ EXCEL
# -----------------------
df = pd.read_excel(EXCEL_FILE)
# 🔥 FIX NaN issue
df = df.where(pd.notnull(df), None)
# Keep only rows required for scraping
df = df[
    (df["scrape_required"] == "YES")
]

# -----------------------
# 2. READ PINCODES
# -----------------------
cursor.execute(f"""
    SELECT city, pincode
    FROM {db.pincode_table}
""")
pincodes = cursor.fetchall()

# -----------------------
# 3. INSERT QUERY
# -----------------------
insert_sql = f"""
INSERT IGNORE INTO {db.comp_availability_data_table} (
    base_product_id,
    base_brand,
    base_targeted_sku,
    base_product_name,
    base_url,
    base_sku,
    base_gramage,

    competitor_brand,
    competitor_targeted_sku,
    competitor_product_name,
    competitor_url,
    competitor_sku,
    competitor_gramage,

    city,
    pincode,
    comp_stock_availability_status,
    cookies,
    status
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
"""

# -----------------------
# 4. CREATE MATRIX & DATA
# -----------------------
batch_data = []

for _, row in df.iterrows():
    for pin in pincodes:

        # -------- HASHES --------
        # base_raw = f"{row.get('base_product_name', '')}{row.get('base_sku', '')}{pin['pincode']}"
        # client_hash_id = hashlib.sha256(base_raw.encode()).hexdigest()
        # comp_raw = f"{row.get('base_sku', '')}{row.get('competitor_targetd_sku', '')}{pin['pincode']}"
        # competitor_hash_id = hashlib.sha256(comp_raw.encode()).hexdigest()

        batch_data.append((
            # BASE PRODUCT
            None,  # base_product_id (can be filled later)
            row["base_brand"],
            row["base_targeted_sku"],
            row["base_product_name"],
            row["base_url"],
            row["base_sku"],
            row["base_gramage"],

            # COMPETITOR PRODUCT
            row["competitor_brand"],
            row["competitor_targeted_sku"],
            row["competitor_product_name"],
            row["competitor_url"],
            row["competitor_sku"],
            row["competitor_gramage"],

            # LOCATION
            pin["city"],
            pin["pincode"],

            # STATUS
            row["competitor_available"],
            None,                    # cookies
            "PENDING",               # status
        ))

# -----------------------
# 5. BULK INSERT
# -----------------------
cursor.executemany(insert_sql, batch_data)
conn.commit()

print(f"✅ Inserted {cursor.rowcount} rows into {db.comp_availability_data_table}")

# -----------------------
# CLEANUP
# -----------------------
cursor.close()
conn.close()
