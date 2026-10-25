import csv
import json
import pymysql

def export_mysql_to_csv():

    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="***HIDDEN***",
        database="urban_outfitters",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

    cursor = conn.cursor()

    query = """
    SELECT *
    FROM data_062026
    """

    cursor.execute(query)

    columns = [desc[0] for desc in cursor.description]

    with open(
        "output.csv",
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=columns,
            quoting=csv.QUOTE_ALL
        )

        writer.writeheader()

        for row in cursor:

            clean_row = {}

            for key, value in row.items():

                if value is None:
                    value = "N/A"

                elif isinstance(value, bytes):
                    value = value.decode("utf-8", errors="ignore")

                # FIX FOR JSON/TEXT COLUMNS
                elif isinstance(value, str):

                    try:
                        parsed = json.loads(value)

                        # convert back without ascii escaping
                        value = json.dumps(
                            parsed,
                            ensure_ascii=False
                        )

                    except:
                        pass

                value = str(value).replace("\x00", "")

                clean_row[key] = value

            writer.writerow(clean_row)

    cursor.close()
    conn.close()

    print("CSV Exported Successfully")

export_mysql_to_csv()