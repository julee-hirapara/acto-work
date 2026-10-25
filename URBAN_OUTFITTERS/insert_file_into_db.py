# # import pandas as pd
# # import pymysql
# # import db_config_1 as db
# #
# # # =========================
# # # MYSQL CONNECTION
# # # =========================
# # conn = db.get_db_connection(db.db_name)
# # cur = conn.cursor()
# #
# # TABLE_NAME = "data_052026_copy"
# #
# # # =========================
# # # READ EXCEL FILE
# # # =========================
# # excel_file = r"D:\Julee\CODE\URBAN_OUTFITTERS\Urban_outfitter_20260515.xlsx"
# #
# # df = pd.read_excel(excel_file)
# #
# # # =========================
# # # RENAME COLUMNS
# # # =========================
# # column_mapping = {
# #     "Website": "website",
# #     "PID": "pid",
# #     "Name": "name",
# #     "Short Description": "short_description",
# #     "Description": "description",
# #     "Category": "category",
# #     "Image URL": "image_url",
# #     "Price": "price",
# #     "Price Currency": "price_currency",
# #     "Sale Price": "sale_price",
# #     "Final Price": "final_price",
# #     "Discount": "discount",
# #     "IsOnSale": "is_on_sale",
# #     "IsInStock": "is_in_stock",
# #     "Keywords": "keywords",
# #     "Brand": "brand",
# #     "Manufacturer": "manufacturer",
# #     "MPN": "mpn",
# #     "UPC or EAN": "upc_ean",
# #     "SKU": "sku",
# #     "Colour": "colour",
# #     "Gender": "gender",
# #     "Size": "size",
# #     "Size Chart": "size_chart",
# #     "Varint_Price": "variant_price",
# #     "Alternate Image URLs": "alternate_image_urls",
# #     "Link URL": "link_url",
# #     "Num Ratings": "num_ratings",
# #     "Average Ratings": "avg_ratings",
# #     "Reviews": "review_text",
# #     "hash_id": "hash_id"
# # }
# #
# # df.rename(columns=column_mapping, inplace=True)
# #
# # # =========================
# # # KEEP ONLY REQUIRED COLUMNS
# # # =========================
# # valid_columns = [
# #     "website",
# #     "pid",
# #     "name",
# #     "short_description",
# #     "description",
# #     "category",
# #     "image_url",
# #     "price",
# #     "price_currency",
# #     "sale_price",
# #     "final_price",
# #     "discount",
# #     "is_on_sale",
# #     "is_in_stock",
# #     "keywords",
# #     "brand",
# #     "manufacturer",
# #     "mpn",
# #     "upc_ean",
# #     "sku",
# #     "colour",
# #     "gender",
# #     "size",
# #     "size_chart",
# #     "variant_price",
# #     "alternate_image_urls",
# #     "link_url",
# #     "num_ratings",
# #     "avg_ratings",
# #     "review_text",
# #     "hash_id"
# # ]
# #
# # df = df[[col for col in valid_columns if col in df.columns]]
# #
# # # =========================
# # # HANDLE NULL VALUES
# # # =========================
# # # df = df.replace({"N/A": None})
# # # df = df.where(pd.notnull(df), None)
# #
# # # =========================
# # # HANDLE NULL VALUES
# # # =========================
# # df = df.replace({"N/A": None})
# #
# # # convert all NaN to None
# # df = df.astype(object).where(pd.notnull(df), None)
# # # =========================
# # # REMOVE DUPLICATES
# # # =========================
# # # df.drop_duplicates(subset=["hash_id"], inplace=True)
# #
# # # =========================
# # # CONVERT DATAFRAME TO TUPLES
# # # =========================
# # data = [tuple(row) for row in df.to_numpy()]
# #
# # # =========================
# # # CREATE INSERT QUERY
# # # =========================
# # columns = ", ".join(df.columns)
# #
# # placeholders = ", ".join(["%s"] * len(df.columns))
# #
# # query = f"""
# # INSERT INTO {TABLE_NAME}
# # ({columns})
# # VALUES ({placeholders})
# # """
# #
# # # =========================
# # # INSERT DATA
# # # =========================
# # cur.executemany(query, data)
# #
# # conn.commit()
# #
# # print(f"{cur.rowcount} rows inserted successfully!")
# #
# # # =========================
# # # CLOSE CONNECTION
# # # =========================
# # cur.close()
# # conn.close()
#
#
# import pymysql
# import db_config_1 as db
#
# conn = db.get_db_connection(db.db_name)
# cur = conn.cursor()
#
# query = """
# UPDATE data_052026_copy t1
# JOIN data_052026 t2
#     ON t1.hash_id = t2.hash_id
# SET t1.size_type = t2.size_type
# WHERE t2.size_chart IS NOT NULL
# """
#
# cur.execute(query)
#
# conn.commit()
#
# print(f"{cur.rowcount} rows updated successfully!")
#
# cur.close()
# conn.close()
#


