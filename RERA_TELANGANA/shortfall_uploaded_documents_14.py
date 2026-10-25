import re
import hashlib
import requests
from bson import ObjectId
from concurrent.futures import ThreadPoolExecutor, as_completed
from lxml import html
import zipfile
import numpy as np
import pandas as pd
import json
import os
from pymongo import MongoClient
import db_config_1 as db

# =========================
# MONGO CONNECTION
# =========================
def get_mongo_db():
    client = MongoClient("mongodb://localhost:27017/")
    return client[db.DB_NAME]

def get_uploaded_doc_collection():
    return get_mongo_db()["shortfall_uploaded_doc_table"]

def ensure_uploaded_doc_indexes():
    col = get_uploaded_doc_collection()
    col.create_index("doc_file_path", unique=True)

def get_links_collection():
    return get_mongo_db()["links"]

# =========================
# HELPERS (UNCHANGED LOGIC)
# =========================

def generate_hash(project_id, document_name):
    raw = f"{project_id}_{document_name}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]

def make_json_safe(obj):
    if isinstance(obj, list):
        return [make_json_safe(i) for i in obj]
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# =========================
# FILE PATH BUILDER
# =========================
def build_save_path(page, doc):
    project_id = doc["project_id"]
    if doc['upid'] == -1:
        pass
    project_name = db.clean_project_name(doc["project_name"])
    project_folder = "Shortfall Uploaded Documents"
    extension = doc["file_type"].split("/")[-1]
    hash_id = generate_hash(project_id, doc["document_name"])
    file_name = f"{project_name} - {hash_id}_{doc['upid']}.{extension}"
    full_dir = os.path.join(db.assets_path_second, project_folder)
    os.makedirs(full_dir, exist_ok=True)
    return os.path.join(full_dir, file_name)


def build_zip_save_path(page, doc):
    project_id = doc["project_id"]
    if doc['upid'] == -1:
        pass
    project_name = db.clean_project_name(doc["project_name"])
    project_folder = "Shortfall Uploaded Documents"
    extension = doc["file_type"].split("/")[-1]
    hash_id = generate_hash(project_id, doc["document_name"])
    file_name = f"{project_name} - {hash_id}_{doc['upid']}.zip"
    # full_dir = os.path.join(db.zip_assets_path, project_folder)
    # os.makedirs(full_dir, exist_ok=True)
    # return os.path.join(full_dir, file_name)


# def build_zip_save_path(page, doc):
#     project_id = doc["project_id"]
#     if doc['upid'] == -1:
#         pass
#     project_name = db.clean_project_name(doc["project_name"])
#     project_folder = "Shortfall Uploaded Documents"
#     extension = doc["file_type"].split("/")[-1]
#     hash_id = generate_hash(project_id, doc["document_name"])
#     file_name = f"{project_name} - {hash_id}_{doc['upid']}.zip"
#     full_dir = os.path.join(db.zip_assets_path, project_folder)
#     os.makedirs(full_dir, exist_ok=True)
#     return os.path.join(full_dir, file_name)

# =========================
# DOWNLOAD DOCUMENT
# =========================

# def download_document(doc, save_path, raw_zip_doc_path):
def download_document(doc, save_path):
    headers = {
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'RoleID': '1',
        'CurrentUserID': '0',
    }
    response = requests.get(
        f'https://rerait.telangana.gov.in/Preview/GetUserDocumentFileContent/{doc['upid']}/1',
        params=params,
        headers=headers,
        verify=False,
    )
    # print("save_path ::::::::::::::; ", save_path)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            f.write(response.content)
        # 3️⃣ Get only filename (important for inside zip)
        pdf_filename = os.path.basename(save_path)
        # 4️⃣ Create ZIP in separate folder
        # with zipfile.ZipFile(raw_zip_doc_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        #     zipf.write(save_path, arcname=pdf_filename)

        print(f"✔ {save_path}")
    else:
        response.raise_for_status()

