# import json
# import db_config_1 as db
# import os
# from parsel import Selector
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from bson import ObjectId
# import pandas as pd
# import numpy as np
#
#
# def get_mongo_collection():
#     db_conn = db.get_db_connection()                            # database name
#     collection = db_conn["project_info"]                 # collection name
#     return collection
#
# def make_json_safe(obj):
#     if isinstance(obj, list):
#         return [make_json_safe(i) for i in obj]
#     elif isinstance(obj, dict):
#         return {
#             k: (str(v) if isinstance(v, ObjectId) else make_json_safe(v))
#             for k, v in obj.items()
#         }
#     else:
#         return obj
#
# def extract_project_information(sel, project_id, project_name, file_name, project_url):
#     final_result = {}
#
#     sections = sel.xpath('//div[@id="DivProject"]//div[contains(@class, "x_panel")]')
#
#     for sec in sections:
#         section_name = sec.xpath('.//div[@class="x_title"]/h2/text()').get()
#         section_name = section_name.strip() if section_name else "Unknown Section"
#
#         # 🔎 Detect sub-sections dynamically (like Bank Details)
#         has_sub_sections = sec.xpath('.//div[contains(@class,"x_content")]//h4')
#
#         section_result = {}
#
#         contents = sec.xpath('.//div[contains(@class,"x_content") and contains(@class,"label-block")]')
#
#         for content in contents:
#             sub_heading = content.xpath('.//h4/text()').get()
#             sub_heading = sub_heading.strip() if sub_heading else None
#
#             rows = content.xpath('.//div[@class="row"]')
#             for row in rows:
#                 labels = row.xpath(".//label/text()").getall()
#                 labels = [l.strip().replace(":", "") for l in labels if l.strip()]
#
#                 value_divs = row.xpath('.//div[contains(@class,"col-md-3") and not(.//label)]')
#                 values = []
#
#                 for div in value_divs:
#                     text = div.xpath('normalize-space(.)').get()
#                     values.append(text if text else None)
#
#                 for i, label in enumerate(labels):
#                     if has_sub_sections and sub_heading:
#                         key = f"{sub_heading}_{label}"
#                     else:
#                         key = label
#
#                     section_result[key] = values[i] if i < len(values) else None
#
#         final_result[section_name] = section_result
#
#     # 🔹 PROJECT METADATA
#     final_result["project_id"] = project_id
#     final_result["project_name"] = project_name
#     final_result["file_name"] = file_name
#     final_result["project_url"] = project_url
#     # print("final_result ::: ", final_result)
#     return final_result
#
#
# def extract_data(page):
#     id = page['SrNo']
#     project_name = page['ProjectName']
#     project_url = page['ViewDetails']
#     project_id = page['project_id']
#     file_name = f"{project_id}_{id}.html"
#     FILE_PATH = f"{db.DATA_PAGESAVE}\\{file_name}"
#     if os.path.exists(FILE_PATH):
#         with open(FILE_PATH, "r", encoding='UTF-8') as f:
#             html_content = f.read()
#     sel = Selector(html_content)
#     final_result = extract_project_information(sel, project_id, project_name, file_name, project_url)
#     # ✅ INSERT INTO MONGODB
#     collection = get_mongo_collection()
#     collection.create_index("project_id", unique=True)
#     collection.update_one(
#         {"project_id": final_result["project_id"]},  # unique key
#         {"$set": final_result},
#         upsert=True
#     )
#     print("Saved to MongoDB:", final_result["project_name"])
#     return final_result
#
#
# def project_info_with_bank_details_json_to_excel(json_path, excel_path):
#     # ==============================
#     # LOAD JSON
#     # ==============================
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#
#     # ==============================
#     # STATIC EXCEL COLUMNS
#     # ==============================
#     columns = [
#         # ---- Project Meta ----
#         "project_id",
#         "project_name",
#         "project_url",
#
#         # ---- Project Information ----
#         "Authority Name",
#         "Plan Approval Number",
#         "Project Status",
#         "Approved Date",
#         "Proposed Date of Completion",
#         "Revised Proposed Date of Completion",
#         "Litigations related to the project ?",
#         "Project Type",
#         "Are there any Promoter(Land Owner/ Investor) (as defined by Telangana RERA Order) in the project ?",
#         "Is the project an MSB or a High-Rise?",
#
#         # ---- Bank Details ----
#         "Collection Account of the Project (100%)_Bank Name",
#         "Collection Account of the Project (100%)_Branch Name",
#         "Collection Account of the Project (100%)_Bank A/c Number",
#         "Collection Account of the Project (100%)_IFSC Code",
#         "Separate Account of the Project (70%)_Bank Name",
#         "Separate Account of the Project (70%)_Branch Name",
#         "Separate Account of the Project (70%)_Bank A/c Number",
#         "Separate Account of the Project (70%)_IFSC Code",
#         "Transaction Account of the Project (30%)_Bank Name",
#         "Transaction Account of the Project (30%)_Branch Name",
#         "Transaction Account of the Project (30%)_Bank A/c Number",
#         "Transaction Account of the Project (30%)_IFSC Code",
#
#         # ---- Land Details ----
#         "Sy.No/TS No.",
#         "Plot No./House No.",
#         "Total Area(In sqmts)",
#         "Area affected in Road widening/FTL of Tanks/Nala Widening(In sqmts)",
#         "Net Area(In sqmts)",
#         "Total Building Units (as per approved plan)",
#         "Proposed Building Units(as per agreement)",
#         "Boundaries East",
#         "Boundaries West",
#         "Boundaries North",
#         "Boundaries South",
#
#         # ---- Built-Up Area ----
#         "Approved Built up Area (In Sqmts)",
#         "Mortgage Area (In Sqmts)",
#
#         # ---- Address Details ----
#         "State",
#         "District",
#         "Mandal",
#         "Village/City/Town",
#         "Street",
#         "Locality",
#         "Pin Code",
#         "file_name"
#     ]
#
#     rows = []
#
#     # ==============================
#     # PROCESS RECORDS
#     # ==============================
#     for item in data:
#         row = {col: "N/A" for col in columns}
#
#         # ---- Meta ----
#         row["project_id"] = item.get("project_id", "N/A")
#         row["project_name"] = item.get("project_name", "N/A")
#         row["project_url"] = item.get("project_url", "N/A")
#         row["file_name"] = item.get("file_name", "N/A")
#
#         # ---- Project Information ----
#         for k, v in item.get("Project Information", {}).items():
#             if k in row:
#                 row[k] = v if v is not None else "N/A"
#
#         # ---- Land Details ----
#         for k, v in item.get("Land Details", {}).items():
#             if k in row:
#                 row[k] = v if v is not None else "N/A"
#
#         # ---- Built-Up Area ----
#         for k, v in item.get("Built-Up Area Details", {}).items():
#             if k in row:
#                 row[k] = v if v is not None else "N/A"
#
#         # ---- Address ----
#         for k, v in item.get("Address Details", {}).items():
#             if k in row:
#                 row[k] = v if v is not None else "N/A"
#
#         # ---- Bank Details ----
#         for k, v in item.get("Bank Details", {}).items():
#             if k in row:
#                 row[k] = v if v is not None else "N/A"
#
#         rows.append(row)
#     # ==============================
#     # CREATE EXCEL
#     # ==============================
#     df = pd.DataFrame(rows, columns=columns)
#     # ---------- Normalize placeholder values ----------
#     # 🔹 Replace placeholder-like strings (including NA variants)
#     df.replace(
#         to_replace=[
#             r'^\s*--\s*$',
#             r'^\s*-\s*$',
#             r'^\s*\.\s*$',
#             r'^\s*$',
#             r'^\s*NA\s*$',
#             r'^\s*N/A\s*$',
#             r'^\s*_\s*$'
#         ],
#         value="N/A",
#         regex=True,
#         inplace=True
#     )
#     # 🔹 Handle real nulls
#     df.replace({None: np.nan}, inplace=True)
#     df.fillna("N/A", inplace=True)
#     df = df.astype(str)
#     with pd.ExcelWriter(
#             excel_path,
#             engine="xlsxwriter",
#             engine_kwargs={"options": {"strings_to_urls": False}}
#     ) as writer:
#         df.to_excel(writer, index=False)
#     print("✅ Excel created successfully")
#     print("📁 Output:", excel_path)
#     print("📊 Total records:", len(df))
#
#
# if __name__ == "__main__":
#     # Fetch scraped links from Mongo
#     links_col = db.get_mongo_links_collection()
#     links = list(links_col.find({"status": "done"}))
#     # links = list(links_col.find({"status": "done"}).limit(10))
#
#     print(f"Total PL fetched: {len(links)}")
#
#     ALL_ROWS = []
#
#     MAX_WORKERS = 10
#
#     with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
#         futures = [executor.submit(extract_data, page) for page in links]
#
#         for future in as_completed(futures):
#             result = future.result()
#             if result:
#                 ALL_ROWS.append(result)
#     json_path = os.path.join(db.RESULT_PAGE, "project_info_bank_details.json")
#     excel_path = os.path.join(db.RESULT_PAGE, "project_info_bank_details.xlsx")
#     with open(json_path, "w", encoding="utf-8") as f:
#         json.dump(ALL_ROWS, f, indent=2, ensure_ascii=False)
#     project_info_with_bank_details_json_to_excel(json_path, excel_path)
#     print("Total saved:", len(ALL_ROWS))


