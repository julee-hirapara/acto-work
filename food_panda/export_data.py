import pandas as pd

from db_config_1 import get_db_connection


def export_mysql_table_to_excel(table_name, output_file):
    conn = get_db_connection("food_panda")

    try:
        cursor = conn.cursor()

        # NOTE: table_name should be validated to avoid SQL injection
        query = f"SELECT * FROM {table_name}"
        print(query)

        cursor.execute(query)

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Create DataFrame
        df = pd.DataFrame(rows, columns=columns)



        # Clean data
        df = df.fillna("N/A")

        # Write to Excel
        with pd.ExcelWriter(
            output_file,
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_urls": False}}
        ) as writer:
            df.to_excel(writer, index=False)

        print(f"Excel file created: {output_file}")

    finally:
        conn.close()
export_mysql_table_to_excel(
    table_name="data_052026",
    output_file="food_panda.xlsx"
)