import hashlib
import os
from datetime import datetime
import re
from pymongo import MongoClient



project_code = "ACT-JNSSND-8045"
now = datetime.now()
current_month_year = now.strftime("%m-%Y")
print(current_month_year)

# "Z:\julee\PAGESAVES"
# === PATH CONFIG ===Z:\dv-bc_52935
# file_server_path = f"J:\\{project_code}\\{current_month_year}\\Projects"
file_server_path = f"X:\\act-jnssnd-8045-property-agent-data-collection-from-rera-telangana-once-off\\Projects\\10-08-2026"
file_server_path_second = f"Z:\\act-jnssnd-8045-property-agent-data-collection-from-rera-telangana-once-off\\Projects\\10-08-2026"
os.makedirs(file_server_path, exist_ok=True)
assets_path = f"{file_server_path}\\Assets\\"
assets_path_second = f"{file_server_path_second}\\Assets\\"
os.makedirs(assets_path, exist_ok=True)
os.makedirs(assets_path_second, exist_ok=True)
files_path = f"{file_server_path}\\Files\\"
os.makedirs(files_path, exist_ok=True)
pagesave_path = f"{file_server_path}\\Pagesaves\\"
os.makedirs(pagesave_path, exist_ok=True)
RESULT_PAGE = f'{pagesave_path}results'
os.makedirs(RESULT_PAGE, exist_ok=True)
LINK_PAGESAVE = f'{pagesave_path}links'
os.makedirs(LINK_PAGESAVE, exist_ok=True)
DATA_PAGESAVE = f'{pagesave_path}data'
os.makedirs(DATA_PAGESAVE, exist_ok=True)
REVOKED_PAGESAVE = f'{pagesave_path}revoked'
os.makedirs(REVOKED_PAGESAVE, exist_ok=True)
LOG_FOLDER = f'{pagesave_path}log'
os.makedirs(LOG_FOLDER, exist_ok=True)


current_month_year_db = now.strftime("%m_%Y")
DB_NAME = f"rera_telangana_{project_code.replace("-","_")}_{current_month_year_db}"

def get_db_connection():
    client = MongoClient("mongodb://localhost:27017/")
    database = client[DB_NAME]
    return database


def get_mongo_links_collection():
    database = get_db_connection()
    return database["links"]

def ensure_indexes():
    col = get_mongo_links_collection()
    col.create_index("project_id", unique=True)
    col.create_index("status")


# === UTILES FUNCTION CONFIG ===
def clean_project_name(project_name: str) -> str:
    """
    Normalize project name for safe file/folder usage.
    - lowercase
    - remove special characters
    - normalize spaces
    """
    if not project_name:
        return None
    project_name = project_name.lower()
    project_name = re.sub(r'[^a-z0-9 ]', '', project_name)
    project_name = re.sub(r'\s+', ' ', project_name).strip()
    return project_name

def generate_hash(*args):
    raw = "|".join([str(a) for a in args if a])
    return hashlib.md5(raw.encode()).hexdigest()[:16]