import json
import db_config_1 as db
import os
from parsel import Selector
from concurrent.futures import ThreadPoolExecutor, as_completed
from bson import ObjectId
import pandas as pd
import numpy as np
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("✅ Script started")

# ==============================
# MONGO CONNECTION
# ==============================

def get_mongo_collection():
    db_conn = db.get_db_connection()
    collection = db_conn["project_info"]
    return collection


# ==============================
# JSON SAFE CONVERSION
# ==============================

def make_json_safe(obj):
    if isinstance(obj, list):
        return [make_json_safe(i) for i in obj]
    elif isinstance(obj, dict):
        return {
            k: (str(v) if isinstance(v, ObjectId) else make_json_safe(v))
            for k, v in obj.items()
        }
    else:
        return obj


# ==============================
# EXTRACT PROJECT INFORMATION
# ==============================

def extract_project_information(sel, project_id, project_name, file_name, project_url):
    final_result = {}

    sections = sel.xpath('//div[@id="DivProject"]//div[contains(@class, "x_panel")]')

    for sec in sections:
        section_name = sec.xpath('.//div[@class="x_title"]/h2/text()').get()
        section_name = section_name.strip() if section_name else "Unknown Section"

        has_sub_sections = sec.xpath('.//div[contains(@class,"x_content")]//h4')
        section_result = {}

        contents = sec.xpath('.//div[contains(@class,"x_content") and contains(@class,"label-block")]')

        for content in contents:
            sub_heading = content.xpath('.//h4/text()').get()
            sub_heading = sub_heading.strip() if sub_heading else None

            rows = content.xpath('.//div[@class="row"]')

            for row in rows:
                labels = row.xpath(".//label/text()").getall()
                labels = [l.strip().replace(":", "") for l in labels if l.strip()]

                value_divs = row.xpath('.//div[contains(@class,"col-md-3") and not(.//label)]')
                values = []

                for div in value_divs:
                    text = div.xpath('normalize-space(.)').get()
                    values.append(text if text else None)

                for i, label in enumerate(labels):
                    if has_sub_sections and sub_heading:
                        key = f"{sub_heading}_{label}"
                    else:
                        key = label

                    section_result[key] = values[i] if i < len(values) else None

        final_result[section_name] = section_result

    # Metadata
    final_result["project_id"] = project_id
    final_result["project_name"] = project_name
    final_result["file_name"] = file_name
    final_result["project_url"] = project_url

    return final_result


