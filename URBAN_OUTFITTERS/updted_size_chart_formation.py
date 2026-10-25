# import db_config_1 as db
# import pymysql
# import os
# import json
#
#
# def get_table_htmls(response):
#     table_htmls = []
#     items = response.get("items", [])
#     for item in items:
#         # CASE 1 → guides
#         for guide in item.get("guides", []):
#             # inchesTables
#             for table in guide.get("inchesTables", []):
#                 if table.get("tableHtml"):
#                     table_htmls.append(table["tableHtml"])
#             # centimetersTables
#             for table in guide.get("centimetersTables", []):
#                 if table.get("tableHtml"):
#                     table_htmls.append(table["tableHtml"])
#         # CASE 2 → tables
#         for table in item.get("tables", []):
#             if table.get("tableHtml"):
#                 table_htmls.append(table["tableHtml"])
#     return table_htmls
#
# def other_data(size_chart_response):
#     chart_name = None
#     items = size_chart_response.get("items", [])
#     for item in items:
#         # CASE 1 → guides
#         for guide in item.get("guides", []):
#             chart_name = guide.get("displayName", "")
#         if not chart_name:
#             chart_name = item.get("displayTitle")
#     print("------------------------------------------------------------------")
#     print(chart_name)
#     print("------------------------------------------------------------------")
#
#
# def main(rows):
#     if not rows:
#         return
#     for r in rows:
#         pid = r["product_id"]
#         filename = os.path.join(db.SIZE_PAGESAVE, f"{pid}.json")
#         if os.path.exists(filename):
#             with open(filename, "r", encoding="utf-8") as f:
#                 size_chart_response =  json.load(f)
#                 print(size_chart_response)
#                 other_data(size_chart_response)
#                 print("\n")
#                 all_tables = get_table_htmls(size_chart_response)
#                 print(all_tables)
#
#
# if __name__ == "__main__":
#     # start_index = sys.argv[1]
#     # end_index = sys.argv[-1]
#     # print("start:", start_index)
#     # print("end:", end_index)
#     conn = db.get_db_connection(db.db_name)
#     cur = conn.cursor(pymysql.cursors.DictCursor)
#     # cur.execute(f"SELECT * FROM {db.link_table} WHERE status = 'pending' AND ID BETWEEN {start_index} AND  {end_index} ORDER BY ID ASC limit 100")
#     cur.execute(f"SELECT * FROM {db.link_table} WHERE status = 'done' ORDER BY ID DESC limit 100")
#     # cur.execute(f"SELECT * FROM {db.link_table} WHERE hash_id = '9334882367448384'  ORDER BY ID ASC")
#     rows = cur.fetchall()
#     main(rows)
#     cur.close()
#     conn.close()



from parsel import Selector
import json
import re
import os
import pymysql
from concurrent.futures import ThreadPoolExecutor


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


def main(record):
    file_name = fr"D:\Julee\PAGESAVES\URBAN_OUTFITTERS\06_2026\size_chart\{record['pid']}.json"
    if not os.path.exists(file_name):
        return None
    with open(file_name, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
    # data = record["size_chart_response"]
    # if isinstance(data, str):
    #     data = json.loads(data)

    extracted_data = {}
    try:
        for raw in data['items']:
            chart_name_title = raw.get("displayTitle")
            for raw_2 in raw['guides']:
                display_name = raw_2.get("displayName", "size_guide")
                extracted_data[display_name] = {}
                if "inchesTables" in (raw_2.keys()):
                    for raw_3 in raw_2['inchesTables']:
                        table = raw_3['tableHtml']
                        table = Selector(table)
                        extracted_data[display_name]['inches'] = extract_table(table)
                if "centimetersTables" in (raw_2.keys()):
                    for raw_3 in raw_2['centimetersTables']:
                        table = raw_3['tableHtml']
                        table = Selector(table)
                        extracted_data[display_name]['centimeters'] = extract_table(table)

    except Exception as e:
        e = str(e)
        if 'guides' in e:
            counter = 1
            for raw in data['items']:
                display_name = raw.get("displayTitle")
                for raw_2 in raw['tables']:
                    extracted_data[display_name] = extract_table(Selector(raw_2['tableHtml']))
                    counter += 1
        else:
            print(e)
    # if extracted_data:
    #     # print(extracted_data)
    final_output = []
    for chart_name, chart_values in extracted_data.items():
        units = []
        if "inches" in chart_values:
            units.append("in")
        if "centimeters" in chart_values:
            units.append("cm")
        if units == []:
            units = "in"
        # guides structure
        if isinstance(chart_values, dict) and (
                "inches" in chart_values or
                "centimeters" in chart_values
        ):
            if "inches" in chart_values:
                final_output.append(
                    convert_to_schema(
                        chart_name,
                        # chart_name_title,
                        chart_values["inches"],
                        "in",
                        units
                    )
                )
            if "centimeters" in chart_values:
                final_output.append(
                    convert_to_schema(
                        chart_name,
                        # chart_name_title,
                        chart_values["centimeters"],
                        "cm",
                        units
                    )
                )
        # tables structure
        else:
            final_output.append(
                convert_to_schema(
                    # chart_name_title,
                    chart_name,
                    chart_values,
                    "in",
                    units
                )
            )
    # con = get_connection()
    # cur = con.cursor()
    # try:
    #     cur.execute(
    #         "update data_062026 set size_chart=%s, status='done' where pid=%s",
    #         (json.dumps(final_output, ensure_ascii=False), record['pid'])
    #     )
    # finally:
    #     cur.close()
    #     con.close()
    # print(json.dumps(final_output, indent=2, ensure_ascii=False))
    cur.execute("update data_062026 set size_chart=%s, status='done' where pid=%s",
                (json.dumps(final_output, ensure_ascii=False), record['pid']))
    con.commit()
    print("Updated: ", record['pid'])


def normalize_key(text):
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
    return text.strip("_")

def get_unit_from_label(label):
    label = (label or "").lower()
    if "(in)" in label or " inch" in label or " inches" in label:
        return "in"
    if "(cm)" in label or " centimeter" in label or " centimeters" in label:
        return "cm"
    return ""

def convert_to_schema(chart_name, chart_data, unit, units):
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
        columns = [{
            "key": base_key,
            "label": base_label,
            "type": column_type,
            "unit": get_unit_from_label(base_label),
        }]
        for key in keys:
            column_type = "measurement"
            if any(x in key.lower() for x in ["alpha", "numeric", "size"]):
                column_type = "size_label"
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
            "default_unit": "in",
            "available_units": units,
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

        columns.append({
            "key": actual_key,
            "label": actual_label,
            "type": column_type,
            "unit": get_unit_from_label(actual_label)
        })
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
                else None
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
        "default_unit": "in",
        "available_units": units,
        "columns": columns,
        "rows": rows
    }

