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
    path = f"{db.C_DATA_PAGESAVE}\\{hash_key}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ======================================================
# SAFE PRICING EXTRACTION
# ======================================================

def extract_competitor_pricing(response):
    if isinstance(response, dict) and "RESPONSE" in response:
        response = response["RESPONSE"]

    response = safe_dict(response)

    pricing = (
        safe_dict(response.get("pageData"))
        .get("pageContext", {})
        .get("pricing", {})
    )

    # -------- PRICE --------
    price = (
        safe_dict(pricing.get("finalPrice")).get("value")
        or pricing.get("fsp")
        or 0
    )

    # -------- MRP --------
    mrp = pricing.get("mrp") or 0
    if not mrp:
        for p in safe_list(pricing.get("prices")):
            if p.get("priceType") == "MRP":
                mrp = p.get("value") or 0
                break

    # -------- DISCOUNT --------
    discount = pricing.get("totalDiscount") or 0
    if not discount:
        for p in safe_list(pricing.get("prices")):
            if p.get("discount") is not None:
                discount = p.get("discount") or 0
                break

    return mrp, price, discount

# ======================================================
# UPDATE COMPETITOR ROW
# ======================================================

def update_competitor(row):
    comp_hash = row["competitor_hash_id"]

    try:
        response = read_page_save(comp_hash)
        mrp, price, discount = extract_competitor_pricing(response)
        # stock_status = "AVAILABLE" if price > 0 else "NOT_AVAILABLE"

    except Exception as e:
        print(f"⚠️ Broken pagesave {comp_hash}: {e}")
        mrp, price, discount = 0, 0, 0
        # stock_status = "NOT_AVAILABLE"

    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE {db.comp_availability_data_table}
        SET
            competitor_mrp = %s,
            competitor_price = %s,
            competitor_discount = %s,
            status = 'SCRAPED'
        WHERE competitor_hash_id = %s
    """, (
        mrp,
        price,
        discount,
        # stock_status,
        comp_hash
    ))
    # comp_stock_availability_status = %s,
    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Competitor updated: {comp_hash}")
    time.sleep(random.uniform(0.3, 0.6))

# ======================================================
# MAIN
# ======================================================

def main():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(f"""
        SELECT competitor_hash_id
        FROM {db.comp_availability_data_table}
        WHERE status = 'SUCCESS'
          AND competitor_hash_id IS NOT NULL
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    print(f"📦 Competitor rows to scrape: {len(rows)}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(update_competitor, rows)

    print("🎉 COMPETITOR TABLE UPDATED SUCCESSFULLY")


def update_price_discount_difference():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE {db.comp_availability_data_table}
        SET
            price_difference = 
                IF(
                    price IS NOT NULL 
                    AND price > 0 
                    AND competitor_price IS NOT NULL 
                    AND competitor_price > 0,
                    price - competitor_price,
                    'N/A'
                ),

            discount_difference = 
                IF(
                    discount_percent IS NOT NULL 
                    AND discount_percent > 0 
                    AND competitor_discount IS NOT NULL 
                    AND competitor_discount > 0,
                    discount_percent - competitor_discount,
                    'N/A'
                )
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Price & Discount difference updated")

# import pymysql
# import db_config as db
#
# def update_price_discount_difference():
#     conn = db.get_db_connection(db.db_name)
#     cur = conn.cursor()
#
#     cur.execute(f"""
#         UPDATE {db.comp_availability_data_table}
#         SET
#             price_difference = CASE
#                 WHEN price IS NOT NULL
#                      AND price > 0
#                      AND competitor_price IS NOT NULL
#                      AND competitor_price > 0
#                 THEN price - competitor_price
#                 ELSE 'N/A'
#             END,
#
#             discount_difference = CASE
#                 WHEN discount_percent IS NOT NULL
#                      AND discount_percent > 0
#                      AND competitor_discount IS NOT NULL
#                      AND competitor_discount > 0
#                 THEN discount_percent - competitor_discount
#                 ELSE 'N/A'
#             END
#         WHERE status = 'SCRAPED'
#     """)
#
#     conn.commit()
#     cur.close()
#     conn.close()
#
#     print("✅ Price & Discount differences updated successfully")

# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":
    # main()
    update_price_discount_difference()