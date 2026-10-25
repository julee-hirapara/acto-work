from parsel import Selector
import json
import db_config_1 as db
import os
import pymysql.cursors

def get_table_htmls(response):
    table_htmls = []

    items = response.get("items", [])

    for item in items:

        # CASE 1 → guides
        for guide in item.get("guides", []):

            # inchesTables
            for table in guide.get("inchesTables", []):
                if table.get("tableHtml"):
                    table_htmls.append(table["tableHtml"])

            # centimetersTables
            for table in guide.get("centimetersTables", []):
                if table.get("tableHtml"):
                    table_htmls.append(table["tableHtml"])

        # CASE 2 → tables
        for table in item.get("tables", []):
            if table.get("tableHtml"):
                table_htmls.append(table["tableHtml"])

    return table_htmls

def detect_unit(table_data):
    if not table_data:
        return "unknown"

    sample = table_data[0]

    # check keys
    for key in sample.keys():
        if key.endswith("_cm"):
            return "centimeters"
        if key.endswith("_in"):
            return "inches"

    return "unknown"

def normalize_key(text):
    return (
        text.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("-", "_")
    )


def clean_value(value):
    if value is None:
        return ""

    value = value.strip()

    # remove units
    value = value.replace(" CM", "")
    value = value.replace(" IN", "")

    # numeric conversion
    try:
        if "." in value:
            return float(value)
        return int(value)
    except:
        return value


def extract_table_rows(selector):
    """
    Extract all rows preserving th/td order
    """
    table_rows = []

    trs = selector.xpath("//tr")

    for tr in trs:
        cols = tr.xpath("./th|./td")

        row = []

        for col in cols:
            text = col.xpath("string(.)").get()
            text = text.strip() if text else ""

            colspan = int(col.attrib.get("colspan", 1))

            # expand colspan
            row.extend([text] * colspan)

        if row:
            table_rows.append(row)

    return table_rows


def is_matrix_table(rows):
    """
    Detect transposed/matrix structure
    """

    if len(rows) < 2:
        return False

    first_row = rows[0]

    # Example:
    # ["US", "4", "4.5", "5"]
    #
    # many columns after first item
    # usually matrix tables have MANY columns
    if len(first_row) >= 5:
        return True

    return False


def parse_standard_table(rows):
    """
    Parse normal tables:
    header row -> data rows
    """

    headers = [normalize_key(h) for h in rows[0]]

    result = []

    for row in rows[1:]:

        # pad row safely
        if len(row) < len(headers):
            row.extend([""] * (len(headers) - len(row)))

        item = {}

        for i, value in enumerate(row):
            item[headers[i]] = clean_value(value)

        result.append(item)

    return result


def parse_matrix_table(rows):
    """
    Parse transposed matrix tables
    """

    headers = rows[0]

    result = []

    for col_index in range(1, len(headers)):

        item = {}

        # master key
        item[normalize_key(headers[0])] = clean_value(
            headers[col_index]
        )

        # remaining rows
        for row in rows[1:]:

            key = normalize_key(row[0])

            if col_index < len(row):
                item[key] = clean_value(row[col_index])
            else:
                item[key] = ""

        result.append(item)

    return result


def html_table_to_json(table_html):

    try:
        selector = Selector(text=table_html)

        rows = extract_table_rows(selector)

        if not rows:
            return []

        # auto detect structure
        if is_matrix_table(rows):
            return parse_matrix_table(rows)

        return parse_standard_table(rows)

    except Exception as e:
        print("❌ Table parse error:", e)
        return []


if __name__ == '__main__':
    size_chart_loc = r"Z:\julee\PAGESAVES\Urban_Outfitters\04_2026\size_chart"
    page_save_paths = os.listdir(size_chart_loc)
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(f"""
        SELECT hash_id
        FROM {db.data_table}
        WHERE hash_id='108895362059'
        """)
    records = cur.fetchall()
    for record in records:
        hash_id = record['hash_id']
        file_name = fr"{size_chart_loc}\{hash_id}_size_chart.json"
        if os.path.exists(file_name):
            with open(file_name, 'r', encoding='utf-8') as f:
                json_data = json.loads(f.read())
            all_tables = get_table_htmls(json_data)
            final_json = {}
            for table_html in all_tables:
                data = html_table_to_json(table_html)
                unit = detect_unit(data)
                if unit == "inches":
                    final_json["inches"] = data
                elif unit == "centimeters":
                    final_json["centimeters"] = data
                else:
                    final_json.setdefault("rows", []).append(data)
            cur.execute(f"UPDATE {db.data_table} SET size_chart=%s WHERE hash_id=%s", (json.dumps(final_json, ensure_ascii=False), hash_id))
            conn.commit()
            print("Updated: ", hash_id)
        else:
            print(f"{hash_id}: Does not exists")
