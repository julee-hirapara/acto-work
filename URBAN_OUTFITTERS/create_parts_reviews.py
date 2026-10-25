import math
import db_config_1 as db
import pymysql.cursors

# --- Configuration ---
python_path = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
script_name = "review.py"

num_parts = 5


# --- Fetch Pending IDs ---
def get_pending_ids():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    cur.execute(f"""
        SELECT DISTINCT pid, hash_id
        FROM {db.data_table}
        WHERE status_review='pending'
        AND num_ratings IS NOT NULL
    """)

    records = cur.fetchall()

    conn.close()

    # choose the correct field
    return [row['pid'] for row in records]


pending_ids = get_pending_ids()

total_records = len(pending_ids)

# Calculate chunk size automatically
chunk_size = math.ceil(total_records / num_parts)

bat_lines = []

# --- Divide into Parts ---
for i in range(0, total_records, chunk_size):

    chunk = pending_ids[i:i + chunk_size]

    start_id = chunk[0]
    end_id = chunk[-1]

    batch_no = (i // chunk_size) + 1

    line = (
        f'start "Batch {batch_no}" '
        f'"{python_path}" {script_name} {start_id} {end_id}'
    )

    bat_lines.append(line)

# --- Save BAT File ---
with open("run_review_bat.bat", "w") as f:
    f.write("\n".join(bat_lines))

print(f"Created {len(bat_lines)} batches.")