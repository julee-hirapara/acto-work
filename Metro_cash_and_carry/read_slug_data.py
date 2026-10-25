import os
import pandas as pd
import db_config_1 as db
import hashlib
import pymysql
import json


# 📦 Extract full product + variant data
def extract_full_product_data(item):
    results = []
    # ✅ Parent fields
    parent_slug = item.get("slug")
    parent_item_code = item.get("item_code")
    parent_uid = item.get("uid")
    parent_weight = item.get("attributes", {}).get("mkp_weight_name")
    parent_net_qty = item.get("attributes", {}).get("net-quantity")
    parent_mrp = item.get("price", {}).get("marked", {}).get("max")
    parent_rrp = item.get("price", {}).get("effective", {}).get("max")
    parent_discount = item.get("discount")
    brand_name = item.get("brand", {}).get("name")
    category_name = None
    if item.get("categories"):
        category_name = item["categories"][0].get("name")
    # ✅ Store ID
    store_id = item.get("_custom_json", {}).get("network", {}).get("storeId")
    # ✅ Add parent row
    if parent_slug:
        results.append({
            "type": "parent",
            "parent_slug": parent_slug,
            "slug": parent_slug,
            "item_code": parent_item_code,
            "uid": parent_uid,
            "weight": parent_weight,
            "net_quantity": parent_net_qty,
            "mrp": parent_mrp,
            "rrp": parent_rrp,
            "discount": parent_discount,
            "brand": brand_name,
            "category": category_name,
            "store_id": store_id
        })
    # ✅ Variant fields
    variants = item.get("_custom_json", {}).get("variants", [])
    for variant in variants:
        variant_weight = variant.get("mkp_weight_name")
        for v_item in variant.get("items", []):
            v = v_item.get("item", {})
            slug = v.get("slug")
            if not slug:
                continue
            results.append({
                "type": "variant",
                "parent_slug": parent_slug,
                "slug": slug,
                "item_code": v.get("item_code"),
                "uid": v.get("uid"),
                "weight": variant_weight,
                "net_quantity": parent_net_qty,  # ✅ same as parent
                "mrp": v.get("mrp"),
                "rrp": v.get("rrp"),
                "discount": v.get("discountPercentage"),
                "brand": brand_name,
                "category": category_name,
                "store_id": store_id  # ✅ same store_id
            })
    return results

# 📂 Process folder
def process_folder(folder_path):
    all_rows = []
    seen_uids = set()
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    print(f"📂 Total files found: {len(files)}")
    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = data.get("items", [])
            for item in items:
                extracted = extract_full_product_data(item)
                for row in extracted:
                    uid = row.get("uid")
                    if uid and uid not in seen_uids:
                        seen_uids.add(uid)
                        row["pagesave"] = file_name   # or file_path if you want full path
                        all_rows.append(row)
        except Exception as e:
            print(f"❌ Error in {file_name}: {e}")
    print(f"✅ Total unique records: {len(all_rows)}")
    return all_rows


# 💾 Save to Excel
def save_to_excel(rows, output_file):
    df = pd.DataFrame(rows)
    # Optional sorting
    df = df.sort_values(by=["parent_slug", "type"])
    df.to_excel(output_file, index=False)
    print(f"📁 Excel saved at: {output_file}")

def insert_products(rows, pincode, city, state, state_code):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    insert_query = f"""
    INSERT INTO `{db.product_link_table}` (
        item_code,
        images,
        product_name,
        brand_name,
        weight,
        net_quantity,
        country_of_origin,
        store_id,
        mrp,
        rrp,
        discount,
        city,
        pincode,
        category_name,
        cat_slug,
        state_code,
        state,
        type,
        product_slug,
        uid,
        in_stock,
        minimum_quantity,
        maximum_quantity,
        hash_key,
        json_dict,
        status,
        pagesave
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s, %s
    )
    """

    data_to_insert = []

    for row in rows:
        slug = row.get("slug")
        store_id = row.get("store_id")

        # 🔑 UNIQUE HASH (VERY IMPORTANT)
        hash_key = hashlib.md5(f"{slug}_{store_id}".encode()).hexdigest()

        values = (
            row.get("item_code"),
            None,  # images (you can fill later)
            None,  # product_name (optional)
            row.get("brand"),
            row.get("weight"),
            row.get("net_quantity"),
            "India",
            store_id,
            row.get("mrp"),
            row.get("rrp"),
            row.get("discount"),
            city,
            pincode,
            row.get("category"),
            None,  # cat_slug
            state_code,  # state_code (adjust if dynamic)
            state,
            row.get("type"),
            slug,
            row.get("uid"),
            None,  # in_stock
            None,
            None,
            hash_key,
            json.dumps(row),
            "pending",
            row.get("pagesave")
        )

        data_to_insert.append(values)

    try:
        cursor.executemany(insert_query, data_to_insert)
        conn.commit()
        print(f"✅ Inserted/Updated: {len(data_to_insert)} records")

    except Exception as e:
        print(f"❌ Insert error: {e}")

    finally:
        cursor.close()
        conn.close()

def main():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = f"""SELECT * FROM {db.pincode_table} WHERE pincode='700099' """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        print("❌ No pincode found")
        return
    for r in rows:
        try:
            pincode = r["pincode"]
            city = r["city"]
            state = r["state"]
            state_code = r["state_code"]
            print(f"\n🚀 Running for {pincode} - {city}")
            # 🔁 CHANGE THIS PATH
            folder_path = os.path.join(db.PL_PAGESAVE, f"search_pages_{pincode}")
            # Z:\Team_Neela\Julee\PAGESAVES\metro_cash_and_carry\04_2026\PL\search_pages_700001
            # folder_path = r"D:\Julee\PAGESAVES\metro_cash_and_carry\21_04_2026\PL\search_pages"
            output_file = "product_variant_data.xlsx"

            rows = process_folder(folder_path)
            insert_products(rows,pincode, city, state, state_code)
            save_to_excel(rows, output_file)
        except Exception as e:
            print(f"❌ Error for {r}: {e}")

# ▶️ MAIN
if __name__ == "__main__":
    main()


