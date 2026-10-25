import gzip

import orjson
from parsel import Selector
import json
import re
import os
import pymysql
import db_config_1 as db
from concurrent.futures import ThreadPoolExecutor, as_completed


def detect_units(chart_values):
    units = set()

    def scan(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                scan(v)
        elif isinstance(obj, list):
            for v in obj:
                scan(v)
        elif isinstance(obj, str):
            v = obj.lower()
            if "cm" in v:
                units.add("cm")
            if "in" in v or "inch" in v or "inches" in v:
                units.add("in")

    scan(chart_values)
    return list(units)

def singular_pipesign(table):
    item = {}
    for raw in table.xpath("//tr"):
        key = raw.xpath(".//th//text()").get()
        if key:
            key = key.strip()
            item[key] = []
        for va in raw.xpath(".//td"):
            value = va.xpath(".//text()").get()
            if value:
                item[key].append(value.strip())
        # item[key] = " , ".join(item.get(key)).strip(" , ") if item.get(key) else "N/A"
    return item


def without_class_head_list_structure(table):
    item = {}
    for ta in table.xpath("//tr"):
        key = ta.xpath(".//*[@scope='col']//text()").get()
        if key:
            item[key] = []
        for ta_2 in ta.xpath(".//td"):
            value = ta_2.xpath(".//text").get()
            if value:
                item[key].append(value.strip())
    if not item:
        headers = table.xpath("//thead//th//text()").getall()
        all_raw = []
        for raw in table.xpath("//tbody//tr"):
            values = raw.xpath(".//td//text()").getall()
            if values:
                all_raw.append(values)
        merged_data = [dict(zip(headers, row)) for row in all_raw]
        headers = merged_data[0].keys()
        item = {
            header: re.sub(r'\s+', " ", " | ".join(row[header] for row in merged_data if header in row)).strip()
            for header in headers
        }
    else:
        counter = 0
        if item:
            for v in item.values():
                if not v:
                    counter += 1
        if counter:
            return singular_pipesign(table)
        else:
            pass
    return item

def check_and_scrape_td_col_structure(table):
    data_col = table.xpath("//tbody//tr//td[@scope='col']")
    data_cm = table.xpath("//tbody//tr//td[contains(text(), '(cm)') or contains(text(), '(in)')]")
    if not data_col and not data_cm:
        return None
    headers = []
    for th in table.xpath("//thead//th"):
        text = th.xpath("string(.)").get("").strip()
        colspan = int(th.xpath("./@colspan").get("1"))
        for _ in range(colspan):
            headers.append(text)
    base_label = headers[0] if headers else "Alpha"
    all_list = []
    for tr in table.xpath("//tr"):
        values = []
        for val in tr.xpath(".//td"):
            text = val.xpath("string(.)").get("").strip()
            colspan = int(val.xpath("./@colspan").get("1"))
            values.extend([text] * colspan)
        if values:
            all_list.append(values)
    item = {}
    for lt in all_list:
        key = lt[0]
        value = dict(zip(headers[1:], lt[1:]))
        item[key] = value
    item["_base_label"] = base_label
    return item

def parse_head_list_structure(table):
    th_class = table.xpath("//thead//th[@class]").getall()
    td_class = table.xpath("//thead//td[@class]").getall()
    if not th_class or td_class:
        return without_class_head_list_structure(table)
    item = {}
    for raw in table.xpath("//tr"):
        item[raw.xpath(".//th//text()").get("unknow")] = []
        for tr in raw.xpath(".//td"):
            item[raw.xpath(".//th//text()").get("unknow")].append(tr.xpath(".//text()").get("N/A"))
        item[raw.xpath(".//th//text()").get("unknow")] = " , ".join(
            item[raw.xpath(".//th//text()").get("unknow")]).strip(" , ")
    return item

def key_value_structure(table):
    th_class = table.xpath("//thead//th[@class]").getall()
    td_class = table.xpath("//thead//td[@class]").getall()
    if not th_class and not td_class:
        return without_class_head_list_structure(table)
    all_list = []
    item = {}
    headers = table.xpath("//thead//th//text()").getall()
    if headers:
        item = {k: [] for k in headers}
    for tr in table.xpath("//tr"):
        values = tr.xpath(".//td//text()").getall()
        if values:
            all_list.append(values)
    if all_list:
        for i in all_list:
            t = list(zip(headers, i))
            for another_loop in t:
                item[another_loop[0]].append(another_loop[-1])
        item = {k.strip(): " , ".join(v).strip(" , ") for k, v in item.items()}
    return item

def extract_table(table):
    table_data = check_and_scrape_td_col_structure(table)
    if table_data:
        return table_data
    html_ele = {}
    for header in table.xpath("//thead//tr//*"):
        key = str(header)
        if key.startswith("<th"):
            html_ele['th'] = html_ele.get("th", 0)
            html_ele['th'] += 1
        elif key.startswith("<td"):
            html_ele['td'] = html_ele.get("td", 0)
            html_ele['td'] += 1
        elif key.startswith("<tr"):
            html_ele['tr'] = html_ele.get("tr", 0)
            html_ele['tr'] += 1
    if "th" in list(html_ele.keys()) and "td" in list(html_ele.keys()):
        table_data = parse_head_list_structure(table)
    else:
        table_data = key_value_structure(table)
    return table_data

# def normalize(data):
#     tabs = data.get("tabs", [])
#     # If all tab names are blank -> flatten to size_charts
#     if tabs and all(t.get("tab_name", "").strip() == "" for t in tabs):
#         size_charts = []
#         for t in tabs:
#             for chart in t.get("size_charts", []):
#                 # Add heading only if chart_name is blank
#                 if not chart.get("chart_name", "").strip():
#                     chart["chart_name"] = data.get("heading", "")
#                 size_charts.append(chart)
#         return {
#             "heading": data.get("heading", ""),
#             "size_charts": size_charts
#         }
#     # Handle tabs with blank tab_name
#     for t in tabs:
#         if not t.get("tab_name", "").strip():
#             for chart in t.get("size_charts", []):
#                 # Add heading only if chart_name is blank
#                 if not chart.get("chart_name", "").strip():
#                     chart["chart_name"] = data.get("heading", "")
#     return data

# def normalize(data):
#     print(data)
#     tabs = data.get("tabs", [])
#     # check if ALL tabs are empty OR first tab_name is blank
#     if tabs and all(t.get("tab_name", "").strip() == "" for t in tabs):
#         size_charts = []
#         for t in tabs:
#             for chart in t.get("size_charts", []):
#                 chart["chart_name"] = ""  # ✅ FIX HERE
#                 size_charts.append(chart)
#         return {
#             "heading": data.get("heading", ""),
#             "size_charts": size_charts
#         }
#     # optional: ALSO handle partial blank tab_name cases
#     for t in tabs:
#         if not t.get("tab_name", "").strip():
#             for chart in t.get("size_charts", []):
#                 # chart["chart_name"] = f'{data.get("heading", "")} - {unit}'
#                 chart["chart_name"] = ""
#     return data


def detect_chart_unit(columns):
    """
    Detect chart unit from measurement column labels.
    Returns: 'in', 'cm', or ''
    """
    units = set()

    for col in columns:
        label = (col.get("label") or "").lower()
        key = (col.get("key") or "").lower()

        if "(cm)" in label or key.endswith("_cm"):
            units.add("cm")

        if "(in)" in label or key.endswith("_in"):
            units.add("in")

    return units.pop() if len(units) == 1 else ""

def normalize(data):
    tabs = data.get("tabs", [])
    # -----------------------------
    # Case 1: All tab names blank
    # -----------------------------
    if tabs and all(t.get("tab_name", "").strip() == "" for t in tabs):
        size_charts = []

        for t in tabs:
            for chart in t.get("size_charts", []):
                if not chart.get("chart_name", "").strip():
                    chart["chart_name"] = data.get("heading", "")
                size_charts.append(chart)

        return {
            "heading": data.get("heading", ""),
            "size_charts": size_charts
        }

    # -----------------------------
    # Case 2: Blank tab names
    # -----------------------------
    for t in tabs:
        if not t.get("tab_name", "").strip():
            for chart in t.get("size_charts", []):
                if not chart.get("chart_name", "").strip():
                    chart["chart_name"] = data.get("heading", "")

    # # -----------------------------
    # # Case 3: Multiple tab names
    # # -----------------------------
    # tab_names = {
    #     t.get("tab_name", "").strip()
    #     for t in tabs
    #     if t.get("tab_name", "").strip()
    # }
    #
    # if len(tab_names) > 1:
    #     for t in tabs:
    #         for chart in t.get("size_charts", []):
    #             unit = chart.get("default_unit", "in")
    #
    #             if unit and not chart["chart_name"].endswith(f"- {unit}"):
    #                 chart["chart_name"] = f"{chart['chart_name']} - {unit}"

    return data


def normalize_key(text):
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
    return text.strip("_")

def get_unit_from_label(label):
    label = (label or "").lower()
    if "(in)" in label or " inch" in label or " inches" in label or "(inch)" in label or "inch" in label:
        return "in"
    if "(cm)" in label or " centimeter" in label or " centimeters" in label or "(cm)" in label or "cm" in label:
        return "cm"
    return ""

def convert_to_schema(chart_name, chart_name_title, chart_data, unit, units):
    if not chart_data:
        return None

    base_label = chart_data.pop("_base_label", "Size") or "Alpha"
    base_key = normalize_key(base_label) or "alpha"

    keys = list(chart_data.keys())
    if not keys:
        return None

    # ==================================================
    # FORMAT 3
    # ==================================================
    if all(isinstance(v, dict) for v in chart_data.values()):

        all_sizes = []
        for values in chart_data.values():
            all_sizes.extend(values.keys())

        all_sizes = list(dict.fromkeys(all_sizes))

        column_type = "measurement"
        if any(x in base_label.lower() for x in ["alpha", "numeric", "size"]):
            column_type = "size_label"

        if column_type == "size_label":
            columns = [{
                "key": base_key,
                "label": base_label,
                "type": column_type
            }]
        else:
            columns = [{
                "key": base_key,
                "label": base_label,
                "type": column_type,
                "unit": get_unit_from_label(base_label)
            }]

        for key in keys:

            column_type = "measurement"
            if any(x in key.lower() for x in ["alpha", "numeric", "size"]):
                column_type = "size_label"

            if column_type == "size_label":
                columns.append({
                    "key": normalize_key(key),
                    "label": key,
                    "type": column_type
                })
            else:
                columns.append({
                    "key": normalize_key(key),
                    "label": key,
                    "type": column_type,
                    "unit": get_unit_from_label(key)
                })

        rows = []

        for size in all_sizes:
            row = {base_key: size}

            for key in keys:
                row[normalize_key(key)] = chart_data[key].get(size)

            rows.append(row)

        return {
            "chart_name": chart_name,
            "chart_type": "",
            "garment_type": "",
            "age_group": "",
            "fit_category": "",
            "gender": "",
            "default_unit": "" if units == [] else unit ,
            "available_units": units if units else [],
            "columns": columns,
            "rows": rows
        }

    # ==================================================
    # FORMAT 2
    # ==================================================

    normalized = {}
    for key, value in chart_data.items():
        if isinstance(value, str):
            if "|" in value:
                normalized[key] = [x.strip() for x in value.split("|") if x.strip()]
            elif "," in value:
                normalized[key] = [x.strip() for x in value.split(",") if x.strip()]
            else:
                normalized[key] = [value]
        else:
            normalized[key] = value
    chart_data = normalized
    # ==================================================
    # FORMAT 1
    # ==================================================
    cleaned_chart_data = {}
    for key, value in chart_data.items():
        cleaned_chart_data[key.strip() if key else "Alpha"] = value
    chart_data = cleaned_chart_data
    columns = []
    for key in chart_data.keys():
        actual_label = key.strip() if key else "Alpha"
        actual_key = normalize_key(actual_label) or "alpha"
        column_type = "measurement"

        if any(x in actual_label.lower() for x in ["alpha", "numeric", "size"]):
            column_type = "size_label"

        if column_type == "size_label":
            columns.append({
                "key": actual_key,
                "label": actual_label,
                "type": column_type
            })
        else:
            columns.append({
                "key": actual_key,
                "label": actual_label,
                "type": column_type,
                "unit": get_unit_from_label(actual_label)
            })

    row_count = max(len(v) for v in chart_data.values())

    rows = []

    for i in range(row_count):

        row = {}

        for key in chart_data.keys():

            values = chart_data[key]

            row[normalize_key(key) or "alpha"] = (
                values[i] if i < len(values) else ""
            )

        rows.append(row)

    return {
        "chart_name": chart_name,
        "chart_type": "",
        "garment_type": "",
        "age_group": "",
        "fit_category": "",
        "gender": "",
        "default_unit": "" if units == [] else unit,
        "available_units": units if units else [],
        "columns": columns,
        "rows": rows
    }

import re

def extract_available_units(columns):
    units = []
    for col in columns:
        unit = col.get("unit", "").lower().strip()
        key = col.get("key", "").lower().strip()
        label = col.get("label", "").lower().strip()
        # First priority: explicit unit field
        if unit == "in":
            if "in" not in units:
                units.append("in")
        elif unit == "cm":
            if "cm" not in units:
                units.append("cm")
        # Second priority: key/label
        if key in ("in", "inch", "inches") or label in ("in", "inch", "inches"):
            if "in" not in units:
                units.append("in")
        if key in ("cm", "centimeter", "centimeters") or label in ("cm", "centimeter", "centimeters"):
            if "cm" not in units:
                units.append("cm")
        # Third priority: labels like Bust (in), Waist (cm)
        text = f"{key} {label}"
        if re.search(r"\(in\)|\bin\b|\binch(?:es)?\b", text):
            if "in" not in units:
                units.append("in")
        if re.search(r"\(cm\)|\bcm\b|\bcentimeter(?:s)?\b", text):
            if "cm" not in units:
                units.append("cm")
    return units

def update_available_units(result):
    def update_chart(chart):
        available_units = extract_available_units(chart.get("columns", []))
        default_unit = chart.get("default_unit", "").strip().lower()
        if default_unit:
            if default_unit not in available_units:
                if available_units:
                    # Replace the existing incorrect unit
                    available_units[0] = default_unit
                else:
                    # No units found
                    available_units = [default_unit]
        chart["available_units"] = available_units
    # Structure with tabs
    if result.get("tabs"):
        for tab in result["tabs"]:
            for chart in tab.get("size_charts", []):
                update_chart(chart)

    # Structure without tabs
    elif result.get("size_charts"):
        for chart in result["size_charts"]:
            update_chart(chart)

    return result



def main(record):
    file_name = fr"{db.SIZE_PAGESAVE}\{record['pid']}.json.gz"
    if not os.path.exists(file_name):
        return None
    if os.path.exists(file_name):
        with gzip.open(file_name, "rt", encoding="utf-8") as f:
            data = json.load(f)
    #
    # if not os.path.exists(file_name):
    #     return None
    # with open(file_name, "r", encoding="utf-8") as f:
    #     data = json.loads(f.read())
    extracted_data = {}
    try:
        for raw in data["items"]:
            chart_name_title = raw.get("displayTitle", "")
            if "guides" in raw:
                for guide in raw["guides"]:
                    display_name = guide.get("displayName", "size_guide")
                    extracted_data[display_name] = {
                        "inches": None,
                        "centimeters": None,
                        "sizeConversions": guide.get("sizeConversions", [])
                    }
                    if "inchesTables" in guide:
                        for tbl in guide["inchesTables"]:
                            extracted_data[display_name]["inches"] = extract_table(Selector(tbl["tableHtml"]))
                    if "centimetersTables" in guide:
                        for tbl in guide["centimetersTables"]:
                            extracted_data[display_name]["centimeters"] = extract_table(Selector(tbl["tableHtml"]))
            else:
                display_name = ""
                for tbl in raw.get("tables", []):
                    extracted_data[display_name] = extract_table(Selector(tbl["tableHtml"]))
    except Exception as e:
        print(e)
    tabs = []
    for chart_name, chart_values in extracted_data.items():
        # -----------------------------
        # Old format (no guides)
        # -----------------------------
        if not isinstance(chart_values, dict) or (
                "inches" not in chart_values
                and "centimeters" not in chart_values
        ):
            units = detect_units(chart_values)
            # unit = extract_available_units(chart_values)
            schema = convert_to_schema(
                chart_name_title,
                chart_name,
                chart_values,
                # "in",
                # units[0],
                units[0] if units else "",
                units
            )
            if schema:
                tabs.append({
                    "tab_name": chart_name,
                    "size_charts": [schema]
                })
            continue
        # -----------------------------
        # Guide format
        # -----------------------------
        units = []
        if chart_values.get("inches"):
            units.append("in")
        if chart_values.get("centimeters"):
            units.append("cm")
        units.extend(detect_units(chart_values))
        units = list(dict.fromkeys(units))
        inch_schema = None
        cm_schema = None
        if chart_values.get("inches"):
            inch_schema = convert_to_schema(
                chart_name,
                chart_name_title,
                chart_values["inches"],
                "in",
                units
            )
        if chart_values.get("centimeters"):
            cm_schema = convert_to_schema(
                chart_name,
                chart_name_title,
                chart_values["centimeters"],
                "cm",
                units
            )
        conversions = chart_values.get("sizeConversions", [])
        # -----------------------------
        # Country-wise tabs
        # -----------------------------
        if conversions:
            single_country = len(conversions) == 1

            for conversion in conversions:
                country = conversion.get("country", "").strip()
                default = conversion.get("defaultUnitOfMeasurement", "").lower()

                size_charts = []

                # If only one country exists, include both tables
                if single_country:
                    if inch_schema:
                        size_charts.append(inch_schema)
                    if cm_schema:
                        size_charts.append(cm_schema)

                # Multiple countries -> use default measurement
                else:
                    if default.startswith("inch"):
                        if inch_schema:
                            size_charts.append(inch_schema)

                    elif default.startswith("cent"):
                        if cm_schema:
                            size_charts.append(cm_schema)

                    else:
                        if inch_schema:
                            size_charts.append(inch_schema)
                        if cm_schema:
                            size_charts.append(cm_schema)

                tabs.append({
                    "tab_name": f"{chart_name} - {country}",
                    "size_charts": size_charts
                })
        else:
            charts = []
            if inch_schema:
                charts.append(inch_schema)
            if cm_schema:
                charts.append(cm_schema)
            tabs.append({
                "tab_name": chart_name,
                "size_charts": charts
            })
    result = {
        "heading": chart_name_title,
        "tabs": tabs
    }
    result = normalize(result)
    result = update_available_units(result)
    tabs = result.get("tabs", [])
    # If there are multiple different tab names
    tab_names = {
        t.get("tab_name", "").strip()
        for t in tabs
        if t.get("tab_name", "").strip()
    }
    if len(tab_names) > 1:
        for tab in tabs:
            for chart in tab.get("size_charts", []):
                unit = detect_chart_unit(chart.get("columns", []))
                if (
                        unit
                        and chart.get("chart_name")
                        and not chart["chart_name"].endswith(f" - {unit}")
                ):
                    chart["chart_name"] += f" - {unit}"
                # -----------------------------
                # Update available_units
                # -----------------------------
                detected_units = extract_available_units(chart.get("columns", []))
                if detected_units:
                    chart["available_units"] = detected_units
    # -----------------------------
    # Database update (your existing code)
    # -----------------------------
    con = None
    cur = None
    try:
        con = pymysql.connect(
            user="root",
            host="***HIDDEN***",
            database="urban_outfitters",
            password="***HIDDEN***",
            autocommit=True,
        )
        cur = con.cursor(pymysql.cursors.DictCursor)
        # result.pop("heading", None)
        def remove_heading(obj):
            if isinstance(obj, dict):
                obj.pop("heading", None)
                for value in obj.values():
                    remove_heading(value)
            elif isinstance(obj, list):
                for item in obj:
                    remove_heading(item)

        # Before json.dumps()
        # remove_heading(result)
        # # Convert dict -> list of dict
        # if isinstance(result, dict):
        #     result = [result]
        # Before json.dumps()
        remove_heading(result)
        # Flatten the structure
        if isinstance(result, dict):
            # Case 1: {"tabs": [...]}
            if "tabs" in result and isinstance(result["tabs"], list):
                result = result["tabs"]
            # Case 2: {"size_charts": [...]}
            elif "size_charts" in result and isinstance(result["size_charts"], list):
                result = result["size_charts"]
            else:
                result = [result]
        elif isinstance(result, list):
            flattened = []
            for item in result:
                if isinstance(item, dict):
                    # [{"tabs": [...]}] -> [{...}, {...}]
                    if "tabs" in item and isinstance(item["tabs"], list):
                        flattened.extend(item["tabs"])
                    # [{"size_charts": [...]}] -> [{...}, {...}]
                    elif "size_charts" in item and isinstance(item["size_charts"], list):
                        flattened.extend(item["size_charts"])
                    else:
                        flattened.append(item)
                else:
                    flattened.append(item)
            result = flattened
        json_text = json.dumps(result)
        json_text = json_text.replace('"-"', '""')
        cur.execute(
            f"""
            UPDATE {db.data_table}
            SET size_chart=%s,
                status='done'
            WHERE pid=%s
            """,
            (json_text, record["pid"]),
        )
        con.commit()
    except Exception as e:
        print(f"PID {record['pid']} ERROR:", e)
    finally:
        if cur:
            cur.close()
        if con:
            con.close()
    print("Updated:", record["pid"])


def get_connection():
    return pymysql.connect(
        user='root',
        host='***HIDDEN***',
        database='urban_outfitters',
        password='***HIDDEN***',
        autocommit=True
    )


if __name__ == "__main__":
    # main()
    con = pymysql.connect(user='root', host='***HIDDEN***', database='urban_outfitters', password='***HIDDEN***', autocommit=True)
    cur = con.cursor(pymysql.cursors.DictCursor)
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='done' AND pid='UO-76010537-000'")
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='done' AND pid='UO-89297493-000'")
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='done' AND pid='UO-107178394-000'")
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='pending'")
    cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where pid='UO-96451505-000'")
    records = cur.fetchall()
    print(len(records))
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(main, record) for record in records]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("THREAD ERROR:", repr(e))
    # for record in records:
    #     main(record)