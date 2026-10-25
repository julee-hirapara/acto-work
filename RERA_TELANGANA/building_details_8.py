import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from lxml import html
from bson import ObjectId
import json
import pandas as pd
import os
import db_config_1 as db
import numpy as np


def is_hidden_row(row):
    style = row.xpath("./@style")
    return bool(style and "display:none" in style[0].replace(" ", "").lower())

def is_invalid(value):
    return not value or value.strip().lower() in {"na", "n/a", "null", ""}


def safe_text_list(lst):
    return lst[0].strip() if lst and lst[0].strip() else ""
import re

def clean_text(text):
    if not text:
        return ""
    # Remove newlines and extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def building_details_main_table(html_content, d_project_name, project_url, project_id, file_name):
    tree = html.fromstring(html_content)
    # ==================================================
    # FIND MAIN BUILDING TABLE (BY HEADER TEXT)
    # ==================================================
    main_table = tree.xpath("//div[@id='DivBuilding']//table[.//th[normalize-space()='Project Name']]")
    if not main_table:
        print("❌ Main building table not found")
        # try:
        #     conn = db.get_db_connection(db.db_name)
        #     cur = conn.cursor()
        #     update_query = f"UPDATE `{db.link_table}` SET status = %s WHERE SrNo = %s"
        #     cur.execute(update_query, ("no", projectRegId))
        #     conn.commit()
        #     cur.close()
        #     conn.close()
        #     print(f"❌ update_status not getting ")
        # except Exception as e:
        #     print(f"❌ Database error for : {e}")
        return None, None, None
    main_table = main_table[0]
    # -----------------------------
    # Extract headers
    # -----------------------------
    headers = [
        h.text_content().strip()
        for h in main_table.xpath(".//tr[1]/th")
    ]
    table_1 = []
    sub_table_1 = []
    sub_table_2 = []
    # -----------------------------
    # Extract ALL data rows
    # -----------------------------
    main_rows = main_table.xpath(
        "./tr[td and not(.//table) and not(contains(translate(@style,' ',''),'display:none'))] | "
        "./tbody/tr[td and not(.//table) and not(contains(translate(@style,' ',''),'display:none'))]"
    )
    # main_rows = main_table.xpath("./tr[td and not(.//table)] | ./tbody/tr[td and not(.//table)]")
    print(f"Total main rows found: {len(main_rows)}")

    for row in main_rows:
        values = [
            td.text_content().strip() or "N/A"
            for td in row.xpath("./td")
        ]
        main_record = dict(zip(headers, values))
        # ❌ Skip invalid main rows
        if (
                is_invalid(main_record.get("Sr.No."))
                or is_invalid(main_record.get("Project Name"))
        ):
            continue
        # ---------------- HASH ID ----------------
        project_name = main_record.get("Project Name", "")
        building_name = main_record.get("Name", "")
        proposed_date = main_record.get(
            "Proposed Date of Completion (As approved by Competent Authority)", ""
        )
        raw_key = f"{project_id}-{project_name}-{building_name}-{proposed_date}"
        main_table_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:24]
        main_record["project_id"] = project_id
        main_record["project_url"] = project_url
        main_record["file_path"] = file_name
        main_record["main_table_key"] = main_table_key
        table_1.append(main_record)

        # ==================================================
        # SUB TABLE 1 — FLOOR DETAILS
        # ==================================================
        floor_table = row.xpath(
            ".//following::table[.//th[normalize-space()='Floor ID']][1]"
        )
        if floor_table:
            floor_headers = [
                h.text_content().strip()
                for h in floor_table[0].xpath(".//tr[1]/th")
            ]
            # for fr in floor_table[0].xpath(".//tr[td]"):
            for fr in floor_table[0].xpath(
                    ".//tr[td and not(.//table) and not(contains(translate(@style,' ',''),'display:none'))]"
            ):
                floor_values = [
                    td.text_content().strip() or "N/A"
                    for td in fr.xpath("./td")
                ]
                record = dict(zip(floor_headers, floor_values))

                # ❌ Skip invalid floor rows
                if is_invalid(record.get("Sr.No.")):
                    continue

                record.update({
                    "project_id": project_id,
                    "project_url": project_url,
                    "project_name": d_project_name,
                    "file_path": file_name,
                    "main_table_key": main_table_key,
                })

                sub_table_1.append(record)
        # ==================================================
        # SUB TABLE 2 — TASK / ACTIVITY
        # ==================================================
        task_table = row.xpath(
            ".//following::table[.//th[contains(normalize-space(),'Tasks')]][1]"
        )

        if task_table:
            for tr in task_table[0].xpath(".//tr[td and not(.//table)]"):

                # ❌ Skip hidden rows (display:none)
                tr_style = tr.xpath("./@style")
                if tr_style and "display:none" in tr_style[0].replace(" ", "").lower():
                    continue

                sr_no = clean_text(tr.xpath("./td[1]/text()")[0]) if tr.xpath("./td[1]/text()") else ""
                task = clean_text(" ".join(tr.xpath("./td[2]//text()")))
                perc = clean_text(tr.xpath("./td[3]/text()")[0]) if tr.xpath("./td[3]/text()") else ""

                # ❌ Skip invalid Sr.No.
                if is_invalid(sr_no):
                    continue

                sub_table_2.append({
                    "project_id": project_id,
                    "project_url": project_url,
                    "project_name": d_project_name,
                    "file_path": file_name,
                    "main_table_key": main_table_key,
                    "Sr.No.": sr_no,
                    "Tasks / Activity": task or "N/A",
                    "Percentage of Work": perc or "N/A",
                })

    return table_1, sub_table_1, sub_table_2


