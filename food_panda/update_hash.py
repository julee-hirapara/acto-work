import hashlib
from db_config_1 import get_db_connection


def generate_hash_id(url):

    hash_object = hashlib.md5(url.encode("utf-8"))
    hash_hex = hash_object.hexdigest()

    # Convert hex to integer
    hash_int = int(hash_hex, 16)

    # Keep first 12 digits
    hash_id = str(hash_int)[:12]

    return hash_id


def update_hash_ids():

    conn = get_db_connection("food_panda")
    cursor = conn.cursor()

    # Fetch rows
    select_query = """
        SELECT id, url
        FROM data_052026
        WHERE url IS NOT NULL
    """

    cursor.execute(select_query)

    rows = cursor.fetchall()

    updates = []

    for row in rows:
        print(row)
        record_id = row["id"]
        url = row["url"]

        hash_id = generate_hash_id(url)

        updates.append((hash_id, record_id))

        print(f"{record_id} -> {hash_id}")

    # Update query
    update_query = """
        UPDATE data_052026
        SET hash_id = %s
        WHERE id = %s
    """

    cursor.executemany(update_query, updates)

    conn.commit()

    print(f"{cursor.rowcount} rows updated")

    cursor.close()
    conn.close()


update_hash_ids()