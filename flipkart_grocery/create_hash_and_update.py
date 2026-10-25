import hashlib

def generate_competitor_hash(competitor_sku, base_sku, pincode):
    raw = f"{competitor_sku}|{base_sku}|{pincode}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


import pymysql
import db_config as db


def backfill_competitor_hash_ids(batch_size=1000):
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    while True:
        # 1️⃣ Read rows needing hash
        cur.execute(f"""
            SELECT id,
                   competitor_targeted_sku,
                   base_targeted_sku,
                   pincode
            FROM {db.comp_availability_data_table}
            WHERE competitor_hash_id IS NULL AND STATUS ='PENDING'
            LIMIT %s
        """, (batch_size,))

        rows = cur.fetchall()
        if not rows:
            break

        update_data = []
        for r in rows:
            hash_key = generate_competitor_hash(
                r["competitor_targeted_sku"],
                r["base_targeted_sku"],
                r["pincode"]
            )
            update_data.append((hash_key, r["id"]))

        # 2️⃣ Bulk update
        cur.executemany(f"""
            UPDATE {db.comp_availability_data_table}
            SET competitor_hash_id = %s
            WHERE id = %s
        """, update_data)

        conn.commit()
        print(f"✔ Updated {cur.rowcount} hash_keys")

    cur.close()
    conn.close()
    print("🎯 Hash backfill completed")

if __name__ == "__main__":
    backfill_competitor_hash_ids()
