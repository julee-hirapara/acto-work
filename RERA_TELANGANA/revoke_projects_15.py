import os
import re
import json
import hashlib
import requests
import pandas as pd
from parsel import Selector
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient
import db_config_1 as db
import numpy as np
import zipfile

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def normalize_name(name):
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'[^a-z0-9 ]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def generate_hash(*args):
    raw = "|".join([str(a) for a in args if a])
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def clean_project_url(url):
    """
    Remove duplicated domain:
    https://rerait.telangana.gov.inhttps://rera.telangana.gov.in/...
    """
    if not url:
        return "N/A"

    bad_prefix = "https://rerait.telangana.gov.in"
    if url.startswith(bad_prefix):
        return url.replace(bad_prefix, "", 1)

    return url


# --------------------------------------------------
# MONGO: LOAD PENDING PROJECTS
# --------------------------------------------------

def load_pending_projects():
    client = MongoClient("mongodb://localhost:27017/")
    col = client[db.DB_NAME]["links"]

    project_map = {}

    cursor = col.find(
        {"status": "pending"},
        {"project_id": 1, "ProjectName": 1, "ViewDetails": 1}
    )

    for doc in cursor:
        key = normalize_name(doc.get("ProjectName"))
        project_map[key] = {
            "project_id": doc.get("project_id", "N/A"),
            "project_url": clean_project_url(doc.get("ViewDetails"))
        }

    print(f"🔗 Loaded pending projects: {len(project_map)}")
    return project_map


# --------------------------------------------------
# FILE PATH
# --------------------------------------------------

def build_pdf_path(promoter, project, sr_no, pdf_name):
    folder = "Projects_Agents - Registration Revoked"
    hash_id = generate_hash(project, promoter, sr_no, pdf_name)
    project = db.clean_project_name(project)
    filename = f"{project} - {hash_id}_{pdf_name}"
    path = os.path.join(db.assets_path, folder)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, filename)


def build_zip_pdf_path(promoter, project, sr_no, pdf_name):
    folder = "Projects_Agents - Registration Revoked"
    hash_id = generate_hash(project, promoter, sr_no, pdf_name)
    project = db.clean_project_name(project)
    filename = f"{project} - {hash_id}_{pdf_name}"
    path = os.path.join(db.zip_assets_path, folder)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, filename)
# --------------------------------------------------
# DOWNLOAD PDF
# --------------------------------------------------
def download_pdf(pdf_name):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': 'https://rera.telangana.gov.in/Home/Revoked',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    }
    url = "https://rera.telangana.gov.in/Home/ShowPDFFile3"
    params = {"pdffilename": pdf_name}

    r = requests.get(url, headers=headers, params=params, verify=False)
    if r.status_code == 200:
        return r.content
    return None
# def download_pdf(pdf_name, save_path):
#     headers = {
#         'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#         'accept-language': 'en-US,en;q=0.9',
#         'cache-control': 'max-age=0',
#         'priority': 'u=0, i',
#         'referer': 'https://rera.telangana.gov.in/Home/Revoked',
#         'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'document',
#         'sec-fetch-mode': 'navigate',
#         'sec-fetch-site': 'same-origin',
#         'sec-fetch-user': '?1',
#         'upgrade-insecure-requests': '1',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
#     }
#     url = "https://rera.telangana.gov.in/Home/ShowPDFFile3"
#     params = {"pdffilename": pdf_name}
#
#     r = requests.get(url, headers=headers, params=params, verify=False)
#     if r.status_code == 200:
#         with open(save_path, "wb") as f:
#             f.write(r.content)


# --------------------------------------------------
# MAIN SCRAPER
# --------------------------------------------------
def save_to_mongo(data):
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    # Database & collection
    db_mongo = client[db.DB_NAME]
    collection = db_mongo["revoked_projects"]
    if not data:
        print("⚠ No data to insert")
        return
    # Insert documents
    result = collection.insert_many(data)
    print(f"✅ Inserted {len(result.inserted_ids)} records into MongoDB")


def fetch_revoked_projects():
    project_lookup = load_pending_projects()
    revoke_file = f"{db.REVOKED_PAGESAVE}\\revoke.html"
    response = requests.get(
        "https://rera.telangana.gov.in/Home/Revoked",
        verify=False
    )
    if response.status_code == 200:
        with open(revoke_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"✔ Saved project page → revoke.html")


    sel = Selector(text=response.text)
    rows = sel.xpath('//table[@id="pdflistgrid"]/tbody/tr')

    data = []

    sr_no = project = promoter = None

    for row in rows:
        rowspan = row.xpath('./td[@rowspan]/text()').getall()
        if len(rowspan) >= 3:
            sr_no = rowspan[0].strip()
            project = rowspan[1].strip()
            promoter = rowspan[2].strip()

        pdf_link = row.xpath('.//a/@href').get()
        if not pdf_link:
            continue

        pdf_name = parse_qs(urlparse(pdf_link).query).get("pdffilename", [None])[0]
        if not pdf_name:
            continue

        doc_name = row.xpath('.//a/ancestor::td/preceding-sibling::td[1]/text()').get()

        normalized = normalize_name(project)
        project_meta = project_lookup.get(normalized, {})

        pdf_path = build_pdf_path(promoter, project, sr_no, pdf_name)
        # doc_pdf_path = pdf_path.split("dv-bc_52935" + os.sep, 1)[-1]
        # document_pdf_path = "dv-bc_52935" + os.sep + doc_pdf_path
        # download_pdf(pdf_name, pdf_path)
        pdf_content = download_pdf(pdf_name)

        if not pdf_content:
            continue

        # 🔹 Save normal PDF
        pdf_path = build_pdf_path(promoter, project, sr_no, pdf_name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_content)
        # # 🔹 Create ZIP file for THIS PDF only
        # zip_pdf_path = build_zip_pdf_path(promoter, project, sr_no, pdf_name)
        # # Change extension to .zip
        # zip_pdf_path = os.path.splitext(zip_pdf_path)[0] + ".zip"
        # with zipfile.ZipFile(zip_pdf_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        #     zipf.writestr(os.path.basename(pdf_path), pdf_content)

        data.append({
            "project_id": project_meta.get("project_id", "N/A"),
            "project_url": project_meta.get("project_url", "N/A"),
            "Project Name": project,
            "Promoter Name": promoter,
            "Document Name": doc_name.strip() if doc_name else "N/A",
            "PDF URL": clean_project_url("https://rera.telangana.gov.in" + pdf_link),
            "file_path": revoke_file,
            "pdf_file_path": pdf_path
            # "pdf_zip_file_path": zip_pdf_path
        })
    # --------------------------------------------------
    # SAVE OUTPUTS
    # --------------------------------------------------

    json_path = os.path.join(db.RESULT_PAGE, "rera_telangana_revoked.json")
    excel_path = os.path.join(db.RESULT_PAGE, "rera_telangana_revoked.xlsx")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    df = pd.DataFrame(data)
    df.replace("", "N/A", inplace=True)
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
    # df.to_excel(excel_path, index=False)
    with pd.ExcelWriter(
            excel_path,
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_urls": False}}
    ) as writer:
        df.to_excel(writer, index=False)
    # df.to_excel(excel_path, index=False)
    save_to_mongo(data)
    print(f"✅ Revoked JSON saved: {json_path}")
    print(f"✅ Revoked Excel saved: {excel_path}")
    print(f"📄 Total records: {len(data)}")


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    fetch_revoked_projects()
