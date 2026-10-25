import db_config_1 as db
import os
from parsel import Selector
from concurrent.futures import ThreadPoolExecutor, as_completed
from bson import ObjectId
import numpy as np
import json
import pandas as pd


def extract_amenities(sel, project_id, project_name, project_url, file_name):
    result = {}
    panels = sel.xpath('//div[@id="DivAmenities"]//div[contains(@class,"x_panel")]')

    for panel in panels:
        # 🔹 Section name (Project Details / Development Work)
        section_name = panel.xpath('.//div[@class="x_title"]/h2/text()').get()
        section_name = section_name.strip() if section_name else "Unknown Section"
        table = panel.xpath('.//table')
        if not table:
            continue

        # 🔹 Extract headers
        headers = table.xpath('.//tr[1]/th/text()').getall()
        headers = [h.strip() for h in headers if h.strip()]
        rows_data = []

        # 🔹 Extract rows
        rows = table.xpath('.//tr[position() > 1 and td]')
        for row in rows:
            cells = row.xpath('./td')
            row_dict = {}

            for i, header in enumerate(headers):
                value = cells[i].xpath('normalize-space(.)').get()
                # Clean name column (remove extra text like ":")
                if header.lower().startswith("name") or "amenities" in header.lower():
                    value = value.split(":")[0].strip()
                row_dict[header] = value

            # 🔹 Add project metadata
            row_dict.update({
                "project_id": project_id,
                "project_name": project_name,
                "project_url": project_url,
                "file_name": file_name
            })
            rows_data.append(row_dict)
        result[section_name] = rows_data
    # print("result :::::::::::; ", result)
    return result


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
    FILE_PATH = os.path.join("J:", page["pdp_path"])
    FILE_PATH = pdp_path.replace("J:", "X:", 1)

    if not os.path.exists(FILE_PATH):
        return None
    # FILE_PATH = f"{db.DATA_PAGESAVE}\\{file_name}"
    with open(FILE_PATH, "r", encoding="UTF-8") as f:
        html_content = f.read()
    sel = Selector(html_content)
    data = extract_amenities(sel, project_id, project_name, project_url, file_name)
    if not data:
        return None
    return {
        "project_details": data.get("Project Details", []),
        "development_work": data.get("Development Work", [])
    }


def get_mongo_collections():
    db_conn = db.get_db_connection()
    return {
        "project_details": db_conn["project_details"],
        "development_work": db_conn["development_work"]
    }


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


def project_details_development_work_json_to_excel(json_path, excel_path, column_order):
    """
    Convert a JSON file into a cleaned Excel file with ordered columns.
    Args:
        json_path (str): Path to input JSON file
        excel_path (str): Path to output Excel file
        column_order (list): Preferred column order
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for row in data:
        row.pop("_id", None)
        row.pop("project_name", None)
    df = pd.DataFrame(data)
    existing_cols = [c for c in column_order if c in df.columns]
    df = df[existing_cols]

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
    print(f"✅ Excel created: {excel_path}")


if __name__ == "__main__":
    # Fetch scraped links from Mongo
    links_col = db.get_mongo_links_collection()
    links = list(links_col.find({"status": "done"}))
    # links = list(links_col.find({"status": "done"}).limit(10))
    print(f"Total PL fetched: {len(links)}")
    collections = get_mongo_collections()
    ALL_PROJECT_DETAILS = []
    ALL_DEVELOPMENT_WORK = []
    MAX_WORKERS = 10
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(extract_data, page) for page in links]
        for future in as_completed(futures):
            result = future.result()
            if not result:
                continue
            if result:
                ALL_PROJECT_DETAILS.extend(result["project_details"])
                ALL_DEVELOPMENT_WORK.extend(result["development_work"])
    if ALL_PROJECT_DETAILS:
        collections["project_details"].insert_many(ALL_PROJECT_DETAILS)
        print("✅ Inserted Project Details:", len(ALL_PROJECT_DETAILS))
    if ALL_DEVELOPMENT_WORK:
        collections["development_work"].insert_many(ALL_DEVELOPMENT_WORK)
        print("✅ Inserted Development Work:", len(ALL_DEVELOPMENT_WORK))

    project_details_path = os.path.join(db.RESULT_PAGE, "project_details.json")
    project_details_excel_path = os.path.join(db.RESULT_PAGE, "project_details.xlsx")
    development_work_path = os.path.join(db.RESULT_PAGE, "development_work.json")
    development_work_excel_path = os.path.join(db.RESULT_PAGE, "development_work.xlsx")
    with open(project_details_path, "w", encoding="utf-8") as f:
        json.dump(make_json_safe(ALL_PROJECT_DETAILS), f, indent=2, ensure_ascii=False)
    project_details_columns = [
        "project_id",
        "project_url",
        "Name",
        "Proposed",
        "Booked",
        "WorkDone(In %)",
        "file_name"
    ]
    project_details_development_work_json_to_excel(project_details_path, project_details_excel_path,
                                                   project_details_columns)

    with open(development_work_path, "w", encoding="utf-8") as f:
        json.dump(make_json_safe(ALL_DEVELOPMENT_WORK), f, indent=2, ensure_ascii=False)
    development_work_columns = [
        "project_id",
        "project_url",
        "Common areas And Facilities, Amenities",
        "Available",
        "Percent",
        "Details",
        "file_name"
    ]
    project_details_development_work_json_to_excel(development_work_path, development_work_excel_path,
                                                   development_work_columns)
    print("Project Details saved:", len(ALL_PROJECT_DETAILS))
    print("Development Work saved:", len(ALL_DEVELOPMENT_WORK))