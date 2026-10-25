import json
import db_config_1 as db
import os
from parsel import Selector
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from bson import ObjectId
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("✅ Script started")

def get_mongo_collection():
    db_conn = db.get_db_connection()                          # database name
    collection = db_conn["promoter_experience"]                 # collection name
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


def extract_promoter_experience(sel, id, project_url, project_name, project_id):
    experience_data = []
    table = sel.xpath(
        '//div[@id="DivExp"]//table[contains(@class,"grid-table")]'
    )
    if not table:
        return experience_data
    table = table[0]
    # headers
    headers = [
        th.xpath("normalize-space(.)").get()
        for th in table.xpath('.//thead/tr[1]/th')
    ]
    # rows
    for tr in table.xpath('.//tbody/tr'):
        values = [
            td.xpath("normalize-space(.)").get() or None
            for td in tr.xpath('./td')
        ]
        row_dict = dict(zip(headers, values))
        # ✅ ADD ID TO EACH DICT
        row_dict["ProjectRegID"] = id
        row_dict["project_id"] = project_id
        row_dict["project_name"] = project_name
        row_dict["project_url"] = project_url
        row_dict["file_name"] = f"{project_id}_{id}.html"

        experience_data.append(row_dict)
    # print("experience_data ::::::::::::::: ", experience_data)
    return experience_data


def extract_data(page):
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

    # FILE_PATH = f"{db.DATA_PAGESAVE}\\{project_id}_{id}.html"
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding='UTF-8') as f:
            html_content = f.read()
    sel = Selector(html_content)
    final_result = extract_promoter_experience(sel, id, project_url, project_name, project_id)
    # ✅ INSERT INTO MONGODB
    if final_result:
        collection = get_mongo_collection()
        collection.insert_many(final_result)
        print(f"✅ Inserted {len(final_result)} records for project {id}")
    return final_result


def generate_promoter_past_experience_excel_from_json(json_path, excel_path):
    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Flatten list of lists
    rows = []
    for group in data:
        for record in group:
            record.pop("_id", None)   # remove MongoDB _id
            rows.append(record)

    if not rows:
        print("❌ No data found")
        return

    # Create DataFrame
    df = pd.DataFrame(rows)

    if "Sr.No." in df.columns:
        df["Sr.No."] = pd.to_numeric(df["Sr.No."], errors="ignore")

    # Optional: Sort data
    sort_cols = [c for c in ["ProjectRegID", "Sr.No."] if c in df.columns]
    if sort_cols:
        df.sort_values(by=sort_cols, inplace=True)

    # Optional: Column order
    preferred_order = [
        "Sr.No.",
        "Project Name",
        "Type of Project",
        "Others",
        "Land Area(In Sq mtrs)",
        "Address",
        "CTS Number",
        "Number of Buildings/Plot",
        "Number of Apartments",
        "Original Proposed Date of Completion",
        "Actual Date of Completion",
        "project_id",
        "project_name",
        "project_url",
    ]

    final_columns = [c for c in preferred_order if c in df.columns]
    remaining_columns = [c for c in df.columns if c not in final_columns]
    df = df[final_columns + remaining_columns]
    df.replace(to_replace=["-", "", None, "NA"], value="N/A", inplace=True)
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
    print(f"✅ Excel created successfully: {excel_path}")


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
                ALL_ROWS.append(result)
    ALL_ROWS = make_json_safe(ALL_ROWS)
    json_path = os.path.join(db.RESULT_PAGE, "promoter_past_experience.json")
    excel_path = os.path.join(db.RESULT_PAGE, "promoter_past_experience.xlsx")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ALL_ROWS, f, indent=2, ensure_ascii=False)
    print("Total saved:", len(ALL_ROWS))
    generate_promoter_past_experience_excel_from_json(json_path, excel_path)
    print(f"✅ Total saved: {len(ALL_ROWS)}")