import pandas as pd
import pymysql


# =========================
# DATABASE CONNECTION
# =========================

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="***HIDDEN***",
    database="walmart_category",
    charset="utf8mb4"
)

cursor = conn.cursor()


# =========================
# READ EXCEL
# =========================
df = pd.read_excel(r"D:\Julee\CODE\walmart\new\walmart_links_sheet.xlsx")
# =========================
# CLEAN DATA
# =========================

df = df.fillna("N/A")


def clean_count(value):

    try:
        value = str(value)

        # remove commas
        value = value.replace(",", "")

        # extract only number
        number = ''.join(ch for ch in value if ch.isdigit())

        return int(number) if number else 0

    except:
        return 0


def get_final_url(row):

    pl = row.get("pl", "N/A")
    sub_category = row.get("sub_category", "N/A")

    if pl != "N/A" and str(pl).strip():
        return pl

    if sub_category != "N/A" and str(sub_category).strip():
        return sub_category

    return None


def get_url_type(url):

    if not url:
        return "other"

    url = url.lower()

    if "/browse/" in url:
        return "browse"

    if "/cp/" in url:
        return "cp"

    if "/shop/" in url:
        return "shop"

    return "other"


# =========================
# INSERT QUERY
# =========================

query = """
INSERT IGNORE INTO walmart_category_master (
    main_cat,
    sub_cat,
    item_count,
    category_name,
    pl_url,
    sub_category_url,
    final_url,
    url_type,
    status
)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
"""



# =========================
# INSERT DATA
# =========================

for _, row in df.iterrows():
    main_cat = row.get("main_cat", "N/A")
    sub_cat = row.get("sub_cat", "N/A")
    item_count = clean_count(row.get("count", 0))
    category_name = row.get("name", "N/A")
    pl_url = row.get("pl", "N/A")
    sub_category_url = row.get("sub_category", "N/A")
    final_url = get_final_url(row)
    url_type = get_url_type(final_url)
    status = 'pending'
    values = (
        main_cat,
        sub_cat,
        item_count,
        category_name,

        pl_url,
        sub_category_url,

        final_url,
        url_type,
        status
    )

    try:

        cursor.execute(query, values)

        print("Inserted:", category_name)

    except Exception as e:

        print("ERROR:", e)
        print(values)


# =========================
# COMMIT
# =========================

conn.commit()

cursor.close()
conn.close()

print("ALL DATA INSERTED SUCCESSFULLY")