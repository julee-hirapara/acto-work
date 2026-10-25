import db_config_1 as db
from concurrent.futures import ThreadPoolExecutor, as_completed
from lxml import html
import os
import json
import re
import pandas as pd
import numpy as np
from bson import ObjectId
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("✅ Script started")


def get_mongo_collection():
    db_conn = db.get_db_connection()                         # database name
    collection = db_conn["promoter_land_owner_investor_details"]                 # collection name
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


def promoter_land_details(html_text, project_name, project_url, project_id, file_name):
    tree = html.fromstring(html_text)
    tables = tree.xpath('.//div[contains(@id, "DivCoPromoter")]//table')
    if not tables:
        return []
    table = tables[0]
    results = []
    rows = table.xpath('.//tr')
    current_headers = []
    for row in rows:
        ths = row.xpath('.//th/text()')
        tds = row.xpath('.//td/text()')
        # Header row → update headers dynamically
        if ths:
            current_headers = [h.strip() for h in ths]
        # Data row → map values to last headers
        elif tds and current_headers:
            values = [v.strip() for v in tds]
            row_data = dict(zip(current_headers, values))
            # 🔹 Add extra dynamic fields
            row_data["project_id"] = project_id
            row_data["project_name"] = project_name
            row_data["project_url"] = project_url
            row_data["file_path"] = file_name
            results.append(row_data)
    # print("results :::::::::::::: ", results)
    return results

def extract_data(page):
    id = page['SrNo']
    project_name = page['ProjectName']
    project_url = page['ViewDetails']
    project_id = page['project_id']
    file_name = f"{project_id}_{id}.html"
    pdp_path = page.get("pdp_path")
    if not pdp_path:
        print(f"❌ pdp_path missing for project: {project_id}")
        return None
    # FILE_PATH = f"{db.DATA_PAGESAVE}\\{file_name}"
    FILE_PATH = os.path.join("J:", page["pdp_path"])
    FILE_PATH = pdp_path.replace("J:", "X:", 1)

    if not os.path.exists(FILE_PATH):
        return None
    with open(FILE_PATH, "r", encoding="UTF-8") as f:
        html_content = f.read()
    land_details = promoter_land_details(html_content, project_name, project_url, project_id, file_name)
    if not land_details:
        return None
    collection = get_mongo_collection()
    # ✅ SIMPLE INSERT — NO UNIQUE CHECK
    collection.insert_many(land_details)
    print(f"Inserted {len(land_details)} land owner or investor for project:", id)
    return land_details


def promoter_land_owner_investor_json_to_excel(json_path, excel_path):
    """
    Convert promoter/land owner/investor JSON data into a cleaned Excel file.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for row in data:
        row.pop("_id", None)
        row.pop("project_name", None)
    df = pd.DataFrame(data)
    preferred_columns = [
        "project_id",
        "project_url",
        "Project Name",
        "Promoter Name",
        "Promoter(Land Owner/ Investor) Type",
        "Type of Agreement/ Arrangement",
        "Office Number",
        "Other Details",
        "file_path"
    ]
    existing_cols = [c for c in preferred_columns if c in df.columns]
    remaining_cols = [c for c in df.columns if c not in existing_cols]
    df = df[existing_cols + remaining_cols]
    # --------------------------------------------------
    # CLEANING FUNCTION
    # --------------------------------------------------
    def clean_junk(value):
        if not isinstance(value, str):
            return value
        # Remove extra spaces, newlines, tabs
        value = re.sub(r"\s+", " ", value).strip()
        # Replace junk-only values
        if not value or re.fullmatch(r"[.\-,`]+", value):
            return "N/A"
        return value

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(clean_junk)
    df = df.replace(r'\s+', ' ', regex=True)
    # 🔹 Replace placeholder-like strings (including NA variants)
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
            excel_path,
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_urls": False}}
    ) as writer:
        df.to_excel(writer, index=False)
    print("✅ Excel created successfully")
    print("📁 Output:", excel_path)
    print("📊 Total records:", len(df))
    # df.replace(
    #     to_replace=[
    #         r'^\s*--\s*$',
    #         r'^\s*-\s*$',
    #         r'^\s*\.\s*$',
    #         r'^\s*$',
    #         r'^\s*NA\s*$',
    #         r'^\s*N/A\s*$',
    #         r'^\s*_\s*$'
    #     ],
    #     value="N/A",
    #     regex=True,
    #     inplace=True
    # )
    # # 🔹 Handle real nulls
    # df.replace({None: np.nan}, inplace=True)
    # df.fillna("N/A", inplace=True)
    # with pd.ExcelWriter(
    #         excel_path,
    #         engine="xlsxwriter",
    #         engine_kwargs={"options": {"strings_to_urls": False}}
    # ) as writer:
    #     df.to_excel(writer, index=False)
    # print("✅ Excel file created successfully:", excel_path)



if __name__ == "__main__":
    # Fetch scraped links from Mongo
    links_col = db.get_mongo_links_collection()
    links = list(links_col.find({"status": "done"}))
    # links = list(links_col.find({"status": "done"}).limit(10))
    print(f"Total PL fetched: {len(links)}")
    ALL_ROWS = []
    MAX_WORKERS = 10
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(extract_data, page) for page in links]
        for future in as_completed(futures):
            result = future.result()
            if result:
                ALL_ROWS.extend(result)
    json_path = os.path.join(db.RESULT_PAGE, "promoter_land_owner_investor_details.json")
    excel_path = os.path.join(db.RESULT_PAGE, "promoter_land_owner_investor_details.xlsx")
    safe_rows = make_json_safe(ALL_ROWS)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(safe_rows, f, indent=2, ensure_ascii=False)
    promoter_land_owner_investor_json_to_excel(json_path, excel_path)
    print("Total saved:", len(ALL_ROWS))


# J:\act-jnssnd-8045-property-agent-data-collection-from-rera-telangana-once-off\Projects\10-08-2026\Pagesaves\data\0a6b6ddcae43b361_6396.html