# ==============================
# MAIN DATA EXTRACTION FUNCTION
# ==============================

def extract_data(page):
    try:
        id = page['SrNo']
        project_name = page['ProjectName']
        project_url = page['ViewDetails']
        project_id = page['project_id']
        pdp_path = page.get("pdp_path")
        if not pdp_path:
            print(f"❌ pdp_path missing for project: {project_id}")
            return None
        FILE_PATH = os.path.join("X:", page["pdp_path"])
        FILE_PATH = pdp_path.replace("J:", "X:", 1)

        file_name = f"{project_id}_{id}.html"
        # FILE_PATH = os.path.join(db.DATA_PAGESAVE, file_name)

        # 🔴 If file does not exist → skip
        if not os.path.exists(FILE_PATH):
            print(f"❌ File not found: {FILE_PATH}")
            return None

        with open(FILE_PATH, "r", encoding="UTF-8") as f:
            html_content = f.read()

        # 🔴 If file is empty → skip
        if not html_content.strip():
            print(f"❌ Empty file: {FILE_PATH}")
            return None

        sel = Selector(text=html_content)

        final_result = extract_project_information(
            sel, project_id, project_name, file_name, project_url
        )

        # Save to MongoDB
        collection.update_one(
            {"project_id": final_result["project_id"]},
            {"$set": final_result},
            upsert=True
        )

        print("✅ Saved:", final_result["project_name"])
        return final_result

    except Exception as e:
        print(f"❌ Error processing project_id {page.get('project_id')}: {e}")
        return None


# ==============================
# JSON TO EXCEL
# ==============================

def extract_keys(obj, keys_set):
    """
    Recursively extract all keys from nested JSON (dicts + lists)
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys_set.add(k)
            extract_keys(v, keys_set)
    elif isinstance(obj, list):
        for item in obj:
            extract_keys(item, keys_set)


def flatten_json(obj, row):
    """
    Recursively flatten JSON into a single-level dictionary
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                flatten_json(v, row)
            else:
                row[k] = v if v not in [None, ""] else "N/A"

    elif isinstance(obj, list):
        for item in obj:
            flatten_json(item, row)


