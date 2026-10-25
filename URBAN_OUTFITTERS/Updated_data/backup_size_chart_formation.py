import orjson
from dns.asyncresolver import resolve
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

# def check_and_scrape_td_col_structure(table):
#     data_col = table.xpath("//tbody//tr//td[@scope='col']")
#     data_cm = table.xpath("//tbody//tr//td[contains(text(), '(cm)') or contains(text(), '(in)')]")
#     if not data_col and not data_cm:
#         return None
#     item = {}
#     all_list = []
#     # headers = table.xpath("//thead//th//text()").getall()
#     # headers = [x.strip() for x in table.xpath("//thead//th//text()").getall()]
#     headers = []
#     for th in table.xpath("//thead//th"):
#         text = th.xpath("string(.)").get("").strip()
#         colspan = int(th.xpath("./@colspan").get("1"))
#         for _ in range(colspan):
#             headers.append(text)
#     base_label = headers[0] if headers else "Size"
#     for tr in table.xpath("//tr"):
#         values = []
#         # for val in tr.xpath(".//td"):
#         #     values.append(val.xpath(".//text()").get("N/A").strip())
#         for val in tr.xpath(".//td"):
#             text = val.xpath("string(.)").get("").strip()
#             colspan = int(val.xpath("./@colspan").get("1"))
#             values.append(text)
#             for _ in range(colspan - 1):
#                 values.append(text)
#             # for _ in range(colspan):
#             #     values.append(text)
#         if values:
#             all_list.append(values)
#     item = {}
#     for lt in all_list:
#         key = lt[0]
#         value = dict(zip(headers[1:], lt[1:]))
#         item[key] = value
#     item["_base_label"] = base_label
#     return item


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


def normalize(data):
    tabs = data.get("tabs", [])
    # check if ALL tabs are empty OR first tab_name is blank
    if tabs and all(t.get("tab_name", "").strip() == "" for t in tabs):
        size_charts = []
        for t in tabs:
            for chart in t.get("size_charts", []):
                chart["chart_name"] = ""   # ✅ FIX HERE
                size_charts.append(chart)
        return {
            "heading": data.get("heading", ""),
            "size_charts": size_charts
        }
    # optional: ALSO handle partial blank tab_name cases
    for t in tabs:
        if not t.get("tab_name", "").strip():
            for chart in t.get("size_charts", []):
                chart["chart_name"] = ""
    return data

# def normalize(data):
#     tabs = data.get("tabs", [])
#     # check if ALL tabs are empty OR first tab_name is blank
#     if tabs and all(t.get("tab_name", "").strip() == "" for t in tabs):
#         size_charts = []
#         for t in tabs:
#             size_charts.extend(t.get("size_charts", []))
#         return {
#             "heading": data.get("heading", ""),
#             "size_charts": size_charts
#         }
#     # default case: keep structure
#     return data