# =========================
# HTML TABLE EXTRACTION
# =========================
def extract_uploaded_doc_table(html_content, project_id, project_url, file_path, project_name):
    tree = html.fromstring(html_content)
    # Get ALL document tables
    tables = tree.xpath("//div[@id='DivDocument']//table[.//th[contains(text(),'Document Name')]]")
    # We need SECOND table only
    if len(tables) < 2:
        return []
    shortfall_table = tables[1]
    records = []
    rows = shortfall_table.xpath(".//tr[td]")
    for row in rows:
        doc_name = row.xpath(".//td[1]//span[1]/text()")
        doc_name = doc_name[0].strip() if doc_name else "N/A"
        status = "N/A"
        if row.xpath(".//button[contains(@title,'View')]"):
            status = "View"
        elif row.xpath(".//label[contains(text(),'Not Uploaded')]"):
            status = "Not Uploaded"
        upid = row.xpath(".//input[starts-with(@name,'UPID_')]/@value")
        upid = upid[0] if upid else None
        file_type = row.xpath(".//input[starts-with(@name,'FileType_')]/@value")
        file_type = file_type[0] if file_type else None
        record = {
            "document_name": doc_name,
            "uploaded_document": status,
            "upid": upid,
            "file_type": file_type,
            "project_id": project_id,
            "project_url": project_url,
            "project_name": project_name,
            "file_path": file_path,
            "status": "pending"
        }
        records.append(record)
    return records

# =========================
# STEP 1: SCRAPE METADATA
# =========================
def scrape_shortfall_uploaded_documents(page):
    project_id = page["project_id"]
    id = page['SrNo']
    project_name = page["ProjectName"]
    pdp_path = page.get("pdp_path")
    if not pdp_path:
        print(f"❌ pdp_path missing for project: {project_id}")
        return None
    file_name = f"{project_id}_{id}.html"
    FILE_PATH = os.path.join("Z:", page["pdp_path"])
    FILE_PATH = pdp_path.replace("J:", "X:", 1)

    # file_name = f"{project_id}_{page['SrNo']}.html"
    # file_path = os.path.join(db.DATA_PAGESAVE, file_name)

    if not os.path.exists(FILE_PATH):
        return 0

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    records = extract_uploaded_doc_table(
        html_content,
        project_id,
        page["ViewDetails"],
        file_name,
        project_name
    )

    if records:
        get_uploaded_doc_collection().insert_many(records)

    return len(records)

# =========================
# STEP 2: DOWNLOAD FILES
# =========================
# def download_uploaded_documents():
#     collection = get_uploaded_doc_collection()
#     docs = list(collection.find({"status": "pending"}))
#
#     print(f"📥 Documents to download: {len(docs)}")
#
#     for doc in docs:
#         try:
#             # ✅ CASE: UPID = -1 → no file exists
#             if doc.get("upid") in (-1, None, "N/A", "-1"):
#                 collection.update_one(
#                     {"_id": doc["_id"]},
#                     {
#                         "$set": {
#                             "status": "completed",
#                             "doc_file_path": "N/A"
#                         }
#                     }
#                 )
#                 continue
#
#             page = {
#                 "project_id": doc["project_id"],
#                 "project_name": doc["project_name"]
#             }
#
#             raw_doc_path = build_save_path(page, doc)
#             doc_path = raw_doc_path.split("dv-bc_52935" + os.sep, 1)[-1]
#             downloaded_doc_path = "dv-bc_52935" + os.sep + doc_path
#             if os.path.exists(raw_doc_path):
#                 collection.update_one(
#                     {"_id": doc["_id"]},
#                     {"$set": {"status": "completed", "doc_file_path": downloaded_doc_path}}
#                 )
#                 continue
#             download_document(doc, raw_doc_path)
#             collection.update_one(
#                 {"_id": doc["_id"]},
#                 {"$set": {"status": "completed", "doc_file_path": downloaded_doc_path}}
#             )
#             print("✅ Downloaded:", raw_doc_path)
#
#         except Exception as e:
#             collection.update_one(
#                 {"_id": doc["_id"]},
#                 # {"$set": {"status": "failed", "error": str(e)}}
#                 {"$set": {"status": "failed"}}
#             )
#             print("❌ Failed:", e)


