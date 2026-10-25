import db_config as db
import traceback

CITIES = [
    "Lucknow", "Noida", "Ghaziabad", "Kanpur", "Gorakhpur",
    "Prayagraj", "Varanasi", "Patna", "Delhi", "Gurgaon",
    "Faridabad", "Jaipur", "Bangalore", "Mysore",
    "Chandigarh", "Ludhiana", "Indore", "Dehradoon",
    "Kolkata", "Chennai", "Ranchi", "Raipur"
]

def insert_city_pincodes(cities):
    master_conn = None
    target_conn = None
    master_cursor = None
    target_cursor = None

    try:
        master_conn = db.get_db_connection(db.MASTER_DB_PINCODE)
        target_conn = db.get_db_connection(db.db_name)

        master_cursor = master_conn.cursor()
        target_cursor = target_conn.cursor()

        city_placeholders = ", ".join(["%s"] * len(cities))

        fetch_query = f"""
        SELECT
            District AS city,
            Pincode,
            Post_Office,
            State,
            District,
            Taluk,
            Latitude,
            Longitude
        FROM {db.MASTER_PINCODE_TABLE}
        WHERE District IN ({city_placeholders})
        """

        master_cursor.execute(fetch_query, cities)
        rows = master_cursor.fetchall()

        if not rows:
            print("No pincodes found for given cities")
            return

        insert_query = f"""
        INSERT INTO {db.pincode_table} (
            city, pincode, post_office, state, district,
            taluk, latitude, longitude, status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        insert_values = [
            (
                r["city"],
                r["Pincode"],
                r["Post_Office"],
                r["State"],
                r["District"],
                r["Taluk"],
                r["Latitude"],
                r["Longitude"],
                "PENDING"
            )
            for r in rows
        ]

        target_cursor.executemany(insert_query, insert_values)
        target_conn.commit()

        print(f"Inserted {len(insert_values)} pincodes successfully")

    except Exception:
        print("City pincode insert failed!")
        print(traceback.format_exc())

    finally:
        if master_cursor is not None:
            master_cursor.close()
        if target_cursor is not None:
            target_cursor.close()
        if master_conn is not None:
            master_conn.close()
        if target_conn is not None:
            target_conn.close()


if __name__ == "__main__":
    insert_city_pincodes(CITIES)
