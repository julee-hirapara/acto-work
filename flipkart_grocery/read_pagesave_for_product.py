# import json
# import time
# import random
# import pymysql
# import db_config as db
# from concurrent.futures import ThreadPoolExecutor
#
# # =============================
# # HELPERS
# # =============================
#
# def clean_text(text):
#     if not text:
#         return None
#     return " ".join(text.split())
#
# def read_page_save(hash_key):
#     path = f"{db.DATA_PAGESAVE}\\{hash_key}.json"
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)
#
# # =============================
# # EXTRACTION
# # =============================
#
# def extract_pricing(response):
#     pricing = (
#         response.get("pageData", {})
#         .get("pageContext", {})
#         .get("pricing", {})
#     )
#
#     price = pricing.get("finalPrice", {}).get("value") or pricing.get("fsp")
#     mrp = pricing.get("mrp")
#
#     if mrp is None:
#         for p in pricing.get("prices", []):
#             if p.get("priceType") == "MRP":
#                 mrp = p.get("value")
#                 break
#
#     discount = pricing.get("totalDiscount")
#     if discount is None:
#         for p in pricing.get("prices", []):
#             if p.get("discount") is not None:
#                 discount = p.get("discount")
#                 break
#
#     return mrp, price, discount
#
# def extract_product_data(response):
#     if "RESPONSE" in response:
#         response = response["RESPONSE"]
#
#     description = clean_text(
#         response.get("pageData", {})
#         .get("pageContext", {})
#         .get("seo", {})
#         .get("description")
#     )
#
#     images = (
#         response.get("slots", [{}])[0]
#         .get("widget", {})
#         .get("data", {})
#         .get("renderableComponents", [{}])[0]
#         .get("value", {})
#         .get("media", {})
#         .get("images", [])
#     )
#
#     image_urls = []
#     for img in images:
#         if img.get("url"):
#             image_urls.append(
#                 img["url"]
#                 .replace("{@width}", "832")
#                 .replace("{@height}", "832")
#                 .replace("{@quality}", "90")
#             )
#
#     image_url = "|".join(image_urls) if image_urls else None
#     mrp, price, discount = extract_pricing(response)
#
#     return description, image_url, mrp, price, discount
#
# # =============================
# # DB UPDATE
# # =============================
#
# def update_product(row):
#     try:
#         hash_key = row["hash_key"]
#         response = read_page_save(hash_key)
#
#         description, image_url, mrp, price, discount = extract_product_data(response)
#
#         conn = db.get_db_connection(db.db_name)
#         cur = conn.cursor()
#
#         cur.execute(f"""
#             UPDATE {db.availability_data_table}
#             SET
#                 description = %s,
#                 image_url = %s,
#                 mrp = %s,
#                 price = %s,
#                 discount_percent = %s,
#                 status = 'SCRAPED'
#             WHERE hash_key = %s
#         """, (description, image_url, mrp, price, discount, hash_key))
#
#         conn.commit()
#         cur.close()
#         conn.close()
#
#         print(f"✅ Updated product {hash_key}")
#         time.sleep(random.uniform(0.3, 0.6))
#
#     except Exception as e:
#         print(f"❌ Error {row['hash_key']}: {e}")
#
# # =============================
# # MAIN
# # =============================
#
# def main():
#     conn = db.get_db_connection(db.db_name)
#     cur = conn.cursor(pymysql.cursors.DictCursor)
#
#     cur.execute(f"""
#         SELECT hash_key
#         FROM {db.availability_data_table}
#         WHERE status = 'DONE'
#           AND hash_key IS NOT NULL
#     """)
#
#     rows = cur.fetchall()
#     cur.close()
#     conn.close()
#
#     print(f"📦 Products to scrape: {len(rows)}")
#
#     with ThreadPoolExecutor(max_workers=5) as executor:
#         executor.map(update_product, rows)
#
#     print("🎉 PRODUCT TABLE UPDATED")
#
# if __name__ == "__main__":
#     main()


import json
import time
import random
import pymysql
import db_config as db
from concurrent.futures import ThreadPoolExecutor

# ======================================================
# SAFE HELPERS
# ======================================================

def safe_dict(obj):
    return obj if isinstance(obj, dict) else {}

def safe_list(obj):
    return obj if isinstance(obj, list) else []

def read_page_save(hash_key):
    path = f"{db.DATA_PAGESAVE}\\{hash_key}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ======================================================
# SAFE EXTRACTION
# ======================================================