def download_uploaded_documents():
    collection = get_uploaded_doc_collection()
    docs = list(collection.find({"status": "pending"}))

    print(f"📥 Documents to download: {len(docs)}")
    # quit()
    for doc in docs:
        try:
            # ✅ CASE: No file exists
            if doc.get("upid") in (-1, None, "N/A", "-1"):
                collection.update_one(
                    {"_id": doc["_id"]},
                    {
                        "$set": {
                            "status": "completed",
                            "doc_file_path": "N/A",
                            # "zip_file_path": "N/A"
                        }
                    }
                )
                continue

            page = {
                "project_id": doc["project_id"],
                "project_name": doc["project_name"]
            }

            raw_doc_path = build_save_path(page, doc)
            # raw_zip_doc_path = build_zip_save_path(page, doc)

            # Build relative paths
            # doc_path = raw_doc_path.split("dv-bc_52935" + os.sep, 1)[-1]
            # zip_doc_path = raw_zip_doc_path.split("dv-bc_52935" + os.sep, 1)[-1]

            # downloaded_doc_path = "dv-bc_52935" + os.sep + doc_path
            # downloaded_zip_doc_path = "dv-bc_52935" + os.sep + zip_doc_path

            # ✅ If already exists
            # if os.path.exists(raw_doc_path) or os.path.exists(raw_zip_doc_path):
            if os.path.exists(raw_doc_path):
                update_fields = {"status": "completed"}

                if os.path.exists(raw_doc_path):
                    update_fields["doc_file_path"] = raw_doc_path

                # if os.path.exists(raw_zip_doc_path):
                #     update_fields["zip_file_path"] = downloaded_zip_doc_path

                collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": update_fields}
                )
                continue

            # ✅ Download if not exists
            # download_document(doc, raw_doc_path, raw_zip_doc_path)
            download_document(doc, raw_doc_path)

            update_fields = {"status": "completed"}

            if os.path.exists(raw_doc_path):
                update_fields["doc_file_path"] = raw_doc_path

            # if os.path.exists(raw_zip_doc_path):
            #     update_fields["zip_file_path"] = downloaded_zip_doc_path

            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": update_fields}
            )

            # print(f"✅ Downloaded: {raw_doc_path} ::: zip: {raw_zip_doc_path}")
            print(f"✅ Downloaded: {raw_doc_path}")

        except Exception as e:
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "failed"}}
            )
            print("❌ Failed:", e)