def get_mongo_collections():
    db_conn = db.get_db_connection()                           # database name
    return {
        "main": db_conn["building_details_main_table"],
        "floor": db_conn["building_details_sub_table_1"],
        "task": db_conn["building_details_sub_table_2"]
    }

def save_tables_to_json(table_1, sub_table_1, sub_table_2):
    main_json_path = os.path.join(db.RESULT_PAGE, "rera_telangana_building_details_main_table.json")
    sub_1_json_path = os.path.join(db.RESULT_PAGE, "rera_telangana_building_details_sub_table_1.json")
    sub_2_json_path = os.path.join(db.RESULT_PAGE, "rera_telangana_building_details_sub_table_2.json")
    if table_1:
        with open(main_json_path, "w", encoding="utf-8") as f:
            json.dump(table_1, f, indent=2, ensure_ascii=False)

    if sub_table_1:
        with open(sub_1_json_path, "w", encoding="utf-8") as f:
            json.dump(sub_table_1, f, indent=2, ensure_ascii=False)

    if sub_table_2:
        with open(sub_2_json_path, "w", encoding="utf-8") as f:
            json.dump(sub_table_2, f, indent=2, ensure_ascii=False)


def extract_data(page):
    # 🔥 SAFETY FIX
    if hasattr(page, "to_dict"):
        page = page.to_dict()

    id = page.get('SrNo')
    project_name = page.get('ProjectName')
    project_url = page.get('ViewDetails')
    project_id = page.get('project_id')
    pdp_path = page.get("pdp_path")
    if not pdp_path:
        print(f"❌ pdp_path missing for project: {project_id}")
        return None
    if not all([id, project_name, project_url]):
        print("⚠ Missing required fields, skipping record")
        # return None
    file_name = f"{project_id}_{id}.html"
    FILE_PATH = os.path.join("J:", page["pdp_path"])
    FILE_PATH = pdp_path.replace("J:", "X:", 1)

    if not os.path.exists(FILE_PATH):
        return None
    # FILE_PATH = f"{db.DATA_PAGESAVE}\\{file_name}"
    if not os.path.exists(FILE_PATH):
        return None
    with open(FILE_PATH, "r", encoding="UTF-8") as f:
        html_content = f.read()
    # building_details_main_table(html_content, id, project_name, project_url, project_id)
    table_1, sub_table_1, sub_table_2 = building_details_main_table(html_content, project_name, project_url, project_id, file_name)
    collections = get_mongo_collections()
    if table_1:
        collections["main"].insert_many(make_json_safe(table_1))
    if sub_table_1:
        collections["floor"].insert_many(make_json_safe(sub_table_1))
    if sub_table_2:
        collections["task"].insert_many(make_json_safe(sub_table_2))
    print("Inserted ___ ", id)
    # try:
    #     conn = db.get_db_connection(db.db_name)
    #     cur = conn.cursor()
    #     update_query = f"UPDATE `{db.link_table}` SET status = %s WHERE SrNo = %s"
    #     cur.execute(update_query, ("processed", id))
    #     conn.commit()
    #     cur.close()
    #     conn.close()
    #     print(f"✔ Saved all category links.")
    # except Exception as e:
    #     print(f"❌ Database error for : {e}")
    return table_1, sub_table_1, sub_table_2


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