import hashlib
import json
import pymysql
import pandas as pd
import db_config_1 as db
from datetime import datetime
import re

# =====================================================
# CLEAN TEXT
# =====================================================
def clean_text(value):

    if value is None or value == "":
        return "N/A"

    if not isinstance(value, str):
        return value

    text = value

    # remove control chars
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)

    # remove invisible unicode chars
    text = re.sub(r"[\u200B-\u200F\u202A-\u202E\u2060-\u206F]", " ", text)

    # remove emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "]+",
        flags=re.UNICODE
    )

    text = emoji_pattern.sub(" ", text)

    # remove escaped chars
    # remove REAL line breaks/tabs
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")

    # remove escaped chars
    text = text.replace("\\n", " ")
    text = text.replace("\\r", " ")
    text = text.replace("\\t", " ")

    # remove backslashes
    text = text.replace("\\", "")

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    text = text.strip()

    return text if text else "N/A"


# =====================================================
# URL TO HASH ID
# =====================================================
def url_to_id(url):

    if not url:
        return "N/A"

    h = hashlib.sha256(url.encode()).hexdigest()
    num = int(h, 16)

    return str(num)[0:12]


# =====================================================
# GENERATE MPN HASH
# =====================================================
def generate_hash_key(pid, color):

    pid = pid if pid else ""
    color = color if color else ""

    raw = f"{pid}+{color}".encode()

    h = hashlib.sha256(raw).hexdigest()
    num = int(h, 16)

    return str(num)[0:12]


# =====================================================
# NORMALIZE REVIEW TEXT
# =====================================================
def normalize_review_text(review_text):

    try:

        if not review_text:
            return {"reviews": []}

        # string -> json
        if isinstance(review_text, str):
            data = json.loads(review_text)
        else:
            data = review_text

        # list
        if isinstance(data, list):
            reviews = data

        # dict
        elif isinstance(data, dict):

            if "reviews" in data:

                if isinstance(data["reviews"], list):
                    reviews = data["reviews"]
                else:
                    reviews = []

            else:
                reviews = [data]

        else:
            reviews = []

        # replace all nulls with N/A
        cleaned_reviews = []

        for review in reviews:

            cleaned_review = {}

            for k, v in review.items():

                if v is None or v == "":
                    cleaned_review[k] = "N/A"

                else:
                    cleaned_review[k] = clean_text(v)

            cleaned_reviews.append(cleaned_review)

        return {"reviews": cleaned_reviews}

    except Exception as e:

        print("Review normalize error:", e)

        return {"reviews": []}