def download_single_document(doc):
    collection = get_uploaded_doc_collection()
    try:
        # CASE: no file
        if doc.get("upid") in (-1, None, "N/A", "-1"):
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "completed", "doc_file_path": "N/A"}}
            )
            return
        page = {
            "project_id": doc["project_id"],
            "project_name": doc["project_name"]
        }
        raw_doc_path = build_save_path(page, doc)
        # raw_zip_doc_path = build_zip_save_path(page, doc)
        # doc_path = raw_doc_path.split("dv-bc_52935" + os.sep, 1)[-1]
        # zip_doc_path = raw_zip_doc_path.split("dv-bc_52935" + os.sep, 1)[-1]
        # downloaded_doc_path = "dv-bc_52935" + os.sep + doc_path
        # downloaded_zip_doc_path = "dv-bc_52935" + os.sep + zip_doc_path
        if os.path.exists(raw_doc_path):
            update_fields = {"status": "completed"}
            if os.path.exists(raw_doc_path):
                update_fields["doc_file_path"] = raw_doc_path
            # if os.path.exists(raw_zip_doc_path):
            #     update_fields["zip_file_path"] = downloaded_zip_doc_path
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": update_fields}
            )
            return

        # if os.path.exists(raw_doc_path):
        #     collection.update_one(
        #         {"_id": doc["_id"]},
        #         {"$set": {"status": "completed", "doc_file_path": downloaded_doc_path}}
        #     )
        #     return
        download_document(doc, raw_doc_path)
        update_fields = {"status": "completed"}
        if os.path.exists(raw_doc_path):
            update_fields["doc_file_path"] = raw_doc_path
        # if os.path.exists(raw_zip_doc_path):
        #     update_fields["zip_file_path"] = downloaded_zip_doc_path
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": update_fields}
        )
        print(f"✅ Downloaded: {raw_doc_path}")

        # collection.update_one(
        #     {"_id": doc["_id"]},
        #     {"$set": {"status": "completed", "doc_file_path": downloaded_doc_path}}
        # )
        # print("✅ Downloaded:", raw_doc_path)
    except Exception as e:
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"status": "failed"}}
        )
        print("❌ Failed:", e)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    # # # ensure_uploaded_doc_indexes()
    # # # STEP 1: SCRAPE DOCUMENT METADATA
    # # links = list(get_links_collection().find({"status": "done"}))
    # # # links = list(get_links_collection().find({"status": "scraped"})
    # # #              .skip(2500)
    # # #              .limit(2500))
    # links = list(get_links_collection().find({"status": "done"}))
    # print(f"🔍 Pages found: {len(links)}")
    # # # quit()
    # with ThreadPoolExecutor(max_workers=10) as executor:
    #     futures = [executor.submit(scrape_shortfall_uploaded_documents, page) for page in links]
    #     for f in as_completed(futures):
    #         f.result()
    #
    # print("✅ Metadata extraction completed")
    # # STEP 2: DOWNLOAD FILES
    download_uploaded_documents()
    print("🎉 All tasks completed")

    # # -----------------------------
    # # STEP 2: DOWNLOAD FILES (THREADS)
    # # -----------------------------
    # download_uploaded_documents_threaded(max_workers=5)
    #
    # print("🎉 All tasks completed")

#
# # ##########################   Create Json and Excel file ##############################

# 🔹 Paths
JSON_PATH = os.path.join(db.RESULT_PAGE, "shortfall_uploaded_documents.json")

# 🔹 Mongo connection
client = MongoClient("mongodb://localhost:27017/")
db_mongo = client[db.DB_NAME]
collection = db_mongo["shortfall_uploaded_doc_table"]
# 🔹 Fetch data
data = list(collection.find({}))   # add filters if needed
print(len(data))

# 🔹 Convert ObjectId → string
for row in data:
    row["_id"] = str(row["_id"])

# 🔹 Save JSON
os.makedirs(db.RESULT_PAGE, exist_ok=True)
with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ JSON file created:", JSON_PATH)

excel_path = os.path.join(db.RESULT_PAGE, "shortfall_uploaded_documents.xlsx")

# 🔹 Load JSON
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# 🔹 Convert Mongo _id to string (safety)
for row in data:
    row.pop("_id", None)
    row.pop("status", None)

# 🔹 Define column order (optional but recommended)
columns = [
    "project_id",
    "project_url",
    "project_name",
    "document_name",
    "uploaded_document",
    "upid",
    "file_path",
    "doc_file_path",
    # "zip_file_path"
]

# 🔹 Create DataFrame
df = pd.DataFrame(data)

# 🔹 Reorder columns (only existing ones)
df = df[[col for col in columns if col in df.columns]]

df.replace(to_replace=["-", "", None, "NA"], value="N/A", inplace=True)
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