def main(record):
    file_name = fr"{db.SIZE_PAGESAVE}\{record['pid']}.json"
    if not os.path.exists(file_name):
        return None
    with open(file_name, "r", encoding="utf-8") as f:
        data = json.loads(f.read())
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
            schema = convert_to_schema(
                chart_name_title,
                chart_name,
                chart_values,
                "in",
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
            for conversion in conversions:
                country = conversion.get("country", "").strip()
                default = conversion.get("defaultUnitOfMeasurement").lower()
                size_charts = []
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
        # -----------------------------
        # No country information
        # -----------------------------
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
    # -----------------------------
    # Database update (your existing code)
    # -----------------------------
    con = None
    cur = None
    try:
        con = pymysql.connect(
            user="root",
            host="localhost",
            database="urban_outfitters",
            password="***HIDDEN***",
            autocommit=True,
        )
        cur = con.cursor(pymysql.cursors.DictCursor)
        json_text = json.dumps(result)
        json_text = json_text.replace('"-"', '""')
        cur.execute(
            """
            UPDATE data_062026
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


# def main(record):
#     file_name = fr"{db.SIZE_PAGESAVE}\{record['pid']}.json"
#     if not os.path.exists(file_name):
#         return None
#     with open(file_name, 'r', encoding='utf-8') as f:
#         data = json.loads(f.read())
#     # data = record["size_chart_response"]
#     # if isinstance(data, str):
#     #     data = json.loads(data)
#     extracted_data = {}
#     try:
#         for raw in data['items']:
#             chart_name_title = raw.get("displayTitle")
#             for raw_2 in raw['guides']:
#                 display_name = raw_2.get("displayName", "size_guide")
#                 extracted_data[display_name] = {}
#                 if "inchesTables" in (raw_2.keys()):
#                     for raw_3 in raw_2['inchesTables']:
#                         table = raw_3['tableHtml']
#                         table = Selector(table)
#                         extracted_data[display_name]['inches'] = extract_table(table)
#                 if "centimetersTables" in (raw_2.keys()):
#                     for raw_3 in raw_2['centimetersTables']:
#                         table = raw_3['tableHtml']
#                         table = Selector(table)
#                         extracted_data[display_name]['centimeters'] = extract_table(table)
#
#     except Exception as e:
#         e = str(e)
#         if 'guides' in e:
#             counter = 1
#             for raw in data['items']:
#                 chart_name_title = raw.get("displayTitle")
#                 # display_name = raw.get("displayTitle")
#                 display_name = ""
#                 for raw_2 in raw['tables']:
#                     extracted_data[display_name] = extract_table(Selector(raw_2['tableHtml']))
#                     counter += 1
#         else:
#             print(e)
#     # if extracted_data:
#     #     # print(extracted_data)
#     final_output = []
#     tabs = []
#
#     for chart_name, chart_values in extracted_data.items():
#         units = []
#         if "inches" in chart_values:
#             units.append("in")
#         if "centimeters" in chart_values:
#             units.append("cm")
#         # if not units:
#         #     units = ["in"]
#         # 2. fallback deep detection (fix missing cases)
#         units.extend(detect_units(chart_values))
#         # 3. remove duplicates + preserve order
#         units = list(dict.fromkeys(units))
#         if not units:
#             units = []
#         size_charts = []
#         # guides structure
#         if isinstance(chart_values, dict) and (
#                 "inches" in chart_values or
#                 "centimeters" in chart_values
#         ):
#             if "inches" in chart_values:
#                 schema = convert_to_schema(
#                     chart_name,
#                     chart_name_title,
#                     chart_values["inches"],
#                     "in",
#                     units
#                 )
#                 if schema:
#                     size_charts.append(schema)
#             if "centimeters" in chart_values:
#                 schema = convert_to_schema(
#                     chart_name,
#                     chart_name_title,
#                     chart_values["centimeters"],
#                     "cm",
#                     units
#                 )
#                 if schema:
#                     size_charts.append(schema)
#         else:
#             schema = convert_to_schema(
#                 chart_name_title,
#                 chart_name,
#                 chart_values,
#                 "in",
#                 units
#             )
#             if schema:
#                 size_charts.append(schema)
#             guide = raw_2  # current guide
#
#             if guide.get("sizeConversions"):
#
#                 for conversion in guide["sizeConversions"]:
#
#                     country = conversion.get("country", "")
#                     default = conversion.get("defaultUnitOfMeasurement", "").lower()
#
#                     tab = {
#                         "tab_name": f"{chart_name} - {country}",
#                         "size_charts": []
#                     }
#
#                     for chart in size_charts:
#
#                         if default.startswith("inch") and chart["default_unit"] == "in":
#                             tab["size_charts"].append(chart)
#
#                         elif default.startswith("cent") and chart["default_unit"] == "cm":
#                             tab["size_charts"].append(chart)
#
#                     tabs.append(tab)
#
#             else:
#
#                 tabs.append({
#                     "tab_name": chart_name,
#                     "size_charts": size_charts
#                 })
#         tabs.append({
#             "tab_name": chart_name,
#             "size_charts": size_charts
#         })
#     result = {
#         "heading": chart_name_title,
#         "tabs": tabs
#     }
#     result = normalize(result)
#     # for chart_name, chart_values in extracted_data.items():
#     #     units = []
#     #     if "inches" in chart_values:
#     #         units.append("in")
#     #     if "centimeters" in chart_values:
#     #         units.append("cm")
#     #     if units == []:
#     #         units = ["in"]
#     #     # guides structure
#     #     if isinstance(chart_values, dict) and (
#     #             "inches" in chart_values or
#     #             "centimeters" in chart_values
#     #     ):
#     #         if "inches" in chart_values:
#     #             final_output.append(
#     #                 convert_to_schema(
#     #                     chart_name,
#     #                     chart_name_title,
#     #                     chart_values["inches"],
#     #                     "in",
#     #                     units
#     #                 )
#     #             )
#     #         if "centimeters" in chart_values:
#     #             final_output.append(
#     #                 convert_to_schema(
#     #                     chart_name,
#     #                     chart_name_title,
#     #                     chart_values["centimeters"],
#     #                     "cm",
#     #                     units
#     #                 )
#     #             )
#     #     # tables structure
#     #     else:
#     #         final_output.append(
#     #             convert_to_schema(
#     #                 chart_name_title,
#     #                 chart_name,
#     #                 chart_values,
#     #                 "in",
#     #                 units
#     #             )
#     #         )
#     # result = {
#     #     "heading": chart_name_title,
#     #     "tab":[{
#     #         "tab_name": chart_name,
#     #         "size_charts":final_output
#     #     }]
#     # }
#
#     # con = get_connection()
#     # cur = con.cursor()
#     # try:
#     #     cur.execute(
#     #         "update data_062026 set size_chart=%s, status='done' where pid=%s",
#     #         (json.dumps(final_output, ensure_ascii=False), record['pid'])
#     #     )
#     # finally:
#     #     cur.close()
#     #     con.close()
#     # print(json.dumps(final_output, indent=2, ensure_ascii=False))
#     con = None
#     cur = None
#
#     try:
#         # #  pip install DBUtils
#         # from dbutils.pooled_db import PooledDB
#         #
#         # pool = PooledDB(
#         #     creator=pymysql,
#         #     maxconnections=20,
#         #     host='localhost',
#         #     user='root',
#         #     password='***HIDDEN***',
#         #     database='urban_outfitters'
#         # )
#         # con = pool.connection()
#         # cur = con.cursor()
#         con = pymysql.connect(user='root', host='localhost', database='urban_outfitters', password='***HIDDEN***',
#                               autocommit=True)
#         cur = con.cursor(pymysql.cursors.DictCursor)
#         json_text = json.dumps(result)
#         # preserve dashes
#         json_text = json_text.replace('"-"', '""')
#         updates = []
#         updates.append(
#             (json_text, record['pid'])
#         )
#         # updates.append(
#         #     (json.dumps(json_text, ensure_ascii=False),record['pid'])
#         # )
#         cur.executemany(
#             """
#             UPDATE data_062026
#             SET size_chart=%s,
#                 status='done'
#             WHERE pid=%s
#             """,
#             updates
#         )
#         con.commit()
#     except Exception as e:
#         print(f"PID {record['pid']} ERROR:", e)
#
#     finally:
#         if cur:
#             cur.close()
#         if con:
#             con.close()
#     # cur.execute("update data_062026 set size_chart=%s, status='done' where pid=%s",
#     #             (json.dumps(final_output, ensure_ascii=False), record['pid']))
#     # con.commit()
#     print("Updated: ", record['pid'])


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

def convert_to_schema(chart_name,chart_name_title, chart_data, unit, units):
    if not chart_data:
        return None
    # base_label = chart_data.pop("_base_label", "Size")
    base_label = chart_data.pop("_base_label", "Size") or "Alpha"
    base_key = normalize_key(base_label) or "alpha"
    keys = list(chart_data.keys())
    if not keys:
        return None
    # ==================================================
    # FORMAT 3
    # {
    #   "Waist": {"XS":"24","S":"26"},
    #   "Hip": {"XS":"34","S":"36"}
    # }
    # ==================================================
    if all(isinstance(v, dict) for v in chart_data.values()):
        all_sizes = []
        for values in chart_data.values():
            all_sizes.extend(values.keys())
        all_sizes = list(dict.fromkeys(all_sizes))
        base_key = normalize_key(base_label)
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
            # "default_unit": "in",
            "default_unit": units[0] if units else "",
            # "available_units": units,
            "available_units": units if units else [],
            "columns": columns,
            "rows": rows
        }
    # ==================================================
    # FORMAT 2
    # pipe/comma separated strings
    # ==================================================
    normalized = {}
    for key, value in chart_data.items():
        if isinstance(value, str):
            if "|" in value:
                normalized[key] = [
                    x.strip()
                    for x in value.split("|")
                    if x.strip()
                ]
            elif "," in value:
                normalized[key] = [
                    x.strip()
                    for x in value.split(",")
                    if x.strip()
                ]
            else:
                normalized[key] = [value]
        else:
            normalized[key] = value
    chart_data = normalized
    # ==================================================
    # FORMAT 1
    # list structure
    # ==================================================
    # if not all(isinstance(v, list) for v in chart_data.values()):
    #     return None
    cleaned_chart_data = {}
    for key, value in chart_data.items():
        new_key = key.strip() if key else "Alpha"
        cleaned_chart_data[new_key] = value
    chart_data = cleaned_chart_data
    columns = []
    first_col = True
    # for key in chart_data.keys():
    #     column_type = "measurement"
    #     if any(x in key.lower() for x in ["alpha", "numeric", "size"]):
    #         column_type = "size_label"
    #     columns.append({
    #         "key": normalize_key(key),
    #         "label": key,
    #         "type": column_type,
    #         "unit": ""
    #     })
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
        # columns.append({
        #     "key": actual_key,
        #     "label": actual_label,
        #     "type": column_type,
        #     "unit": get_unit_from_label(actual_label)
        # })
        first_col = False
    row_count = max(len(v) for v in chart_data.values())
    rows = []
    for i in range(row_count):
        row = {}
        for key in chart_data.keys():
            values = chart_data[key]
            row_key = normalize_key(key) or "alpha"
            row[row_key] = (
                values[i]
                if i < len(values)
                else ""
            )
            # row[normalize_key(key)] = (
            #     values[i]
            #     if i < len(values)
            #     else None
            # )
        rows.append(row)
    return {
        "chart_name": chart_name,
        "chart_type": "",
        "garment_type": "",
        "age_group": "",
        "fit_category": "",
        "gender": "",
        # "default_unit": "in",
        "default_unit": units[0] if units else "",
        # "available_units": units,
        "available_units": units if units else [],
        "columns": columns,
        "rows": rows
    }


def get_connection():
    return pymysql.connect(
        user='root',
        host='localhost',
        database='urban_outfitters',
        password='***HIDDEN***',
        autocommit=True
    )


if __name__ == "__main__":
    # main()
    con = pymysql.connect(user='root', host='localhost', database='urban_outfitters', password='***HIDDEN***', autocommit=True)
    cur = con.cursor(pymysql.cursors.DictCursor)
    cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='done' AND pid='UO-76010537-000'")
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='done'")
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

###########################  20-07-2026  ###############################################################

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
            # "heading": data.get("heading", ""),
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

# def update_available_units(result):
#     # Structure with tabs
#     if result.get("tabs"):
#         for tab in result["tabs"]:
#             for chart in tab.get("size_charts", []):
#                 chart["available_units"] = extract_available_units(
#                     chart.get("columns", [])
#                 )
#
#     # Structure without tabs
#     elif result.get("size_charts"):
#         for chart in result["size_charts"]:
#             chart["available_units"] = extract_available_units(
#                 chart.get("columns", [])
#             )
#     return result


def main(record):
    file_name = fr"{db.SIZE_PAGESAVE}\{record['pid']}.json"
    if not os.path.exists(file_name):
        return None
    with open(file_name, "r", encoding="utf-8") as f:
        data = json.loads(f.read())
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
                units[0],
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
        # if conversions:
        #     for conversion in conversions:
        #         country = conversion.get("country", "").strip()
        #         default = conversion.get("defaultUnitOfMeasurement").lower()
        #         size_charts = []
        #         if default.startswith("inch"):
        #             if inch_schema:
        #                 size_charts.append(inch_schema)
        #         elif default.startswith("cent"):
        #             if cm_schema:
        #                 size_charts.append(cm_schema)
        #         else:
        #             if inch_schema:
        #                 size_charts.append(inch_schema)
        #             if cm_schema:
        #                 size_charts.append(cm_schema)
        #         tabs.append({
        #             "tab_name": f"{chart_name} - {country}",
        #             "size_charts": size_charts
        #         })
        # -----------------------------
        # No country information
        # -----------------------------
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
        # "heading": chart_name_title,
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
            host="localhost",
            database="urban_outfitters",
            password="***HIDDEN***",
            autocommit=True,
        )
        cur = con.cursor(pymysql.cursors.DictCursor)
        json_text = json.dumps(result)
        json_text = json_text.replace('"-"', '""')
        cur.execute(
            """
            UPDATE data_062026
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


# def main(record):
#     file_name = fr"{db.SIZE_PAGESAVE}\{record['pid']}.json"
#     if not os.path.exists(file_name):
#         return None
#     with open(file_name, 'r', encoding='utf-8') as f:
#         data = json.loads(f.read())
#     # data = record["size_chart_response"]
#     # if isinstance(data, str):
#     #     data = json.loads(data)
#     extracted_data = {}
#     try:
#         for raw in data['items']:
#             chart_name_title = raw.get("displayTitle")
#             for raw_2 in raw['guides']:
#                 display_name = raw_2.get("displayName", "size_guide")
#                 extracted_data[display_name] = {}
#                 if "inchesTables" in (raw_2.keys()):
#                     for raw_3 in raw_2['inchesTables']:
#                         table = raw_3['tableHtml']
#                         table = Selector(table)
#                         extracted_data[display_name]['inches'] = extract_table(table)
#                 if "centimetersTables" in (raw_2.keys()):
#                     for raw_3 in raw_2['centimetersTables']:
#                         table = raw_3['tableHtml']
#                         table = Selector(table)
#                         extracted_data[display_name]['centimeters'] = extract_table(table)
#
#     except Exception as e:
#         e = str(e)
#         if 'guides' in e:
#             counter = 1
#             for raw in data['items']:
#                 chart_name_title = raw.get("displayTitle")
#                 # display_name = raw.get("displayTitle")
#                 display_name = ""
#                 for raw_2 in raw['tables']:
#                     extracted_data[display_name] = extract_table(Selector(raw_2['tableHtml']))
#                     counter += 1
#         else:
#             print(e)
#     # if extracted_data:
#     #     # print(extracted_data)
#     final_output = []
#     tabs = []
#
#     for chart_name, chart_values in extracted_data.items():
#         units = []
#         if "inches" in chart_values:
#             units.append("in")
#         if "centimeters" in chart_values:
#             units.append("cm")
#         # if not units:
#         #     units = ["in"]
#         # 2. fallback deep detection (fix missing cases)
#         units.extend(detect_units(chart_values))
#         # 3. remove duplicates + preserve order
#         units = list(dict.fromkeys(units))
#         if not units:
#             units = []
#         size_charts = []
#         # guides structure
#         if isinstance(chart_values, dict) and (
#                 "inches" in chart_values or
#                 "centimeters" in chart_values
#         ):
#             if "inches" in chart_values:
#                 schema = convert_to_schema(
#                     chart_name,
#                     chart_name_title,
#                     chart_values["inches"],
#                     "in",
#                     units
#                 )
#                 if schema:
#                     size_charts.append(schema)
#             if "centimeters" in chart_values:
#                 schema = convert_to_schema(
#                     chart_name,
#                     chart_name_title,
#                     chart_values["centimeters"],
#                     "cm",
#                     units
#                 )
#                 if schema:
#                     size_charts.append(schema)
#         else:
#             schema = convert_to_schema(
#                 chart_name_title,
#                 chart_name,
#                 chart_values,
#                 "in",
#                 units
#             )
#             if schema:
#                 size_charts.append(schema)
#             guide = raw_2  # current guide
#
#             if guide.get("sizeConversions"):
#
#                 for conversion in guide["sizeConversions"]:
#
#                     country = conversion.get("country", "")
#                     default = conversion.get("defaultUnitOfMeasurement", "").lower()
#
#                     tab = {
#                         "tab_name": f"{chart_name} - {country}",
#                         "size_charts": []
#                     }
#
#                     for chart in size_charts:
#
#                         if default.startswith("inch") and chart["default_unit"] == "in":
#                             tab["size_charts"].append(chart)
#
#                         elif default.startswith("cent") and chart["default_unit"] == "cm":
#                             tab["size_charts"].append(chart)
#
#                     tabs.append(tab)
#
#             else:
#
#                 tabs.append({
#                     "tab_name": chart_name,
#                     "size_charts": size_charts
#                 })
#         tabs.append({
#             "tab_name": chart_name,
#             "size_charts": size_charts
#         })
#     result = {
#         "heading": chart_name_title,
#         "tabs": tabs
#     }
#     result = normalize(result)
#     # for chart_name, chart_values in extracted_data.items():
#     #     units = []
#     #     if "inches" in chart_values:
#     #         units.append("in")
#     #     if "centimeters" in chart_values:
#     #         units.append("cm")
#     #     if units == []:
#     #         units = ["in"]
#     #     # guides structure
#     #     if isinstance(chart_values, dict) and (
#     #             "inches" in chart_values or
#     #             "centimeters" in chart_values
#     #     ):
#     #         if "inches" in chart_values:
#     #             final_output.append(
#     #                 convert_to_schema(
#     #                     chart_name,
#     #                     chart_name_title,
#     #                     chart_values["inches"],
#     #                     "in",
#     #                     units
#     #                 )
#     #             )
#     #         if "centimeters" in chart_values:
#     #             final_output.append(
#     #                 convert_to_schema(
#     #                     chart_name,
#     #                     chart_name_title,
#     #                     chart_values["centimeters"],
#     #                     "cm",
#     #                     units
#     #                 )
#     #             )
#     #     # tables structure
#     #     else:
#     #         final_output.append(
#     #             convert_to_schema(
#     #                 chart_name_title,
#     #                 chart_name,
#     #                 chart_values,
#     #                 "in",
#     #                 units
#     #             )
#     #         )
#     # result = {
#     #     "heading": chart_name_title,
#     #     "tab":[{
#     #         "tab_name": chart_name,
#     #         "size_charts":final_output
#     #     }]
#     # }
#
#     # con = get_connection()
#     # cur = con.cursor()
#     # try:
#     #     cur.execute(
#     #         "update data_062026 set size_chart=%s, status='done' where pid=%s",
#     #         (json.dumps(final_output, ensure_ascii=False), record['pid'])
#     #     )
#     # finally:
#     #     cur.close()
#     #     con.close()
#     # print(json.dumps(final_output, indent=2, ensure_ascii=False))
#     con = None
#     cur = None
#
#     try:
#         # #  pip install DBUtils
#         # from dbutils.pooled_db import PooledDB
#         #
#         # pool = PooledDB(
#         #     creator=pymysql,
#         #     maxconnections=20,
#         #     host='localhost',
#         #     user='root',
#         #     password='***HIDDEN***',
#         #     database='urban_outfitters'
#         # )
#         # con = pool.connection()
#         # cur = con.cursor()
#         con = pymysql.connect(user='root', host='localhost', database='urban_outfitters', password='***HIDDEN***',
#                               autocommit=True)
#         cur = con.cursor(pymysql.cursors.DictCursor)
#         json_text = json.dumps(result)
#         # preserve dashes
#         json_text = json_text.replace('"-"', '""')
#         updates = []
#         updates.append(
#             (json_text, record['pid'])
#         )
#         # updates.append(
#         #     (json.dumps(json_text, ensure_ascii=False),record['pid'])
#         # )
#         cur.executemany(
#             """
#             UPDATE data_062026
#             SET size_chart=%s,
#                 status='done'
#             WHERE pid=%s
#             """,
#             updates
#         )
#         con.commit()
#     except Exception as e:
#         print(f"PID {record['pid']} ERROR:", e)
#
#     finally:
#         if cur:
#             cur.close()
#         if con:
#             con.close()
#     # cur.execute("update data_062026 set size_chart=%s, status='done' where pid=%s",
#     #             (json.dumps(final_output, ensure_ascii=False), record['pid']))
#     # con.commit()
#     print("Updated: ", record['pid'])


# def convert_to_schema(chart_name,chart_name_title, chart_data, unit, units):
#     if not chart_data:
#         return None
#     # base_label = chart_data.pop("_base_label", "Size")
#     base_label = chart_data.pop("_base_label", "Size") or "Alpha"
#     base_key = normalize_key(base_label) or "alpha"
#     keys = list(chart_data.keys())
#     if not keys:
#         return None
#     # ==================================================
#     # FORMAT 3
#     # {
#     #   "Waist": {"XS":"24","S":"26"},
#     #   "Hip": {"XS":"34","S":"36"}
#     # }
#     # ==================================================
#     if all(isinstance(v, dict) for v in chart_data.values()):
#         all_sizes = []
#         for values in chart_data.values():
#             all_sizes.extend(values.keys())
#         all_sizes = list(dict.fromkeys(all_sizes))
#         base_key = normalize_key(base_label)
#         column_type = "measurement"
#         if any(x in base_label.lower() for x in ["alpha", "numeric", "size"]):
#             column_type = "size_label"
#         if column_type == "size_label":
#             columns = [{
#                 "key": base_key,
#                 "label": base_label,
#                 "type": column_type
#             }]
#         else:
#             columns = [{
#                 "key": base_key,
#                 "label": base_label,
#                 "type": column_type,
#                 "unit": get_unit_from_label(base_label)
#             }]
#         for key in keys:
#             column_type = "measurement"
#             if any(x in key.lower() for x in ["alpha", "numeric", "size"]):
#                 column_type = "size_label"
#             if column_type == "size_label":
#                 columns.append({
#                     "key": normalize_key(key),
#                     "label": key,
#                     "type": column_type
#                 })
#             else:
#                 columns.append({
#                     "key": normalize_key(key),
#                     "label": key,
#                     "type": column_type,
#                     "unit": get_unit_from_label(key)
#                 })
#         rows = []
#         for size in all_sizes:
#             row = {base_key: size}
#             for key in keys:
#                 row[normalize_key(key)] = chart_data[key].get(size)
#             rows.append(row)
#         return {
#             "chart_name": chart_name,
#             # "chart_name": f"{chart_name}" if chart_name else f"{chart_name_title} - {unit}",
#             "chart_type": "",
#             "garment_type": "",
#             "age_group": "",
#             "fit_category": "",
#             "gender": "",
#             # "default_unit": "in",
#             "default_unit": units[0] if units else "",
#             # "available_units": units,
#             "available_units": units if units else [],
#             "columns": columns,
#             "rows": rows
#         }
#     # ==================================================
#     # FORMAT 2
#     # pipe/comma separated strings
#     # ==================================================
#     normalized = {}
#     for key, value in chart_data.items():
#         if isinstance(value, str):
#             if "|" in value:
#                 normalized[key] = [
#                     x.strip()
#                     for x in value.split("|")
#                     if x.strip()
#                 ]
#             elif "," in value:
#                 normalized[key] = [
#                     x.strip()
#                     for x in value.split(",")
#                     if x.strip()
#                 ]
#             else:
#                 normalized[key] = [value]
#         else:
#             normalized[key] = value
#     chart_data = normalized
#     # ==================================================
#     # FORMAT 1
#     # list structure
#     # ==================================================
#     # if not all(isinstance(v, list) for v in chart_data.values()):
#     #     return None
#     cleaned_chart_data = {}
#     for key, value in chart_data.items():
#         new_key = key.strip() if key else "Alpha"
#         cleaned_chart_data[new_key] = value
#     chart_data = cleaned_chart_data
#     columns = []
#     first_col = True
#     # for key in chart_data.keys():
#     #     column_type = "measurement"
#     #     if any(x in key.lower() for x in ["alpha", "numeric", "size"]):
#     #         column_type = "size_label"
#     #     columns.append({
#     #         "key": normalize_key(key),
#     #         "label": key,
#     #         "type": column_type,
#     #         "unit": ""
#     #     })
#     for key in chart_data.keys():
#
#         actual_label = key.strip() if key else "Alpha"
#         actual_key = normalize_key(actual_label) or "alpha"
#
#         column_type = "measurement"
#         if any(x in actual_label.lower() for x in ["alpha", "numeric", "size"]):
#             column_type = "size_label"
#         if column_type == "size_label":
#             columns.append({
#                 "key": actual_key,
#                 "label": actual_label,
#                 "type": column_type
#             })
#         else:
#             columns.append({
#                 "key": actual_key,
#                 "label": actual_label,
#                 "type": column_type,
#                 "unit": get_unit_from_label(actual_label)
#             })
#         # columns.append({
#         #     "key": actual_key,
#         #     "label": actual_label,
#         #     "type": column_type,
#         #     "unit": get_unit_from_label(actual_label)
#         # })
#         first_col = False
#     row_count = max(len(v) for v in chart_data.values())
#     rows = []
#     for i in range(row_count):
#         row = {}
#         for key in chart_data.keys():
#             values = chart_data[key]
#             row_key = normalize_key(key) or "alpha"
#             row[row_key] = (
#                 values[i]
#                 if i < len(values)
#                 else ""
#             )
#             # row[normalize_key(key)] = (
#             #     values[i]
#             #     if i < len(values)
#             #     else None
#             # )
#         rows.append(row)
#     return {
#         "chart_name": chart_name,
#         # "chart_name": f"{chart_name}" if chart_name else f"{chart_name_title} - {unit}",
#         "chart_type": "",
#         "garment_type": "",
#         "age_group": "",
#         "fit_category": "",
#         "gender": "",
#         # "default_unit": "in",
#         "default_unit": units[0] if units else "",
#         # "available_units": units,
#         "available_units": units if units else [],
#         "columns": columns,
#         "rows": rows
#     }


def get_connection():
    return pymysql.connect(
        user='root',
        host='localhost',
        database='urban_outfitters',
        password='***HIDDEN***',
        autocommit=True
    )


if __name__ == "__main__":
    # main()
    con = pymysql.connect(user='root', host='localhost', database='urban_outfitters', password='***HIDDEN***', autocommit=True)
    cur = con.cursor(pymysql.cursors.DictCursor)
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='done' AND pid='UO-76010537-000'")
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='done' AND pid='UO-89297493-000'")
    # cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='done' AND pid='UO-107178394-000'")
    cur.execute(f"SELECT  DISTINCT main_url, pid FROM {db.data_table} where status='done'")
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

    # def extract_data(url, sel, has_key):
    #     hash_id = url_to_id(url)
    #     rows = []
    #
    #     try:
    #         # ------------------------ #
    #         # Parse JSON-LD
    #         # ------------------------ #
    #         blocks = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
    #         if not blocks:
    #             print("No JSON-LD block found")
    #             return rows
    #
    #         try:
    #             data = json.loads(blocks[-1].strip())
    #         except Exception as e:
    #             print(f"JSON-LD parsing failed: {e}")
    #             return rows
    #
    #         name = data.get("name")
    #         mpn = data.get("mpn")
    #         category = data.get("category", "")
    #         category = category.replace(" > ", "/") if category else ""
    #
    #         # Handle OLD + NEW offer structure
    #         offers_data = data.get("offers", {})
    #         sku_list = []
    #
    #         if isinstance(offers_data, list):
    #             sku_list = [
    #                 str(item.get("sku"))
    #                 for item in offers_data
    #                 if item.get("sku")
    #             ]
    #             price_currency = offers_data[0].get("priceCurrency", "USD")
    #
    #         elif isinstance(offers_data, dict):
    #             price_currency = offers_data.get("priceCurrency", "USD")
    #
    #         else:
    #             price_currency = "USD"
    #
    #         # ------------------------ #
    #         # Parse URBN State
    #         # ------------------------ #
    #         state_block = sel.xpath('//script[@id="urbnInitialState"]/text()').get()
    #         if not state_block:
    #             print("No urbnInitialState found")
    #             return rows
    #
    #         try:
    #             temp = json.loads(state_block)
    #             data_2 = json.loads(temp) if isinstance(temp, str) else temp
    #         except Exception as e:
    #             print(f"urbnInitialState parsing failed: {e}")
    #             return rows
    #
    #         # Safe product key detection
    #         try:
    #             key_name = next(
    #                 key for key in data_2.keys()
    #                 if key.startswith("product--")
    #             )
    #         except StopIteration:
    #             print("Product key not found")
    #             return rows
    #
    #         product_core = data_2.get(key_name, {}).get("core", {}).get("catalogData", {})
    #         if not product_core:
    #             print("catalogData missing")
    #             return rows
    #
    #         pid = product_core.get("productId")
    #         rating_count = product_core.get("reviews", {}).get("count")
    #         average_ratings = product_core.get("reviews", {}).get("averageRating")
    #
    #         product_info = product_core.get("product", {})
    #         long_desc = product_info.get("longDescription", "")
    #         brand = product_info.get("brand", "")
    #         brand_desc = product_info.get("brandDescription", "")
    #
    #         description_parts = [long_desc]
    #         if brand_desc:
    #             description_parts.extend([brand, brand_desc])
    #
    #         description = " ".join(description_parts)
    #         clean_description = re.sub(r"[\\\-\*]", "", description)
    #         clean_description = re.sub(r"\s+", " ", clean_description).strip()
    #
    #         color_list = product_core.get("skuInfo", {}).get("primarySlice", {}).get("sliceItems", [])
    #         size_list = product_core.get("skuInfo", {}).get("secondarySlice", {}).get("sliceItems", [])
    #         selector_map = data_2.get(key_name, {}).get("skuSelection", {}).get("selectorMap", {})
    #
    #         # ------------------------ #
    #         # Collect Hidden SKUs (availableStatus == 1111)
    #         # ------------------------ #
    #         invalid_skus = set()
    #         for slice_item in color_list:
    #             for sku_obj in slice_item.get("includedSkus", []):
    #                 if sku_obj.get("availableStatus") == 1111:
    #                     invalid_skus.add(str(sku_obj.get("skuId")))
    #         # Fix slug safely
    #         parsed = urlparse(url)
    #         slug = parsed.path.split("/")[-1]
    #
    #         # ------------------------ #
    #         # Loop Variants
    #         # ------------------------ #
    #         for selector_key, selector_value in selector_map.items():
    #
    #             try:
    #                 if not selector_value:
    #                     continue
    #
    #                 sku_id = selector_value.get("skuId")
    #                 # Skip hidden SKUs
    #                 if sku_id in invalid_skus:
    #                     continue
    #
    #                 if sku_list and sku_id not in sku_list:
    #                     continue
    #
    #                 saleprice = round(float(selector_value.get("salePrice", 0)), 2)
    #                 listprice = round(float(selector_value.get("listPrice", 0)), 2)
    #
    #                 discount = listprice - saleprice
    #                 discount = None if discount == 0 else round(discount, 2)
    #
    #                 stock_level = selector_value.get("stockLevel", 0)
    #                 is_in_stock = "FALSE" if stock_level == 0 else "TRUE"
    #
    #                 colour_id = selector_value.get("colorId")
    #                 size_id = selector_value.get("sizeId")
    #
    #                 # ---- Map Size ----
    #                 size = None
    #                 fit_type = None
    #
    #                 for size_item in size_list:
    #                     fit_label = size_item.get("displayName")
    #                     for s in size_item.get("includedSizes", []):
    #                         if str(s.get("id")) == str(size_id):
    #                             size = s.get("displayName")
    #                             fit_type = fit_label
    #                             break
    #                     if size:
    #                         break
    #
    #                 new_size_format = f"{size} - {fit_type}" if fit_type else size
    #                 fit_type_param = fit_type.upper() if fit_type else ""
    #
    #                 # ---- Map Color ----
    #                 colour_name = None
    #                 image_url = ""
    #                 alt_image_urls = ""
    #                 color_code = None
    #
    #                 for color_item in color_list:
    #                     if str(color_item.get("code")) == str(colour_id):
    #                         colour_name = color_item.get("displayName")
    #                         color_code = color_item.get("code")
    #                         image_id = color_item.get("id")
    #
    #                         images = [
    #                             f"https://images.urbndata.com/is/image/UrbanOutfitters/{image_id}_{img}?$xlarge$&fit=constrain&qlt=80&wid=640"
    #                             for img in color_item.get("images", [])
    #                         ]
    #
    #                         if images:
    #                             image_url = images[0]
    #                             alt_image_urls = " | ".join(images[1:])
    #                         break
    #
    #                 size_param = urllib.parse.quote_plus(size) if size else ""
    #
    #                 variant_url = (
    #                     f"https://www.urbanoutfitters.com/shop/{slug}"
    #                     f"?color={color_code}&type={fit_type_param}&quantity=1&size={size_param}"
    #                 )
    #
    #                 row = {
    #                     "website": "Urban Outfitters",
    #                     "pid": pid,
    #                     "name": name,
    #                     "short_description": None,
    #                     "description": clean_description,
    #                     "category": category,
    #                     "image_url": image_url,
    #                     "price": listprice,
    #                     "price_currency": price_currency,
    #                     "sale_price": saleprice,
    #                     "final_price": saleprice,
    #                     "discount": discount,
    #                     "is_on_sale": None,
    #                     "is_in_stock": is_in_stock,
    #                     "keywords": None,
    #                     "brand": brand if brand else None,
    #                     "manufacturer": None,
    #                     "mpn": mpn,
    #                     "upc_ean": None,
    #                     "sku": sku_id,
    #                     "colour": colour_name,
    #                     "gender": None,
    #                     "size": size,
    #                     "variant_price": saleprice,
    #                     "alternate_image_urls": alt_image_urls,
    #                     "link_url": variant_url,
    #                     "num_ratings": rating_count,
    #                     "avg_ratings": average_ratings,
    #                     "hash_id": str(hash_id),
    #                     "main_url": url,
    #                     "size_type": new_size_format,
    #                 }
    #
    #                 rows.append(row)
    #
    #             except Exception as variant_error:
    #                 print(f"Variant error for {selector_key}: {variant_error}")
    #                 continue
    #         # print("rows ::: ", rows)
    #         return rows
    #
    #     except Exception as main_error:
    #         print(f"Fatal error while extracting {url}: {main_error}")
    #         return rows

    # # full_hash = hashlib.sha256(url.encode()).hexdigest()
    # hash_id = url_to_id(url)
    # rows = []
    # # ------------------------ #
    # # Parse JSON-LD (block 1)
    # # ------------------------ #
    # blocks_1 = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
    # if not blocks_1:
    #     raise ValueError("No application/ld+json blocks found")
    # last_block = blocks_1[-1].strip()
    # try:
    #     data = json.loads(last_block)
    #     valid_sku_list = data.get("offers", {}).get("offers") or []
    #     if not isinstance(valid_sku_list, list):
    #         valid_sku_list = []
    #     sku_list = [
    #         str(item.get("sku"))
    #         for item in valid_sku_list
    #         if isinstance(item, dict) and item.get("sku")
    #     ]
    #     # valid_sku_list = data.get("offers", {}).get("offers")
    #     # sku_list = [str(item.get("sku")) for item in valid_sku_list if "sku" in item]
    #     name = data["name"]
    #     images = data["image"]
    #     mpn = data["mpn"]
    #     category = data["category"].replace(" > ", "/")
    # except json.JSONDecodeError as e:
    #     raise ValueError(f"Failed to parse JSON: {e}")
    # # ------------------------ #
    # # Parse URBN state (block 2)
    # # ------------------------ #
    # blocks_2 = sel.xpath('//script[@id="urbnInitialState"]/text()').get()
    # if not blocks_2:
    #     raise ValueError("No URBN state block found")
    # try:
    #     temp = json.loads(blocks_2)
    #     data_2 = json.loads(temp) if isinstance(temp, str) else temp
    #     slug = url.split("/")[-1]
    #     key_name = f"product--{slug}"
    #     # key_name = "product--" + re.sub(r"[^a-z0-9\-]", "", temp_name)
    #     pid = data_2[key_name]["core"]["catalogData"]["productId"]
    #     rating_count = data_2[key_name]["core"]["catalogData"]["reviews"]["count"]
    #     average_ratings = data_2[key_name]["core"]["catalogData"]["reviews"]["averageRating"]
    #     long_desc = data_2[key_name]["core"]["catalogData"]["product"].get("longDescription", "")
    #     brand = data_2[key_name]["core"]["catalogData"]["product"].get("brand", "")
    #     branddescription = data_2[key_name]["core"]["catalogData"]["product"].get("brandDescription", "")
    #     parts = [long_desc]  # always include long description
    #     if brand and branddescription:
    #         parts.append(brand)
    #     if branddescription:
    #         parts.append(branddescription)
    #     description = " ".join(parts)
    #     # description = " ".join(part for part in [long_desc, brand, branddescription] if part)
    #     clean_description = re.sub(r"[\\\-\*]", "", description)
    #     clean_description = re.sub(r"\s+", " ", clean_description).strip()
    #     color_name_list = data_2[key_name]["core"]["catalogData"]["skuInfo"]["primarySlice"]["sliceItems"]
    #     size_name_list = data_2[key_name]["core"]["catalogData"]["skuInfo"]["secondarySlice"]["sliceItems"]
    #     selector_map = data_2[key_name]["skuSelection"]["selectorMap"]
    #     # ------------------------ #
    #     # Loop through variants
    #     # ------------------------ #
    #     for selector in selector_map:
    #         if selector_map[selector]:
    #             sku_id = selector_map[selector]["skuId"]
    #             # size = selector_map[selector]["size"]
    #             sale_price = selector_map[selector]["salePrice"]
    #             list_Price = selector_map[selector]["listPrice"]
    #             saleprice = float("{:.2f}".format(float(sale_price)))
    #             listprice = float("{:.2f}".format(float(list_Price)))
    #             discount = listprice - saleprice
    #             if discount == 0:
    #                 discount = None
    #             stock_level = selector_map[selector]["stockLevel"]
    #             is_in_stock = "FALSE" if stock_level == 0 else "TRUE"
    #             colour_id = selector_map[selector]["colorId"]
    #             size_id = selector_map[selector]["sizeId"]
    #             size = None
    #             fit_type = None
    #             for size_item in size_name_list:
    #                 url_size_displayname = size_item["displayName"]
    #                 included_size = size_item["includedSizes"]
    #                 for all_size in included_size:
    #                     sizeid = all_size["id"]
    #                     if str(sizeid) == str(size_id):
    #                         size = all_size.get("displayName")
    #                         fit_type = url_size_displayname
    #                         break
    #                 if size:
    #                     break
    #             # Normalize fit_type
    #             if fit_type:
    #                 new_size_formate = f"{size} - {fit_type}"
    #             fit_type = fit_type.upper() if fit_type else ""
    #             colour_name = None
    #             images_code_lst = []
    #             for color_item in color_name_list:
    #                 if str(color_item.get("code")) == str(colour_id):
    #                     color_code =color_item.get("code")
    #                     colour_name = color_item.get("displayName")
    #                     image_id = color_item.get("id")
    #                     images_level_list = color_item.get("images")
    #                     for i in images_level_list:
    #                         images_code = f"{image_id}_{i}"
    #                         images_code_lst.append(images_code)
    #             images = [
    #                 f"https://images.urbndata.com/is/image/UrbanOutfitters/{code}?$xlarge$&fit=constrain&qlt=80&wid=640"
    #                 for code in images_code_lst
    #             ]
    #             if images:
    #                 image_url = images[0]
    #                 alt_image_urls = " | ".join(images[1:])
    #             else:
    #                 image_url = ""
    #                 alt_image_urls = ""
    #             # Safety fallback
    #             price_currency = data.get("offers", {}).get("priceCurrency", "USD")
    #
    #             # ------------------------ #
    #             # ------------------------ #
    #             # Build output row
    #             # ------------------------ #
    #             if sku_id in sku_list:
    #                 size_param = urllib.parse.quote_plus(size) if size else ""
    #                 variant_url = (
    #                     f"https://www.urbanoutfitters.com/shop/{slug}"
    #                     f"?color={color_code}&type={fit_type}&quantity=1&size={size_param}"
    #                 )
    #                 row = {
    #                     "website": "Urban Outfitters",
    #                     "pid": pid,
    #                     "name": name,
    #                     "short_description": None,
    #                     "description": clean_description,
    #                     "category": category,
    #                     "image_url": image_url,
    #                     "price": listprice,
    #                     "price_currency": price_currency,
    #                     "sale_price": saleprice,
    #                     "final_price": saleprice,
    #                     "discount": None if discount==0 else discount,
    #                     "is_on_sale": None,
    #                     "is_in_stock": is_in_stock,
    #                     "keywords": None,
    #                     "brand": brand if brand else None,
    #                     "manufacturer": None,
    #                     "mpn": mpn,
    #                     "upc_ean": None,
    #                     "sku": sku_id,
    #                     "colour": colour_name,
    #                     "gender": None,
    #                     "size": size,
    #                     "variant_price": saleprice,
    #                     "alternate_image_urls": alt_image_urls,
    #                     "link_url": variant_url,
    #                     "num_ratings": rating_count,
    #                     "avg_ratings": average_ratings,
    #                     "hash_id": str(hash_id),
    #                     "main_url": url,
    #                     "size_type": new_size_formate,
    #                     "fit_type": fit_type,
    #                 }

    #  LOAD PROXIES FROM FILE