def extract_pricing_safe(response):
    response = safe_dict(response)
    page_data = safe_dict(response.get("pageData"))
    page_ctx = safe_dict(page_data.get("pageContext"))
    pricing = safe_dict(page_ctx.get("pricing"))

    price = (
        safe_dict(pricing.get("finalPrice")).get("value")
        or pricing.get("fsp")
        or 0
    )

    mrp = pricing.get("mrp") or 0

    if not mrp:
        for p in safe_list(pricing.get("prices")):
            if p.get("priceType") == "MRP":
                mrp = p.get("value") or 0
                break

    discount = pricing.get("totalDiscount") or 0

    if not discount:
        for p in safe_list(pricing.get("prices")):
            if p.get("discount") is not None:
                discount = p.get("discount") or 0
                break

    return mrp, price, discount


def extract_product_data_safe(response):
    if isinstance(response, dict) and "RESPONSE" in response:
        response = response["RESPONSE"]

    response = safe_dict(response)

    # -------- DESCRIPTION --------
    description = (
        safe_dict(response.get("pageData"))
        .get("pageContext", {})
        .get("seo", {})
        .get("description")
    )
    description = description if description else "N/A"

    # -------- IMAGES --------
    image_url = (
        safe_dict(response.get("pageData"))
        .get("pageContext", {})
        .get("imageUrl", "")
    )

    if image_url:
        image_url = (
            image_url.replace("{@width}", "832")
            .replace("{@height}", "832")
            .replace("{@quality}", "90")
        )
        print(image_url)
    else:
        image_url = "N/A"
    # images = (
    #     safe_dict(
    #         safe_list(response.get("slots"))[0]
    #     )
    #     .get("widget", {})
    #     .get("data", {})
    #     .get("renderableComponents", [{}])[0]
    #     .get("value", {})
    #     .get("media", {})
    #     .get("images", [])
    # )
    #
    # image_urls = []
    # for img in safe_list(images):
    #     url = img.get("url")
    #     if url:
    #         image_urls.append(
    #             url.replace("{@width}", "832")
    #                .replace("{@height}", "832")
    #                .replace("{@quality}", "90")
    #         )
    #
    # image_url = "|".join(image_urls) if image_urls else "N/A"

    # -------- PRICING --------
    mrp, price, discount = extract_pricing_safe(response)

    return description, image_url, mrp, price, discount

# ======================================================
# DATABASE UPDATE
# ======================================================

def update_product(row):
    hash_key = row["hash_key"]
    stock_status = row["stock_availability_status"]
    print(stock_status)
    # -------------------------------
    # CASE 1: STOCK READY → FORCE N/A
    # -------------------------------
    if stock_status == "ready":
        description, image_url, mrp, price, discount = "N/A", "N/A", 0, 0, 0
    # --------------------------------
    # CASE 2: TRY SCRAPING PAGESAVE
    # --------------------------------
    else:
        try:
            response = read_page_save(hash_key)
            description, image_url, mrp, price, discount = extract_product_data_safe(response)
        except Exception as e:
            print(f"⚠️ Pagesave broken {hash_key}: {e}")
            description, image_url, mrp, price, discount = "N/A", "N/A", 0, 0, 0

    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE {db.availability_data_table}
        SET
            description = %s,
            image_url = %s,
            mrp = %s,
            price = %s,
            discount_percent = %s,
            status = 'SCRAPED'
        WHERE hash_key = %s
    """, (
        description,
        image_url,
        mrp,
        price,
        discount,
        hash_key
    ))

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Updated {hash_key}")
    time.sleep(random.uniform(0.3, 0.6))

# ======================================================
# MAIN
# ======================================================

def main():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(f"""
        SELECT *
        FROM {db.availability_data_table}
        WHERE status = 'DONE'
          AND hash_key IS NOT NULL
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    print(rows)
    print(f"📦 Rows to update: {len(rows)}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(update_product, rows)

    print("🎉 PRODUCT TABLE UPDATED SUCCESSFULLY")

def update_competitor_from_base():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE {db.comp_availability_data_table} c
        JOIN {db.availability_data_table} b
            ON c.base_product_name = b.product_name
           AND c.pincode = b.pincode
        SET
            c.description = b.description,
            c.image_url = b.image_url,
            c.price = b.price,
            c.mrp = b.mrp,
            c.discount_percent = b.discount_percent,
            c.client_stock_availability_status = b.stock_availability_status,
            c.client_hash_id = b.hash_key
        WHERE b.status = 'SCRAPED'
          AND b.price >= 0
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("🎯 Competitor table synced successfully")

# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":
    # main()
    update_competitor_from_base()