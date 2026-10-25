from concurrent.futures import ThreadPoolExecutor, as_completed
from lxml import html
from bson import ObjectId
import numpy as np
import json
import pandas as pd
import os
import db_config_1 as db


def extract_project_professional_info(html_content, project_id, project_url, project_name, file_name):
    tree = html.fromstring(html_content)
    table = tree.xpath("//div[@id='DivProfessional']//table[.//th[contains(text(),'Professional Name')]]")
    if not table:
        print("❌ professional Details table not found")
        return []
    table = table[0]
    # Extract headers
    headers = [th.text_content().strip() for th in table.xpath(".//tr[1]/th")]
    project_professional_data = []
    # Extract all data rows
    rows = table.xpath(".//tr[td]")
    for row in rows:
        values = [td.text_content().strip() or "N/A" for td in row.xpath("./td")]
        record = dict(zip(headers, values))
        # Add meta info
        record["project_id"] = project_id
        record["project_url"] = project_url
        record["project_name"] = project_name
        record["file_path"] = file_name
        project_professional_data.append(record)
    print("project_professional_data ::::::::::::::::: ", project_professional_data)
    return project_professional_data


def get_mongo_collection():
    db_conn = db.get_db_connection()
    return db_conn["project_professional_info"]


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
    FILE_PATH = os.path.join("J:", page["pdp_path"])
    FILE_PATH = pdp_path.replace("J:", "X:", 1)

    # FILE_PATH = f"{db.DATA_PAGESAVE}\\{file_name}"
    if not os.path.exists(FILE_PATH):
        return None
    with open(FILE_PATH, "r", encoding="UTF-8") as f:
        html_content = f.read()
    project_professional_data = extract_project_professional_info(html_content, project_id, project_url, project_name,
                                                                  file_name)
    if project_professional_data:
        collection = get_mongo_collection()
        collection.insert_many(make_json_safe(project_professional_data))
        print(f"✅ Inserted {len(project_professional_data)} plot records for project {project_id}")

    return project_professional_data


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


def project_professional_info(json_path, excel_path):
    # 🔹 Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 🔹 Convert Mongo _id to string (safety)
    for row in data:
        row.pop("_id", None)
        # row.pop("project_name", None)

    # 🔹 Define column order (optional but recommended)
    columns = [
        "project_id",
        "project_url",
        "project_name",
        "Professional Name",
        "TelanganaRERA Certificate No.",
        "Professional Type",
        "file_path",
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
    all_plot_data = []
    MAX_WORKERS = 10
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(extract_data, page) for page in links]
        for future in as_completed(futures):
            result = future.result()
            if not result:
                continue
            if result:
                all_plot_data.extend(result)
    json_path = os.path.join(db.RESULT_PAGE, "project_professional_info.json")
    excel_path = os.path.join(db.RESULT_PAGE, "project_professional_info.xlsx")
    safe_rows = make_json_safe(all_plot_data)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(safe_rows, f, indent=2, ensure_ascii=False)
    print("Total saved:", len(all_plot_data))
    project_professional_info(json_path, excel_path)
