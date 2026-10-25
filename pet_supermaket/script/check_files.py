import os
import db_config_1 as db

FOLDER_PATH = db.PDP_PAGESAVE

def get_db_hashes():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT hash_key 
        FROM {db.link_table} 
        WHERE status = 'done'
    """)

    rows = cursor.fetchall()
    conn.close()

    return set(row['hash_key'] for row in rows)


def get_folder_hashes():
    files = os.listdir(FOLDER_PATH)

    hashes = set()
    for f in files:
        if f.endswith(".html"):
            hash_key = os.path.splitext(f)[0]
            hashes.add(hash_key)

    return hashes


def compare():
    db_hashes = get_db_hashes()
    folder_hashes = get_folder_hashes()

    # 1️⃣ Files exist but NOT in DB
    extra_files = folder_hashes - db_hashes

    # 2️⃣ DB entries exist but file missing
    missing_files = db_hashes - folder_hashes

    print("\n✅ Files present in folder but NOT in DB:")
    for h in extra_files:
        print(h)

    print("\n❌ Files missing in folder but present in DB:")
    for h in missing_files:
        print(h)

    print("\n📊 Summary:")
    print("DB count:", len(db_hashes))
    print("Folder count:", len(folder_hashes))
    print("Extra files:", len(extra_files))
    print("Missing files:", len(missing_files))


if __name__ == "__main__":
    compare()