# =====================================================
# CREATE CSV
# =====================================================
def create_csv_output():

    # =========================
    # DB CONNECTION
    # =========================
    con = db.get_db_connection(db.db_name)

    cur = con.cursor(pymysql.cursors.DictCursor)

    cur.execute(f"""
        SELECT *
        FROM `data_062026`
        ORDER BY id ASC
    """)

    rows = cur.fetchall()

    final_data = []

    # =====================================================
    # LOOP ROWS
    # =====================================================
    serial_no = 1
    for index, row in enumerate(rows, start=1):

        category = clean_text(row.get("category"))

        category_lower = str(category).lower()

        # skip home/lifestyle
        if category_lower.startswith(("home", "lifestyle")):
            continue

        # =========================
        # PRICE
        # =========================
        listprice = row.get("price") if row.get("price") else "N/A"

        saleprice = row.get("sale_price") if row.get("sale_price") else "N/A"

        # discount
        try:

            if listprice != "N/A" and saleprice != "N/A":

                discount = round(float(listprice) - float(saleprice), 2)

                if discount == 0:
                    discount = "N/A"

            else:
                discount = "N/A"

        except:
            discount = "N/A"

        # =========================
        # HASH
        # =========================
        hash_id = url_to_id(row.get("main_url"))

        mpn = generate_hash_key(
            row.get("pid"),
            row.get("colour")
        )

        # =========================
        # REVIEW TEXT
        # =========================
        review_text = row.get("review_text")

        normalized_reviews = normalize_review_text(review_text)

        if normalized_reviews.get("reviews"):

            review_output = json.dumps(
                normalized_reviews,
                separators=(',', ':'),
                ensure_ascii=False
            )

        else:
            review_output = "N/A"

        # =========================
        # SIZE CHART
        # =========================
        size_chart = row.get("size_chart")

        try:

            if size_chart:

                size_chart_output = json.dumps(
                    json.loads(size_chart),
                    separators=(',', ':'),
                    ensure_ascii=False
                )

            else:
                size_chart_output = "N/A"

        except:
            size_chart_output = "N/A"

        # =========================
        # ROW DATA
        # =========================
        instock = clean_text(row.get("is_in_stock"))
        # print(instock)
        # print(type(instock))
        if instock == "1":
            instock = "TRUE"
        elif instock == "0":
            instock = "FALSE"
        row_data = {
            "S.No.": serial_no,
            # "S.No.": index,
            "Website": clean_text(row.get("website")),
            "PID": clean_text(row.get("pid")),
            "Name": clean_text(row.get("name")),
            "Short Description": clean_text(row.get("short_description")),
            "Description": clean_text(row.get("description")),
            "Category": clean_text(row.get("category")),
            "Image URL": clean_text(row.get("image_url")),
            "Price": listprice,
            "Price Currency": clean_text(row.get("price_currency")),
            "Sale Price": saleprice,
            "Final Price": row.get("final_price") if row.get("final_price") else "N/A",
            "Discount": discount,
            "IsOnSale": clean_text(row.get("is_on_sale")),
            "IsInStock": instock,
            "Keywords": clean_text(row.get("keywords")),
            "Brand": clean_text(row.get("brand")),
            "Manufacturer": clean_text(row.get("manufacturer")),
            "MPN": str(mpn),
            "UPC or EAN": clean_text(row.get("upc_ean")),
            "SKU": clean_text(row.get("sku")),
            "Colour": clean_text(row.get("colour")),
            "Gender": clean_text(row.get("gender")),
            "Size": clean_text(row.get("size_type")),
            "Size Chart": size_chart_output,
            "Varint_Price": row.get("variant_price") if row.get("variant_price") else "N/A",
            "Alternate Image URLs": clean_text(row.get("alternate_image_urls")),
            "Link URL": clean_text(row.get("link_url")),
            "Num Ratings": row.get("num_ratings") if row.get("num_ratings") else "N/A",
            "Average Ratings": round(row.get("avg_ratings"), 1) if row.get("avg_ratings") else "N/A",
            "Reviews": review_output,
            "hash_id": str(row.get("hash_id"))
            # "main_url": clean_text(row.get("main_url"))
        }

        final_data.append(row_data)
        serial_no += 1
    # =====================================================
    # CREATE DATAFRAME
    # =====================================================
    # df = pd.DataFrame(final_data)
    # =====================================================
    # CREATE DATAFRAME
    # =====================================================

    columns = [
        "S.No.",
        "Website",
        "PID",
        "Name",
        "Short Description",
        "Description",
        "Category",
        "Image URL",
        "Price",
        "Price Currency",
        "Sale Price",
        "Final Price",
        "Discount",
        "IsOnSale",
        "IsInStock",
        "Keywords",
        "Brand",
        "Manufacturer",
        "MPN",
        "UPC or EAN",
        "SKU",
        "Colour",
        "Gender",
        "Size",
        "Size Chart",
        "Varint_Price",
        "Alternate Image URLs",
        "Link URL",
        "Num Ratings",
        "Average Ratings",
        "Reviews",
        "hash_id"
    ]

    df = pd.DataFrame(final_data, columns=columns)

    # =====================================================
    # CLEAN EXTRA COLUMNS
    # =====================================================

    df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
    df = df.loc[:, df.columns.notna()]

    # =====================================================
    # REPLACE NULLS
    # =====================================================
    df = df.fillna("N/A")
    # =====================================================
    # OUTPUT FILE
    # =====================================================
    current_date = datetime.now().strftime("%Y%m%d")

    output_file = f"{db.RESULT_PAGE}/Urban_outfitter_{current_date}.csv"

    # =====================================================
    # EXPORT CSV
    # =====================================================
    import csv
    df.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_ALL
        # quoting=1
    )

    # =====================================================
    # CLOSE DB
    # =====================================================
    cur.close()
    con.close()

    print(f"✅ CSV file created successfully: {output_file}")


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":

    create_csv_output()