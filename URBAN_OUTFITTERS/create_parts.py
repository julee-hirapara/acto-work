import math
import db_config_1 as db
import pymysql.cursors
# --- Configuration ---
python_path = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"
script_name = "pdp_4.py"
chunk_size = 50


# --- 1. Fetch Pending IDs ---
# This is a placeholder for your DB logic
def get_pending_ids():
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(f"Select * from {db.link_table} where status='pending'")
    records = [row['id'] for row in cur.fetchall()]
    conn.close()
    return records


pending_ids = get_pending_ids()
total_records = len(pending_ids)

bat_lines = []

# --- 2. Divide into Parts ---
for i in range(0, total_records, chunk_size):
    # Get the slice of IDs for this chunk
    chunk = pending_ids[i: i + chunk_size]

    start_id = chunk[0]
    end_id = chunk[-1]

    batch_no = (i // chunk_size) + 1

    # Create the command
    line = (
        f'start "Batch {batch_no}" '
        f'"{python_path}" {script_name} {start_id} {end_id}'
    )
    bat_lines.append(line)

# --- 3. Save File ---
with open("run_pdp_bat.bat", "w") as f:
    f.write("\n".join(bat_lines))

print(f"Created BAT file for {total_records} pending records in {len(bat_lines)} batches.")