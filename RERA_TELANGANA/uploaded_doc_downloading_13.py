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
    return get_mongo_db()["uploaded_doc_table"]

def ensure_uploaded_doc_indexes():
    col = get_uploaded_doc_collection()
    col.create_index(
        [("doc_file_path", 1)],
        unique=True,
        partialFilterExpression={
            "doc_file_path": {"$exists": True}
        }
    )
    # col.create_index("doc_file_path", unique=True)

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
    project_folder = "Uploaded Documents"
    extension = doc["file_type"].split("/")[-1]
    hash_id = generate_hash(project_id, doc["document_name"])
    file_name = f"{project_name} - {hash_id}_{doc['upid']}.{extension}"
    full_dir = os.path.join(db.assets_path, project_folder)
    os.makedirs(full_dir, exist_ok=True)
    return os.path.join(full_dir, file_name)


def build_zip_save_path(page, doc):
    project_id = doc["project_id"]
    if doc['upid'] == -1:
        pass
    project_name = db.clean_project_name(doc["project_name"])
    project_folder = "Uploaded Documents"
    extension = doc["file_type"].split("/")[-1]
    hash_id = generate_hash(project_id, doc["document_name"])
    file_name = f"{project_name} - {hash_id}_{doc['upid']}.zip"
    # full_dir = os.path.join(db.zip_assets_path, project_folder)
    # os.makedirs(full_dir, exist_ok=True)
    # return os.path.join(full_dir, file_name)



# =========================
# DOWNLOAD DOCUMENT
# =========================
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
    table = tree.xpath("//div[@id='DivDocument']//table[.//th[contains(text(),'Document Name')]]")
    if not table:
        print("❌ Document Name table not found")
        return []
    table = table[0]
    uploaded_doc_table = []

    # iterate over data rows
    rows = table.xpath(".//tr[td]")
    for row in rows:
        # Document name
        doc_name = row.xpath(".//td[1]//span[1]/text()")
        doc_name = doc_name[0].strip() if doc_name else "N/A"
        uploaded_doc = row.xpath(".//td[2]//text()")
        uploaded_doc = uploaded_doc[0].strip() if uploaded_doc else "N/A"

        status = "N/A"
        doc_id = "N/A"

        view_btn = row.xpath(".//button[contains(@title,'View')]")
        if view_btn:
            status = "View"
            # status = row.xpath(".//button[contains(@title, 'View')]/text()").get().strip()
            doc_id = row.xpath(".//input[@id='Doc_ID']/@value")
            doc_id = doc_id[0] if doc_id else "N/A"
        else:
            if row.xpath(".//label[contains(text(),'Not Uploaded')]"):
                # status = row.xpath(".//label[contains(@for, 'Not_Uploaded')]/text()").get().strip()
                status = "Not Uploaded"
        # ID / UPID
        upid = row.xpath(".//input[starts-with(@name,'UPID_')]/@value")
        upid = upid[0] if upid else None

        # File type
        file_type = row.xpath(".//input[starts-with(@name,'FileType_')]/@value")
        file_type = file_type[0] if file_type else None

        # Doc type (PDF)
        doc_type = row.xpath(".//input[starts-with(@name,'DocType_')]/@value")
        doc_type = doc_type[0] if doc_type else None

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
        uploaded_doc_table.append(record)
    return uploaded_doc_table

# =========================
# STEP 1: SCRAPE METADATA
# =========================
def scrape_uploaded_documents(page):
    project_id = page["project_id"]
    id = page['SrNo']
    project_name = page["ProjectName"]
    pdp_path = page.get("pdp_path")
    if not pdp_path:
        print(f"❌ pdp_path missing for project: {project_id}")
        return None
    file_name = f"{project_id}_{id}.html"
    # FILE_PATH = os.path.join("X:\\", page["pdp_path"])
    FILE_PATH =page["pdp_path"]
    # file_name = f"{project_id}_{page['SrNo']}.html"
    # file_path = os.path.join(db.DATA_PAGESAVE, file_name)
    FILE_PATH = FILE_PATH.replace("J:", "X:", 1)

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
    # records = [r for r in records if r.get("doc_file_path")]

    # if records:
    #     get_uploaded_doc_collection().insert_many(records, ordered=False)
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
                            "zip_file_path": "N/A"
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
            return

        # if os.path.exists(raw_doc_path):
        #     collection.update_one(
        #         {"_id": doc["_id"]},
        #         {"$set": {"status": "completed", "doc_file_path": downloaded_doc_path}}
        #     )
        #     return
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
        # print(f"✅ Downloaded: {raw_doc_path} ::: zip file path: {raw_zip_doc_path}")
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

def download_uploaded_documents_threaded(max_workers=10):
    collection = get_uploaded_doc_collection()
    docs = list(collection.find({"status": "pending"}))
    print(f"📥 Documents to download: {len(docs)}")
    if not docs:
        return
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(download_single_document, doc)
            for doc in docs
        ]
        for f in as_completed(futures):
            f.result()  # raise exception if any

def update_no_document_records():
    collection = get_uploaded_doc_collection()
    result = collection.update_many(
        {
            "upid": "-1"
        },
        {
            "$set": {
                "status": "completed",
                "doc_file_path": "N/A"
            }
        }
    )
    print(f"✅ Matched: {result.matched_count}")
    print(f"✅ Updated: {result.modified_count}")

# =========================
# MAIN
# =========================
def remove_doc_file_path_index():
    collection = get_uploaded_doc_collection()

    try:
        collection.drop_index("doc_file_path_1")
        print("✅ doc_file_path_1 index removed")
    except Exception as e:
        print("⚠️ Index not found:", e)
if __name__ == "__main__":
    ensure_uploaded_doc_indexes()
    remove_doc_file_path_index()
    update_no_document_records()
    # # STEP 1: SCRAPE DOCUMENT METADATA
    # # links = list(get_links_collection().find({"status": "done"}).limit(10))
    # # links = list(get_links_collection().find({"status": "scraped"})
    # #              .skip(2500)
    # #              .limit(2500))
    # # links = list(get_links_collection().find({"status": "done"}).limit(10))
    # links = list(get_links_collection().find({"status": "done"}))
    # print(f"🔍 Pages found: {len(links)}")
    # # quit()
    # with ThreadPoolExecutor(max_workers=10) as executor:
    #     futures = [executor.submit(scrape_uploaded_documents, page) for page in links]
    #     for f in as_completed(futures):
    #         f.result()
    #
    # print("✅ Metadata extraction completed")
    #
    # # STEP 2: DOWNLOAD FILES
    # download_uploaded_documents()
    # print("🎉 All tasks completed")

    # -----------------------------
    # STEP 2: DOWNLOAD FILES (THREADS)
    # -----------------------------
    download_uploaded_documents_threaded(max_workers=2)
    print("🎉 All tasks completed")

#
# # # ##########################   Create Json and Excel file ##############################

# 🔹 Paths
JSON_PATH = os.path.join(db.RESULT_PAGE, "uploaded_documents.json")

# 🔹 Mongo connection
client = MongoClient("mongodb://localhost:27017/")
db_mongo = client[db.DB_NAME]
collection = db_mongo["uploaded_doc_table"]
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

excel_path = os.path.join(db.RESULT_PAGE, "uploaded_documents.xlsx")

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
    "zip_file_path"
]

# 🔹 Create DataFrame
df = pd.DataFrame(data)

# 🔹 Reorder columns (only existing ones)
df = df[[col for col in columns if col in df.columns]]

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
