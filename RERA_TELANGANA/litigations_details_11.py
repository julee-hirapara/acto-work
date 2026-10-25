import json
import db_config_1 as db
import os
from parsel import Selector
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np
from bson import ObjectId


def extract_litigations_details(sel, project_name, project_url, project_id, file_path):
    case_details = []
    table = sel.xpath('//div[@id="DivCaseDetails"]//table')
    if not table:
        return case_details
    # 🔹 Extract headers
    headers = table.xpath('.//tr[1]/th//text()').getall()
    headers = [h.strip() for h in headers if h.strip()]
    # 🔹 Extract data rows
    rows = table.xpath('.//tr[position() > 1 and td]')
    for row in rows:
        values = row.xpath('./td')
        data = {}
        for i, header in enumerate(headers):
            # Safe check
            if i >= len(values):
                data[header] = ""
                continue
            # Normal cell extraction
            cell_text = values[i].xpath('normalize-space(.)').get()
            data[header] = cell_text
        # 🔹 Add project metadata (same as members)
        data.update({
            "project_id": project_id,
            "project_url": project_url,
            "project_name": project_name,
            "file_name": file_path,
        })
        case_details.append(data)
    return case_details


def extract_data(page):
    id = page['SrNo']
    project_name = page['ProjectName']
    project_url = page['ViewDetails']
    project_id = page['project_id']
    pdp_path = page.get("pdp_path")
    if not pdp_path:
        print(f"❌ pdp_path missing for project: {project_id}")
        return None
    file_name = f"{project_id}_{id}.html"
    # FILE_PATH = os.path.join("Z:", page["pdp_path"])
    FILE_PATH = pdp_path.replace("J:", "X:", 1)

    # FILE_PATH = f"{db.DATA_PAGESAVE}\\{file_name}"
    if not os.path.exists(FILE_PATH):
        return None
    with open(FILE_PATH, "r", encoding="UTF-8") as f:
        html_content = f.read()
    sel = Selector(html_content)
    litigations_details = extract_litigations_details(sel, project_name, project_url, project_id, file_name)
    if not litigations_details:
        return None
    collection = get_mongo_collection()
    # ✅ SIMPLE INSERT — NO UNIQUE CHECK
    collection.insert_many(litigations_details)
    print(f"Inserted {len(litigations_details)} Litigations details for project:", project_name)
    return litigations_details


def get_mongo_collection():
    db_conn = db.get_db_connection()                          # database name
    collection = db_conn["litigations_details"]                 # collection name
    return collection


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

def litigations_details_json_to_excel(json_path, excel_path):
    # 🔹 Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 🔹 Convert Mongo _id to string (safety)
    for row in data:
        row.pop("_id", None)
    # 🔹 Define column order (optional but recommended)
    columns = [
        "project_id",
        "project_url",
        "Project Name",
        "Name Of The Court",
        "Case Number",
        "Case Type",
        "Preventive/Injunction/Interim Order is Passed?",
        "Petition Name",
        "Other Petition Details",
        "Year",
        "Present Status",
        "Case Related Documents",
        "file_name",
    ]

    # 🔹 Create DataFrame
    df = pd.DataFrame(data)
    # 🔹 Reorder columns (only existing ones)
    df = df[[col for col in columns if col in df.columns]]
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
    # 🔹 Export to Excel
    # df.to_excel(excel_path, index=False)
    with pd.ExcelWriter(
            excel_path,
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_urls": False}}
    ) as writer:
        df.to_excel(writer, index=False)

    print("✅ Excel file created successfully:", excel_path)

if __name__ == "__main__":
    # Fetch scraped links from Mongo
    links_col = db.get_mongo_links_collection()
    # links = list(links_col.find({"status": "done"}).limit(10))
    links = list(links_col.find({"status": "done"}))
    print(f"Total PL fetched: {len(links)}")
    ALL_ROWS = []
    MAX_WORKERS = 10
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(extract_data, page) for page in links]
        for future in as_completed(futures):
            result = future.result()
            if result:
                ALL_ROWS.extend(result)
    json_path = os.path.join(db.RESULT_PAGE, "litigations_details.json")
    excel_path = os.path.join(db.RESULT_PAGE, "litigations_details.xlsx")
    safe_rows = make_json_safe(ALL_ROWS)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(safe_rows, f, indent=2, ensure_ascii=False)
    litigations_details_json_to_excel(json_path, excel_path)
    print("Total saved:", len(ALL_ROWS))