def project_info_with_bank_details_json_to_excel(json_path, excel_path):

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # -------------------------------
    # Step 1: Extract all unique keys
    # -------------------------------
    columns_set = set()

    for item in data:
        extract_keys(item, columns_set)

    # Add metadata columns if not present
    columns_set.update(["project_id", "project_name", "project_url", "file_name"])

    columns = list(columns_set)

    # -------------------------------
    # Step 2: Create rows
    # -------------------------------
    rows = []

    for item in data:
        row = {col: "N/A" for col in columns}
        flatten_json(item, row)
        rows.append(row)

    # -------------------------------
    # Step 3: Create DataFrame
    # -------------------------------
    df = pd.DataFrame(rows)

    df.replace({None: np.nan}, inplace=True)
    df.replace(to_replace=["-", "", None], value="N/A", inplace=True)
    df = df.replace(r'\s+', ' ', regex=True)
    # ---------- Normalize placeholder values ----------
    df.replace(
        to_replace=[
            r'^\s*--\s*$',
            r'^\s*-\s*$',
            r'^\s*\.\s*$',
            r'^\s*$',
            r'^\s*NA\s*$',
            r'^\s*N/A\s*$',
            r'^\s*_\s*$'
        ],
        value="N/A",
        regex=True,
        inplace=True
    )
    df.fillna("N/A", inplace=True)
    df = df.astype(str)
    with pd.ExcelWriter(
            excel_path,
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_urls": False}}
    ) as writer:
        df.to_excel(writer, index=False)
    print(f"Excel created successfully → {excel_path}")
    # df.fillna("N/A", inplace=True)
    # df = df.astype(str)
    #
    # # -------------------------------
    # # Step 4: Export to Excel
    # # -------------------------------
    # with pd.ExcelWriter(
    #     excel_path,
    #     engine="xlsxwriter",
    #     engine_kwargs={"options": {"strings_to_urls": False}}
    # ) as writer:
    #     df.to_excel(writer, index=False)
    #
    # print("✅ Excel created successfully")
    print("📊 Total records:", len(df))

#
# def project_info_with_bank_details_json_to_excel(json_path, excel_path):
#
#     with open(json_path, "r", encoding="utf-8") as f:
#         data = json.load(f)
#
#     columns = list({
#         key
#         for item in data
#         for section in item.values()
#         if isinstance(section, dict)
#         for key in section.keys()
#     })
#
#     # Add metadata columns
#     columns.extend(["project_id", "project_name", "project_url", "file_name"])
#     columns = list(set(columns))
#
#     rows = []
#
#     for item in data:
#         row = {col: "N/A" for col in columns}
#
#         for key, value in item.items():
#             if isinstance(value, dict):
#                 for k, v in value.items():
#                     row[k] = v if v else "N/A"
#             else:
#                 row[key] = value if value else "N/A"
#
#         rows.append(row)
#
#     df = pd.DataFrame(rows)
#     df.replace({None: np.nan}, inplace=True)
#     df.fillna("N/A", inplace=True)
#     df = df.astype(str)
#
#     with pd.ExcelWriter(
#         excel_path,
#         engine="xlsxwriter",
#         engine_kwargs={"options": {"strings_to_urls": False}}
#     ) as writer:
#         df.to_excel(writer, index=False)
#
#     print("✅ Excel created successfully")
#     print("📊 Total records:", len(df))
#

# ==============================
# MAIN EXECUTION
# ==============================

if __name__ == "__main__":

    # Get Mongo collections
    collection = get_mongo_collection()
    collection.create_index("project_id", unique=True)

    links_col = db.get_mongo_links_collection()
    links = list(links_col.find({"status": "done"}))

    print(f"Total PL fetched: {len(links)}")

    ALL_ROWS = []
    MAX_WORKERS = 10

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(extract_data, page) for page in links]

        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    ALL_ROWS.append(make_json_safe(result))
            except Exception as e:
                print("❌ Thread error:", e)

    # Save JSON
    json_path = os.path.join(db.RESULT_PAGE, "project_info_bank_details.json")
    excel_path = os.path.join(db.RESULT_PAGE, "project_info_bank_details.xlsx")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ALL_ROWS, f, indent=2, ensure_ascii=False)

    # Convert to Excel
    project_info_with_bank_details_json_to_excel(json_path, excel_path)

    print("🎉 Total saved:", len(ALL_ROWS))
