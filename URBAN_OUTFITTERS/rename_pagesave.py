import os
import pymysql
import db_config_1 as db

# =========================
# CONFIG
# =========================
FOLDER_PATH = r"Z:\julee\PAGESAVES\Urban_Outfitters\05_2026\review"

# =========================
# DB CONNECTION
# =========================
conn = db.get_db_connection(db.db_name)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# =========================
# LOAD PID -> HASH_ID MAP
# =========================
print("Loading DB mapping...")

cursor.execute(f"""
    SELECT DISTINCT pid, hash_id
    FROM {db.data_table}
    WHERE pid IS NOT NULL
    AND hash_id IS NOT NULL
""")

rows = cursor.fetchall()

pid_map = {
    row["pid"].strip(): str(row["hash_id"]).strip()
    for row in rows
}

print(f"Loaded {len(pid_map)} pid mappings")

# =========================
# RENAME FILES
# =========================
renamed = 0
skipped = 0
not_found = 0

files = os.listdir(FOLDER_PATH)

for file_name in files:

    # only process UO files
    if not file_name.startswith("UO-"):
        continue

    # only review json files
    if not file_name.endswith("_review.json"):
        continue

    try:
        # remove suffix
        pid = file_name.replace("_review.json", "").strip()

        # find hash_id
        hash_id = pid_map.get(pid)

        if not hash_id:
            print(f"❌ PID not found in DB: {pid}")
            not_found += 1
            continue

        old_path = os.path.join(FOLDER_PATH, file_name)

        new_file_name = f"{hash_id}_review.json"
        new_path = os.path.join(FOLDER_PATH, new_file_name)

        # skip if already exists
        if os.path.exists(new_path):
            print(f"⚠ Already exists: {new_file_name}")
            skipped += 1
            continue

        os.rename(old_path, new_path)

        print(f"✅ {file_name}  -->  {new_file_name}")

        renamed += 1

    except Exception as e:
        print(f"❌ Error for {file_name}: {e}")

# =========================
# DONE
# =========================
cursor.close()
conn.close()

print("\n======================")
print(f"Renamed : {renamed}")
print(f"Skipped : {skipped}")
print(f"Not Found : {not_found}")
print("======================")