# def convert_to_schema(chart_name, chart_data, unit, units):
#     keys = list(chart_data.keys())
#     if not keys:
#         return None
#     first_value = chart_data[keys[0]]
#     # ----------------------------------
#     # FORMAT 3
#     # nested dictionaries
#     # ----------------------------------
#     # if isinstance(first_value, dict):
#     if all(isinstance(v, dict) for v in chart_data.values()):
#         all_sizes = []
#         for values in chart_data.values():
#             all_sizes.extend(values.keys())
#         all_sizes = list(dict.fromkeys(all_sizes))
#         size_column = "size"
#         for candidate in ["size", "alpha", "length"]:
#             if candidate.lower() in [s.lower() for s in all_sizes]:
#                 size_column = normalize_key(candidate)
#                 break
#         columns = [{
#             "key": size_column,
#             "label": size_column.replace("_", " ").title(),
#             "type": "size_label"
#         }]
#         # all_sizes = []
#         # for values in chart_data.values():
#         #     all_sizes.extend(values.keys())
#         # all_sizes = list(dict.fromkeys(all_sizes))
#         # base_label = chart_data.pop("_base_label", "Size")
#         # base_key = normalize_key(base_label)
#         # columns = [{
#         #     "key": base_key,
#         #     "label": base_label,
#         #     "type": "size_label"
#         # }]
#         # columns = [{
#         #     "key": "size",
#         #     "label": "Size",
#         #     "type": "size_label"
#         # }]
#         for key in keys:
#             columns.append({
#                 "key": normalize_key(key),
#                 "label": key,
#                 "type": "measurement"
#             })
#         rows = []
#         for size in all_sizes:
#             row = {
#                 "size": size
#             }
#             for key in keys:
#                 row[normalize_key(key)] = (chart_data[key].get(size))
#             rows.append(row)
#         return {
#             "chart_name": chart_name,
#             "chart_type": "",
#             "garment_type": "",
#             "age_group": "",
#             "fit_category": "",
#             "gender": "",
#             "default_unit": "in",
#             "available_units": units,
#             "columns": columns,
#             "rows": rows
#         }
#     # ----------------------------------
#     # FORMAT 2
#     # comma-separated strings
#     # ----------------------------------
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
#     # ----------------------------------
#     # FORMAT 1
#     # lists
#     # ----------------------------------
#     columns = []
#     for key in chart_data.keys():
#         columns.append({
#             "key": normalize_key(key),
#             "label": key,
#             "type": "size_label"
#         })
#     row_count = max(
#         len(v)
#         for v in chart_data.values()
#     )
#     rows = []
#     for i in range(row_count):
#         row = {}
#         for key in chart_data.keys():
#             values = chart_data[key]
#             row[normalize_key(key)] = (
#                 values[i]
#                 if i < len(values)
#                 else None
#             )
#         rows.append(row)
#     return {
#         "chart_name": chart_name,
#         "chart_type": "",
#         "garment_type": "",
#         "age_group": "",
#         "fit_category": "",
#         "gender": "",
#         # "chart_name": chart_name,
#         # "chart_type": "size_conversion",
#         "default_unit": "in",
#         "available_units": units,
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
    con = pymysql.connect(user='root', host='localhost', database='urban_outfitters', password='***HIDDEN***')
    cur = con.cursor(pymysql.cursors.DictCursor)
    # cur.execute(f"SELECT  DISTINCT id, main_url, pid FROM data_062026 where status='pending' ORDER BY id ASC LIMIT 1000")
    cur.execute(f"SELECT  DISTINCT main_url, pid FROM data_062026 where status='pending' AND id BETWEEN 40000 AND 60000")
    records = cur.fetchall()
    # con = pymysql.connect(user='root',host='localhost',database='urban_outfitters',password='***HIDDEN***')
    # cur = con.cursor(pymysql.cursors.DictCursor)
    # cur.execute("""
    #         SELECT DISTINCT main_url, pid, size_chart_response
    #         FROM data_062026
    #         WHERE status='pending'
    #         LIMIT 1000
    #     """)
    # records = cur.fetchall()
    # cur.close()
    # con.close()
    # with ThreadPoolExecutor(max_workers=20) as executor:
    #     executor.map(main, records)
    for record in records:
        main(record)