#
# ################################################################################################################
# import os
# import re
# import shutil
# import time
# from datetime import datetime
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from pymongo import MongoClient
# import db_config_1 as db
#
#
# # ==============================
# # Mongo Connection
# # ==============================
# client = MongoClient(
#     "mongodb://localhost:27017/",
#     maxPoolSize=50
# )
#
# database = client[db.DB_NAME]
# uploaded_collection = database["shortfall_uploaded_doc_table"]
#
#
# # ==============================
# # Utilities
# # ==============================
#
# def sanitize_folder_name(name):
#     name = re.sub(r'[\\/*?:"<>|]', '_', name)
#     name = re.sub(r'\s+', ' ', name)
#     return name.strip()
#
#
# def safe_copy(src, dst, retries=3):
#     for i in range(retries):
#         try:
#             shutil.copy2(src, dst)
#             return True
#         except PermissionError:
#             time.sleep(1)
#         except Exception as e:
#             print("Copy error:", e)
#             return False
#     return False
#
#
# # ==============================
# # Build File Index (FAST)
# # ==============================
#
# def build_file_index(root_folder):
#
#     file_index = {}
#
#     print("Scanning uploaded files...")
#
#     for root, dirs, files in os.walk(root_folder):
#         for file in files:
#             if file not in file_index:
#                 file_index[file] = os.path.join(root, file)
#
#     print("Indexed files:", len(file_index))
#
#     return file_index
#
#
# # ==============================
# # Thread Worker
# # ==============================
#
# def process_single_document(doc, base_assets_path, file_index):
#
#     project_id = doc.get("project_id")
#     project_name = sanitize_folder_name(doc.get("project_name", ""))
#
#     if not project_id or not project_name:
#         return
#
#     print("Processing:", project_id)
#
#     base_folder_name = f"{project_name} - {project_id}"
#     project_folder = os.path.join(base_assets_path, base_folder_name)
#
#     if not os.path.exists(project_folder):
#         print("Project folder not found:", project_id)
#         return
#
#     uploaded_folder = os.path.join(project_folder, "Shortfall_Uploaded_Documents")
#     os.makedirs(uploaded_folder, exist_ok=True)
#
#     update_fields = {}
#
#     doc_file_path = doc.get("doc_file_path")
#
#     # Skip empty paths
#     if not doc_file_path or doc_file_path.strip().upper() == "N/A":
#         print("No document for:", project_id)
#         return
#
#     filename = os.path.basename(doc_file_path)
#
#     # Fast lookup instead of os.walk
#     full_doc_path = file_index.get(filename)
#
#     if full_doc_path:
#
#         new_doc_path = os.path.join(uploaded_folder, filename)
#
#         if not os.path.exists(new_doc_path):
#             safe_copy(full_doc_path, new_doc_path)
#
#         update_fields["updated_doc_file_path"] = new_doc_path
#         update_fields["status"] = "done"
#
#     else:
#         print("File not found:", filename)
#
#     if update_fields:
#         uploaded_collection.update_one(
#             {"_id": doc["_id"]},
#             {"$set": update_fields}
#         )
#
#
# # ==============================
# # Main Process
# # ==============================
#
# def process_uploaded_documents():
#
#     # current_month_year = datetime.now().strftime("%m-%Y")
#     current_month_year = "02-2026"
#
#     base_assets_path = f"Z:\\dv-bc_52935\\{current_month_year}\\Assets"
#
#     uploaded_root = f"Z:\\dv-bc_52935\\{current_month_year}\\Projects\\Assets\\Shortfall Uploaded Documents"
#
#     # Build file index once
#     file_index = build_file_index(uploaded_root)
#
#     docs = uploaded_collection.find(
#         {"status": "completed"},
#         no_cursor_timeout=True
#     )
#
#     docs = list(docs)
#
#     print("Total docs:", len(docs))
#
#     MAX_THREADS = 10
#
#     with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
#
#         futures = [
#             executor.submit(
#                 process_single_document,
#                 doc,
#                 base_assets_path,
#                 file_index
#             )
#             for doc in docs
#         ]
#
#         for future in as_completed(futures):
#             try:
#                 future.result()
#             except Exception as e:
#                 print("Thread error:", e)
#
#     print("All uploaded documents processed successfully.")
#
#
# # ==============================
# # RUN
# # ==============================
#
# if __name__ == "__main__":
#     process_uploaded_documents()
#
# # import os
# # import re
# # import shutil
# # import time
# # from datetime import datetime
# # from pymongo import MongoClient
# # import db_config_1 as db
# #
# #
# # # ==============================
# # # Mongo Connection
# # # ==============================
# # client = MongoClient("mongodb://localhost:27017/")
# # database = client[db.DB_NAME]
# #
# # uploaded_collection = database["shortfall_uploaded_doc_table"]
# #
# #
# # # ==============================
# # # Utilities
# # # ==============================
# #
# # def sanitize_folder_name(name):
# #     name = re.sub(r'[\\/*?:"<>|]', '_', name)
# #     name = re.sub(r'\s+', ' ', name)
# #     return name.strip()
# #
# #
# # def safe_copy(src, dst, retries=3):
# #     for i in range(retries):
# #         try:
# #             shutil.copy2(src, dst)
# #             return True
# #         except PermissionError:
# #             time.sleep(1)
# #         except Exception as e:
# #             print("Copy error:", e)
# #             return False
# #     return False
# #
# #
# # def find_file_recursively(root_folder, filename):
# #     """
# #     Search filename inside all subfolders (Batch folders)
# #     """
# #     for root, dirs, files in os.walk(root_folder):
# #         if filename in files:
# #             return os.path.join(root, filename)
# #     return None
# #
# #
# # # ==============================
# # # Process Uploaded Documents
# # # ==============================
# #
# # def process_uploaded_documents():
# #     # current_month_year = datetime.now().strftime("%m-%Y")
# #     current_month_year = '02-2026'
# #     # 🔹 Destination base folder (already created earlier)
# #     base_assets_path = f"Z:\\dv-bc_52935\\{current_month_year}\\Assets"
# #     # 🔹 Source folder where batch folders exist
# #     uploaded_root = f"Z:\\dv-bc_52935\\{current_month_year}\\Projects\\Assets\\Shortfall Uploaded Documents"
# #
# #     docs = uploaded_collection.find({"status": "completed"} ,no_cursor_timeout=True)
# #     for doc in docs:
# #         project_id = doc.get("project_id")
# #         project_name = sanitize_folder_name(doc.get("project_name", ""))
# #         if not project_id or not project_name:
# #             continue
# #         print("Processing Uploaded Docs for:", project_id)
# #         # 🔹 Project folder (already created by previous script)
# #         base_folder_name = f"{project_name} - {project_id}"
# #         project_folder = os.path.join(base_assets_path, base_folder_name)
# #         if not os.path.exists(project_folder):
# #             print("Project folder not found, skipping:", project_id)
# #             continue
# #         uploaded_folder = os.path.join(project_folder, "Shortfall_Uploaded_Documents")
# #         os.makedirs(uploaded_folder, exist_ok=True)
# #         update_fields = {}
# #         # ==========================================
# #         # 1️⃣ PDF File Search & Copy
# #         # ==========================================
# #         doc_file_path = doc.get("doc_file_path")
# #         # 🚫 Skip invalid or empty paths
# #         if not doc_file_path or doc_file_path.strip().upper() == "N/A":
# #             print("No document for project:", project_id)
# #             continue
# #         if doc_file_path:
# #             filename = os.path.basename(doc_file_path)
# #             # 🔍 Search inside all batch folders
# #             full_doc_path = find_file_recursively(uploaded_root, filename)
# #             if full_doc_path:
# #                 print("Found file at:", full_doc_path)
# #                 new_doc_path = os.path.join(uploaded_folder, filename)
# #                 if not os.path.exists(new_doc_path):
# #                     safe_copy(full_doc_path, new_doc_path)
# #                 update_fields["updated_doc_file_path"] = new_doc_path
# #                 update_fields["status"] = 'done'
# #             else:
# #                 print("File not found in any batch folder:", filename)
# #         # ==========================================
# #         # Update Mongo
# #         # ==========================================
# #         if update_fields:
# #             uploaded_collection.update_one(
# #                 {"_id": doc["_id"]},
# #                 {"$set": update_fields}
# #             )
# #             print("Updated Mongo for:", project_id, "\n")
# #         # quit()
# #     print("All uploaded documents processed successfully.")
# #
# # # ==============================
# # # RUN
# # # ==============================
# # process_uploaded_documents()