def building_details_json_to_excel(json_file, excel_file, column_order=None):
    # 🔹 Load JSON
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        print(f"⚠ Empty JSON file: {json_file}")
        return
    # 🔹 Remove MongoDB _id if present
    for row in data:
        row.pop("_id", None)
    # 🔹 Create DataFrame
    df = pd.DataFrame(data)
    # 🔹 Reorder columns (only existing ones)
    if column_order:
        df = df[[col for col in column_order if col in df.columns]]
    # 🔹 Fill missing values
    df.replace("", "N/A", inplace=True)
    df = df.replace(r'\s+', ' ', regex=True)
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
    # 🔹 Handle real nulls
    df.replace({None: np.nan}, inplace=True)
    df.fillna("N/A", inplace=True)
    df = df.astype(str)

    with pd.ExcelWriter(
            excel_file,
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_urls": False}}
    ) as writer:
        df.to_excel(writer, index=False)
    print(f"✅ Excel created: {excel_file}")

if __name__ == "__main__":
    # Fetch scraped links from Mongo
    links_col = db.get_mongo_links_collection()
    links = list(links_col.find({"status": "done"}))
    # links = list(links_col.find({"status": "done"}).limit(10))
    print(f"Total PL fetched: {len(links)}")
    ALL_TABLE_1 = []
    ALL_SUB_TABLE_1 = []
    ALL_SUB_TABLE_2 = []
    MAX_WORKERS = 10
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(extract_data, page) for page in links]
        for future in as_completed(futures):
            result = future.result()
            if not result:
                continue
            if result:
                table_1, sub_table_1, sub_table_2 = result
                if table_1:
                    ALL_TABLE_1.extend(table_1)
                if sub_table_1:
                    ALL_SUB_TABLE_1.extend(sub_table_1)
                if sub_table_2:
                    ALL_SUB_TABLE_2.extend(sub_table_2)
    main_json_path = os.path.join(db.RESULT_PAGE, "building_details_main_table.json")
    main_excel_path = os.path.join(db.RESULT_PAGE, "building_details_main_table.xlsx")
    sub_1_json_path = os.path.join(db.RESULT_PAGE, "building_details_sub_table_1.json")
    sub_1_excel_path = os.path.join(db.RESULT_PAGE, "building_details_sub_table_1.xlsx")
    sub_2_json_path = os.path.join(db.RESULT_PAGE, "building_details_sub_table_2.json")
    sub_2_excel_path = os.path.join(db.RESULT_PAGE, "building_details_sub_table_2.xlsx")
    if ALL_TABLE_1:
        with open(main_json_path, "w", encoding="utf-8") as f:
            json.dump(ALL_TABLE_1, f, indent=2, ensure_ascii=False)

    if ALL_SUB_TABLE_1:
        with open(sub_1_json_path, "w", encoding="utf-8") as f:
            json.dump(ALL_SUB_TABLE_1, f, indent=2, ensure_ascii=False)

    if ALL_SUB_TABLE_2:
        with open(sub_2_json_path, "w", encoding="utf-8") as f:
            json.dump(ALL_SUB_TABLE_2, f, indent=2, ensure_ascii=False)
    # save_tables_to_json(ALL_TABLE_1, ALL_SUB_TABLE_1, ALL_SUB_TABLE_2)
    print("building main table Details saved:", len(ALL_TABLE_1))
    print("building sub table 1 Details saved:", len(ALL_SUB_TABLE_1))
    print("building sub table 2 Details saved:", len(ALL_SUB_TABLE_2))
    # =====================================================
    # 🔹 1️⃣ BUILDING DETAILS – MAIN TABLE
    # =====================================================
    building_details_json_to_excel(main_json_path, main_excel_path,
        column_order=[
            "project_id",
            "project_url",
            "main_table_key",
            "Sr.No.",
            "Project Name",
            "Name",
            "Proposed Date of Completion (As approved by Competent Authority)",
            "Number of Basement's",
            "Number of Plinth",
            "Number of Podium's",
            "Number of Slab of Super Structure",
            "Number of Stilts",
            "Number of Open Parking",
            "Total Parking Area (In sqmts)",
            "file_path"
        ]
    )
    # =====================================================
    # 🔹 2️⃣ BUILDING DETAILS – FLOOR TABLE
    # =====================================================
    building_details_json_to_excel(sub_1_json_path, sub_1_excel_path,
        column_order=[
            "project_id",
            "project_url",
            "project_name",
            "main_table_key",
            "Sr.No.",
            "Floor ID",
            "Mortgage Area",
            "Apartment Type",
            "Saleable Area (in Sqmts)",
            "Number of Apartment",
            "Number of Booked Apartment",
            "file_path"
        ]
    )

    # =====================================================
    # 🔹 3️⃣ BUILDING DETAILS – TASK / ACTIVITY TABLE
    # =====================================================
    building_details_json_to_excel(sub_2_json_path, sub_2_excel_path,
        column_order=[
            "project_id",
            "project_url",
            "project_name",
            "main_table_key",
            "Sr.No.",
            "Tasks / Activity",
            "Percentage of Work",
            "file_path"
        ]
    )
    print("\n🎉 All Building Details Excel files created successfully!")
