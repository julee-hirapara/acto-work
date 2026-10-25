import os
import csv
from openpyxl import Workbook
import db_config_1 as db
from datetime import datetime

current_date = datetime.now().strftime("%Y%m%d")

# -----------------------------
# CONNECT DB
# -----------------------------
conn = db.get_db_connection(db.db_name)
cursor = conn.cursor()
file_name_excel = os.path.join(db.RESULT_PATH, f"pet_supermarket_{current_date}.xlsx")
file_name_csv = os.path.join(db.RESULT_PATH, f"pet_supermarket_{current_date}.csv")
# -----------------------------
# FETCH DATA
# -----------------------------
query = f"""
SELECT
    website,
    pid,
    name,
    short_description,
    description,
    category,
    image_url,
    price,
    price_currency,
    sale_price,
    final_price,
    discount,
    is_on_sale,
    is_in_stock,
    keywords,
    brand,
    manufacturer,
    mpn,
    upc_ean,
    sku,
    colour,
    gender,
    size,
    variant_price,
    alternate_image_urls,
    main_url,
    num_ratings,
    avg_ratings,
    hash_id,
    coupons_and_offers,
    delivery_ETA,
    shipping_cost,
    return_fee,
    tags,
    review_summary,
    return_policy,
    created_at,
    created_at,
    reviews
FROM {db.data_table}
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f"Total records: {len(rows)}")

# -----------------------------
# EXCEL SETUP
# -----------------------------
wb = Workbook()
ws = wb.active
ws.title = "Data"

headers = [
    "S.No.","Website","PID","Name","Short Description","Description",
    "Category","Image URL","Price","Price Currency","Sale Price",
    "Final Price","Discount","IsOnSale","IsInStock","Keywords",
    "Brand","Manufacturer","MPN","UPC or EAN","SKU","Colour",
    "Gender","Size","Size Chart","Tags", "Other_fields", "Varint_Price","Alternate Image URLs",
    "Link URL","Num Ratings","Average Ratings","Reviews","hash_id",
    "Coupons & Offers","Delivery ETA","Crawl Date-Time",
    "Shipping Cost","Return Fee","Review Summary","Return Policy"
]

ws.append(headers)
csv_file = open(file_name_csv, "w", newline="", encoding="utf-8-sig")
csv_writer = csv.writer(csv_file)

# write headers
csv_writer.writerow(headers)
def na_if_zero(value):
    return "N/A" if value in (0, 0.0,0.00, None) else value

# -----------------------------
# WRITE DATA
# -----------------------------
for i, row in enumerate(rows, 1):

    # 👉 Variant hash (unique per SKU)
    variant_hash_id = row["sku"]
    if row.get("num_ratings") == 0:
        num_rating = "N/A"
    else:
        num_rating = row.get("num_ratings")
    if row.get("avg_ratings") == 0.0:
        avg_ratings = "N/A"
    else:
        avg_ratings = row.get("avg_ratings")
    price = na_if_zero(row.get("price"))
    sale_price = na_if_zero(row.get("sale_price"))
    final_price = na_if_zero(row.get("final_price"))
    discount = na_if_zero(row.get("discount"))
    variant_price = na_if_zero(row.get("variant_price"))
    price_currency = "N/A" if sale_price == 'N/A' else 'USD'
    reviews = na_if_zero(row.get("reviews"))
    if price != "N/A" and final_price != "N/A" and price is not None and final_price is not None:
        if price-final_price > 0:
            isonsale = "Yes"
        else:
            isonsale = "No"
    else:
        isonsale = "No"
    excel_row = [
        i,
        row.get("website"),
        row.get("pid"),
        row.get("name"),
        row.get("short_description"),
        row.get("description"),
        row.get("category"),
        row.get("image_url"),
        # row.get("price"),
        price,
        # row.get("price_currency"),
        price_currency,
        # row.get("sale_price"),
        sale_price,
        # row.get("final_price"),
        final_price,
        # row.get("discount"),
        discount,
        # row.get("is_on_sale"),
        isonsale,
        row.get("is_in_stock"),
        row.get("keywords"),
        row.get("brand"),
        row.get("manufacturer"),
        row.get("mpn"),
        row.get("upc_ean"),
        row.get("sku"),
        row.get("colour"),
        row.get("gender"),
        row.get("size"),
        "N/A",
        "N/A",
        # row.get("variant_price"),
        "N/A",
        variant_price,
        row.get("alternate_image_urls"),
        row.get("main_url"),
        num_rating,
        avg_ratings,
        reviews,
        str(row.get("hash_id"))[:12],
        row.get("coupons_and_offers") if row.get("coupons_and_offers") else "N/A",
        "N/A",
        row.get("created_at"),
        "N/A",
        "N/A",
        "N/A",
        row.get("return_policy"),

    ]
    excel_row = [" ".join(str(v).split()) if isinstance(v, str) else v for v in excel_row]
    ws.append(excel_row)
    csv_writer.writerow(excel_row)

# -----------------------------
# SAVE FILE
# -----------------------------
wb.save(file_name_excel)
print(f"\n✅ Excel Created: {file_name_excel}")
# -----------------------------
# CLOSE DB
# -----------------------------
conn.close()
csv_file.close()

# #
# # ############################################################################################
# #
# # import os
# # import shutil
# # import pymysql
# # from pathlib import Path
# # import db_config_1 as db
# #
# # # PageSave source folder
# # PAGESAVE_FOLDER = r"D:\Julee\PAGESAVES\pet_supermarket\092026\PDP"
# # variation_folder = r"D:\Julee\PAGESAVES\pet_supermarket\092026\PDP\variation_pagesave"
# #
# # # Destination for HTML main pages
# # HTML_DESTINATION = Path(
# #     r"D:\Julee\PAGESAVES\pet_supermarket_moved\html"
# # )
# #
# # # Destination for JSON variation pages
# # JSON_DESTINATION = Path(
# #     r"D:\Julee\PAGESAVES\pet_supermarket_moved\variation"
# # )
# #
# # # ============================================================
# # # CREATE DESTINATION FOLDERS
# # # ============================================================
# # HTML_DESTINATION.mkdir(parents=True, exist_ok=True)
# # JSON_DESTINATION.mkdir(parents=True, exist_ok=True)
# #
# # # ============================================================
# # # READ DB
# # # ============================================================
# # def get_db_values():
# #     conn = db.get_db_connection(db.db_name)
# #     cursor = conn.cursor()
# #
# #     cursor.execute("""
# #         SELECT hash_id, sku
# #         FROM `data_092026`
# #     """)
# #
# #     rows = cursor.fetchall()
# #
# #     print("\nFirst 10 rows:")
# #     for row in rows[:10]:
# #         print(row)
# #
# #     print(f"Total DB rows: {len(rows):,}")
# #
# #     hash_ids = set()
# #     skus = set()
# #
# #     for row in rows:
# #         hash_id = row.get("hash_id")
# #         sku = row.get("sku")
# #
# #         if hash_id is not None:
# #             hash_id = str(hash_id).strip()
# #             if hash_id:
# #                 hash_ids.add(hash_id)
# #
# #         if sku is not None:
# #             sku = str(sku).strip()
# #             if sku:
# #                 skus.add(sku)
# #
# #     cursor.close()
# #     conn.close()
# #
# #     print(f"Unique hash_ids: {len(hash_ids):,}")
# #     print(f"Unique skus    : {len(skus):,}")
# #
# #     return hash_ids, skus
# # # ============================================================
# # # SAFE MOVE
# # # ============================================================
# # def move_file(source_file, destination_folder):
# #     destination_file = destination_folder / source_file.name
# #     # If same filename already exists,
# #     # don't overwrite it.
# #     if destination_file.exists():
# #         print(f"[SKIP - EXISTS] {source_file.name}")
# #         return False
# #     shutil.move(str(source_file), str(destination_file))
# #     return True
# #
# # # ============================================================
# # # MAIN
# # # ============================================================
# # def main():
# #     print("=" * 80)
# #     print("PET SUPERMARKET PAGESAVE CLEANUP")
# #     print("=" * 80)
# #     # --------------------------------------------------------
# #     # READ DATABASE
# #     # --------------------------------------------------------
# #     print("\nReading database...")
# #     hash_ids, skus = get_db_values()
# #     print(f"DB hash_id count : {len(hash_ids):,}")
# #     print(f"DB SKU count     : {len(skus):,}")
# #     # quit()
# #     # --------------------------------------------------------
# #     # SCAN PAGESAVE
# #     # --------------------------------------------------------
# #     print("\nScanning PageSave folder...")
# #     html_files = []
# #     json_files = []
# #     # ============================================================
# #     # SCAN MAIN PAGESAVE - HTML ONLY
# #     # ============================================================
# #     for root, dirs, files in os.walk(PAGESAVE_FOLDER):
# #         root_path = Path(root)
# #         # Skip variation folder
# #         dirs[:] = [
# #             d for d in dirs
# #             if (root_path / d).resolve() != Path(variation_folder).resolve()
# #         ]
# #         for filename in files:
# #             if filename.lower().endswith(".html"):
# #                 html_files.append(root_path / filename)
# #     # ============================================================
# #     # SCAN VARIATION PAGESAVE - JSON ONLY
# #     # ============================================================
# #     for root, dirs, files in os.walk(variation_folder):
# #         root_path = Path(root)
# #         for filename in files:
# #             if filename.lower().endswith(".json"):
# #                 json_files.append(root_path / filename)
# #     print(f"HTML PageSave files : {len(html_files):,}")
# #     print(f"JSON variation files: {len(json_files):,}")
# #
# #     # ========================================================
# #     # MAIN HTML FILES
# #     # Match filename with hash_id
# #     # ========================================================
# #     print("\n" + "=" * 80)
# #     print("CHECKING HTML FILES USING hash_id")
# #     print("=" * 80)
# #     moved_html = 0
# #
# #     html_file_map = {
# #         file_path.stem.strip(): file_path
# #         for file_path in html_files
# #     }
# #
# #     # PageSave hash_ids which are NOT present in DB
# #     extra_hash_ids = set(html_file_map.keys()) - hash_ids
# #
# #     print(f"Extra HTML files not in DB: {len(extra_hash_ids):,}")
# #
# #     for hash_id in extra_hash_ids:
# #         file_path = html_file_map[hash_id]
# #
# #         try:
# #             if move_file(file_path, HTML_DESTINATION):
# #                 moved_html += 1
# #                 print(f"[HTML MOVED - NOT IN DB] {file_path.name}")
# #         except Exception as e:
# #             print(f"[ERROR] {file_path} -> {e}")
# #     # ========================================================
# #     # VARIATION JSON FILES
# #     # Match filename with SKU
# #     # ========================================================
# #     print("\n" + "=" * 80)
# #     print("CHECKING JSON FILES USING SKU")
# #     print("=" * 80)
# #     moved_json = 0
# #
# #     json_file_map = {
# #         file_path.stem.strip(): file_path
# #         for file_path in json_files
# #     }
# #
# #     # PageSave SKUs which are NOT present in DB
# #     extra_skus = set(json_file_map.keys()) - skus
# #
# #     print(f"Extra JSON files not in DB: {len(extra_skus):,}")
# #
# #     for sku in extra_skus:
# #         file_path = json_file_map[sku]
# #
# #         try:
# #             if move_file(file_path, JSON_DESTINATION):
# #                 moved_json += 1
# #                 print(f"[JSON MOVED - SKU NOT IN DB] {file_path.name}")
# #         except Exception as e:
# #             print(f"[ERROR] {file_path} -> {e}")
# #     # ========================================================
# #     # SUMMARY
# #     # ========================================================
# #     print("\n" + "=" * 80)
# #     print("FINAL SUMMARY")
# #     print("=" * 80)
# #     print(f"DB hash_id count       : {len(hash_ids):,}")
# #     print(f"HTML PageSave count    : {len(html_files):,}")
# #     print(f"HTML moved             : {moved_html:,}")
# #     print(f"HTML extra/not in DB   : {len(extra_hash_ids):,}")
# #     print(f"DB SKU count           : {len(skus):,}")
# #     print(f"JSON variation count   : {len(json_files):,}")
# #     print(f"JSON moved             : {moved_json:,}")
# #     print(f"JSON extra/not in DB   : {len(extra_skus):,}")
# #     print(f"TOTAL MOVED            : {moved_html + moved_json:,}")
# #     print("\nDestinations:")
# #     print(f"HTML : {HTML_DESTINATION}")
# #     print(f"JSON : {JSON_DESTINATION}")
# #     print("\nCompleted.")
# #
# #
# # # ============================================================
# # # RUN
# # # ============================================================
# #
# # if __name__ == "__main__":
# #     main()
#
# #######################################################################################################
# #
# import subprocess
# from pathlib import Path
#
# DESTINATION = Path(
#     r"Z:\Team_Neela\Projects\act-plssav-7725-non-fashion-data-collection-from-39-websites\Pet Supermarket\Pagesave\092026\PDP"
# )
#
# SOURCE = Path(
#     r"D:\Julee\PAGESAVES\pet_supermarket\092026\PDP"
# )
#
# print("=" * 80)
# print("COPYING PAGESAVE FOLDER")
# print("=" * 80)
#
# print(f"Source      : {SOURCE}")
# print(f"Destination : {DESTINATION}")
#
# DESTINATION.mkdir(parents=True, exist_ok=True)
#
# command = [
#     "robocopy",
#     str(SOURCE),
#     str(DESTINATION),
#
#     # Copy all files/subfolders
#     "/E",
#
#     # Multi-threaded copy
#     "/MT:32",
#
#     # Retry settings
#     "/R:2",
#     "/W:2",
#
#     # Preserve file data, attributes and timestamps
#     "/COPY:DAT",
#
#     # Don't print every copied file
#     "/NFL",
#     "/NDL",
#     "/NP",
#
#     # Show summary
#     "/ETA",
# ]
#
# print("\nStarting copy...\n")
#
# result = subprocess.run(command)
#
# print("\n" + "=" * 80)
#
# # Robocopy exit codes 0-7 are normally successful/non-fatal
# if result.returncode <= 7:
#     print("COPY COMPLETED SUCCESSFULLY")
#     print(f"Robocopy exit code: {result.returncode}")
# else:
#     print("COPY FAILED / HAD ERRORS")
#     print(f"Robocopy exit code: {result.returncode}")
#
# print("=" * 80)