# pip install pymupdf easyocr pillow
import fitz  # PyMuPDF
import easyocr
import numpy as np
import pandas as pd
import json
import math
import random
import pdfplumber
import db_config_1 as db
import time
from parsel import Selector
import re
from curl_cffi import requests
from pymongo.errors import DuplicateKeyError
import logging
from logging.handlers import RotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
import zipfile
import os


reader = easyocr.Reader(['en'], gpu=False)

user_agent = [
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.166 Safari/537.36",
    "Mozilla/5.0 (Windows Server 2012 R2 Standard; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5975.80 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36"
]
BROWSERS = ["chrome", "chrome110", "chrome107", "chrome104", "chrome101",
            "edge99", "edge101", "safari15_5", "safari15_3"]

LOG_FILE = os.path.join(db.LOG_FOLDER, "PL_PDP_img_extraction.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    handlers=[
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
            encoding="utf-8"
        ),
        logging.StreamHandler()  # keeps console output
    ]
)
logger = logging.getLogger(__name__)


def insert_links_mongo(data):
    """Insert project link records into MongoDB, ignore duplicates"""
    col = db.get_mongo_links_collection()
    for link in data:
        try:
            col.insert_one(link)
        except DuplicateKeyError:
            pass
    logger.info(f"✔ Saved all projects {len(data)}links (MongoDB).")

def get_token_and_html(response_text):
    """Extract RequestVerificationToken and return Selector from HTML and handle session"""
    sel = Selector(text=response_text)
    token = sel.xpath('//input[@name="__RequestVerificationToken"]/@value').get()
    return token, sel

# --------------------------------------------------
# FILE PATH BUILDERS
# --------------------------------------------------
def build_profile_image_path(project_id, project_name, sr_no):
    """Generate local file path for project profile image"""
    project_folder = f"General Information - profile"
    hash_id = db.generate_hash(project_id, sr_no, "profile")
    project_name = db.clean_project_name(project_name)
    filename = f"{project_name} - {hash_id}_{sr_no}_profile_image.jpg"
    path = os.path.join(db.assets_path, project_folder)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, filename)

def build_certificate_path(project_id, project_name, cert_type):
    """Generate local file path for certificates PDFs"""
    project_folder = "Project Listing"
    project_name = db.clean_project_name(project_name)
    hash_id = db.generate_hash(project_id, cert_type)
    filename = f"{project_name} - {hash_id}_{cert_type}.pdf"
    # print(f"file_name {project_id}::: {filename}")
    path = os.path.join(db.assets_path, project_folder)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, filename)


# def build_certificate_path_zip(project_id, project_name, cert_type):
#     """Generate local file path for certificates PDFs"""
#     project_folder = "Project Listing"
#     project_name = db.clean_project_name(project_name)
#     hash_id = db.generate_hash(project_id, cert_type)
#     filename = f"{project_name} - {hash_id}_{cert_type}.zip"
#     # print(f"file_name {project_id}::: {filename}")
#     path = os.path.join(db.zip_assets_path, project_folder)
#     os.makedirs(path, exist_ok=True)
#     return os.path.join(path, filename)

def fetch_registered_project_count():
    """
    step: 1
    Fetches the total number of registered projects from
    the Telangana RERA website.
    The returned count is used later to handle pagination.
    """
    url = 'https://rera.telangana.gov.in/'
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': 'https://www.google.com/',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    }

    FILE_PATH = f"{db.LINK_PAGESAVE}\\main_page.html"
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding='UTF-8') as f:
            html_content = f.read()
    else:
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, verify=False)
                break
            except Exception as e:
                logger.warning(f"Retry {attempt + 1}/{max_retries} failed: {e}")
                time.sleep(2)
        else:
            logger.info("❌ Could not fetch page after retries")
            return
        time.sleep(5)
        if response.status_code == 200:
            html_content = response.text
            with open(FILE_PATH, "w", encoding='UTF-8') as f:
                f.write(html_content)
        else:
            response.raise_for_status()
    sel = Selector(text=html_content)
    count = sel.xpath("//a[contains(@href, 'SearchList/Search')]//h3/span/text()").get()
    count = count.strip()
    print("total count :: ", int(count.replace(",", "")))
    return int(count.replace(",", ""))

# Get project links...
def fetch_project_links(count):
    """
    step : 2
    Paginate project listings, store links, and trigger detail scraping
    """
    session = requests.Session()
    # Load initial GET page to get session cookies + first token
    first_page = session.get("https://rerait.telangana.gov.in/SearchList/Search", verify=False)
    current_token, sel = get_token_and_html(first_page.text)
    total_pages = math.ceil(count / 30)
    url = 'https://rerait.telangana.gov.in/SearchList/Search'
    for page in range(0, total_pages + 1):
    # for page in range(0, 7):
        file_path = f"{db.LINK_PAGESAVE}/links_page_{page}.html"
        logger.info(f"🔄 Fetching page {page}/{total_pages}")
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'origin': 'https://rerait.telangana.gov.in',
            'referer': 'https://rerait.telangana.gov.in/SearchList/Search',
            'user-agent': random.choice(user_agent),
        }
        data = [
            ('__RequestVerificationToken', current_token),
            ('Type', 'Promoter'),
            ('ID', '0'),
            ('pageTraverse', '1'),
            ('RoleIDPageload', '1'),
            ('Project', ''),
            ('hdnProject', ''),
            ('Promoter', ''),
            ('hdnPromoter', ''),
            ('AgentName', ''),
            ('hdnAgent', ''),
            ('CertiNo', ''),
            ('hdnCertiNo', ''),
            ('District', ''),
            ('hdnDivision', ''),
            ('hdnDistrict', ''),
            ('hdnProject', ''),
            ('hdnDTaluka', ''),
            ('hdnVillage', ''),
            ('hdnState', ''),
            ('Taluka', ''),
            ('Village', ''),
            ('CompletionDate_From', ''),
            ('hdnfromdate', ''),
            ('CompletionDate_To', ''),
            ('hdntodate', ''),
            ('PType', ''),
            ('hdnPType', ''),
            ('PlotBearing', ''),
            ('hdnPlotBearing', ''),
            ('Captcha', ''),
            ('TotalRecords', count),
            ('CurrentPage', page),
            ('TotalPages', total_pages),
            ('Command', 'Next'),
            ('PageSize', '30'),
        ]
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = session.post(url, headers=headers, data=data, impersonate=random.choice(BROWSERS), verify=False)
                # logger.info(response.status_code)
                break
            except Exception as e:
                logger.warning(f"Retry {attempt + 1}/{max_retries} failed: {e}")
                time.sleep(2)
        else:
            logger.info("❌ Could not fetch page after retries")
            return
        # time.sleep(5)
        if response.status_code == 200:
            html_content = response.text
            new_token, sel = get_token_and_html(response.text)
            current_token = new_token
            with open(file_path, "w", encoding='UTF-8') as f:
                f.write(html_content)
        else:
            response.raise_for_status()
        sel = Selector(text=html_content)
        data = extract_project_links(sel, file_path)
        # print(f"data ::: {data}")
        insert_links_mongo(data)

        fetch_project_details(data, session)
        print("get fetch project............")
        MAX_WORKERS = 3  # 🔥 SAFE VALUE (increase slowly)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for live in data:
                # Insert first (same as before)
                collection = db.get_mongo_links_collection()
                collection.update_one(
                    {"SrNo": str(live["SrNo"])},
                    {"$setOnInsert": live},
                    upsert=True
                )
                futures.append(executor.submit(process_project, live))
            for future in as_completed(futures):
                future.result()  # raises error if thread crashed

        print(f"✔ Page {page + 1}/{total_pages} processed")
        reprocess_failed_records()
    return

def extract_project_links(sel, file_path):
    """ step: 3 | Parse project rows from listing page and build project metadata"""
    rows = sel.xpath('//*[@id="projectTable"]/tbody/tr')
    token = sel.xpath('//input[contains(@name, "__RequestVerificationToken")]/@value').get()
    json_list = []

    def safe_text(n):
        return n.strip() if n else None

    for r in rows:
        map_onclick_value = r.xpath('./td[8]//a[contains(@id, "btnMap")]/@onclick').get()
        if map_onclick_value:
            project_id = map_onclick_value.split("(")[1].split(")")[0].replace("'", "")
            map_url = f"https://rerait.telangana.gov.in/GIS/view_map.aspx?ID={project_id}"
        else:
            map_url = None
        direction_onclick_value = r.xpath('./td[9]//a[contains(@id, "btnDirections")]/@onclick').get()
        if direction_onclick_value:
            lat, lng = re.findall(r"'(.*?)'", direction_onclick_value)
            direction_url = f"https://rerait.telangana.gov.in/GIS/get_direction.aspx?LAT={lat}&LNG={lng}"
        else:
            lat, lng = None, None
            direction_url = None

        view_details_value = safe_text(r.xpath('./td[4]/a/@href').get())
        if view_details_value:
            view_details = f"https://rerait.telangana.gov.in{view_details_value}"
        else:
            view_details = None

        extention_certificate = safe_text(r.xpath('./td[7]//a[contains(@id, "btnShow")]/@data-qstr').get())
        certificate = safe_text(r.xpath('./td[6]//a[contains(@id, "btnShow")]/@data-qstr').get())
        srno= safe_text(r.xpath('./td[1]/text()').get())
        project_name = safe_text(r.xpath('./td[2]/text()').get())
        last_modified_date = safe_text(r.xpath('./td[5]/text()').get())
        promoter_name = safe_text(r.xpath('./td[3]/text()').get())
        project_id = db.generate_hash(srno, project_name, promoter_name,last_modified_date)
        if file_path:
            file_path = file_path.replace("/", "\\")
            if file_path.startswith("Z:\\"):
                file_path = file_path.replace("Z:\\", "", 1)

        row_data = {
            "__RequestVerificationToken": token,
            "SrNo": srno,
            "ProjectName": project_name,
            "PromoterName": promoter_name,
            "ViewDetails": view_details,
            "LastModifiedDate": last_modified_date,
            "ViewCertificate": certificate,
            "ViewExtensionCertificate": extention_certificate,
            "ViewonMap": map_url,
            "Directions": direction_url,
            "Latitude": lat,
            "Longitude": lng,
            "project_id": project_id,
            "status": "pending",
            "file_path": file_path
        }
        json_list.append(row_data)
    return json_list


def fetch_image(sel, sr_no, session, project_id, project_name):
    """ step: 4 | Download and save project profile image"""
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'priority': 'u=0, i',
        'referer': 'https://rerait.telangana.gov.in/PrintPreview/PrintPreview?q=BtoHeb8QHAADiOjqG82OHd3pu%2fLIuCorXhNcE3xGNBhoH%2fsTZBsxK%2blC8aHwaCV8ZuB65IhfaZILlAetA4Si0uR%2b24DpizRHPYOe5R7dS3qNTJ%2bGo7eaXbFflbenD7iyH1UpfREACrCjSsChQGMrgCvMkr4tZ01lkTucNPYQn6o%3d',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    }
    response = session.get('https://rerait.telangana.gov.in/Preview/GetPicture',
                           headers=headers, verify=False)
    path = build_profile_image_path(project_id, project_name, sr_no)
    if response.status_code == 200:
        with open(path, "wb") as f:
            f.write(response.content)
        logger.info(f"✔ {sr_no} Image downloaded successfully!")
        return path
    else:
        logger.info(f"❌ Failed: {response.status_code}")
        return None


def fetch_db_projects():
    """Fetch pending projects from MongoDB and map by name & promoter"""
    col = db.get_mongo_links_collection()
    cursor = col.find(
        {"status": "pending"},   # WHERE status='completed'
        {
            "_id": 0,
            "project_id": 1,
            "ProjectName": 1,
            "PromoterName": 1,
            "ViewDetails": 1,
            "ViewCertificate": 1,
            "ViewExtensionCertificate": 1,
            "SrNo": 1,
            "status": 1
        }
    )
    project_map = {}
    for r in cursor:
        key = (r["ProjectName"], r["PromoterName"])
        project_map[key] = r
    return project_map


def fetch_project_details(data, session):
    """ step: 5 | Fetch project detail pages and update DB with paths"""
    max_retries = 5
    backoff = 10
    db_projects = fetch_db_projects()

    for rec in data:
        key = (rec["ProjectName"], rec["PromoterName"])
        # ❌ No exact match → skip
        if key not in db_projects:
            continue
        db_row = db_projects[key]
        sr_no = rec["SrNo"]
        view_url = rec["ViewDetails"]
        project_name = rec["ProjectName"]
        project_id = db_row['project_id']

        details_file = f"{db.DATA_PAGESAVE}\\{project_id}_{sr_no}.html"
        logger.info(f"details_file :: {details_file}")
        for attempt in range(max_retries):
            try:
                time.sleep(random.uniform(2, 5))
                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'referer': 'https://rerait.telangana.gov.in/SearchList/Search',
                    "user-agent": random.choice(user_agent),
                }
                response = session.get(view_url, headers=headers, impersonate=random.choice(BROWSERS), verify=False, timeout=500)
                # Unauthorized page
                if "Unauthorized" in response.text:
                    logger.info(f"❌ Unauthorized for {sr_no}, waiting 2 minutes…")
                    time.sleep(150)
                    session = requests.Session()  # refresh session
                    continue
                # ❌ Request worked but server responded 0 bytes (empty page)
                if len(response.text.strip()) == 0:
                    logger.info(f"⚠ Empty response for {sr_no}, retrying in {backoff}s…")
                    time.sleep(backoff)
                    backoff += 10
                    session = requests.Session()
                    continue
                # Successful fetch
                if response.status_code == 200:
                    sel = Selector(response.text)
                    image_path = sel.xpath('//div[contains(@class, "profile-img")]')
                    image_savepath = None
                    if image_path:
                        image_savepath = fetch_image(sel, sr_no, session, project_id, project_name)
                    with open(details_file, "w", encoding="utf-8") as f:
                        f.write(response.text)
                    logger.info(f"✔ Saved project page → {sr_no}.html")
                    # Update link table DB
                    try:
                        col = db.get_mongo_links_collection()
                        pdp_path = details_file.replace("Z:\\", "") if details_file else None
                        image_path = image_savepath.replace("Z:\\", "") if image_savepath else None
                        update_data = {
                            "status": "scraped",
                            "pdp_path": pdp_path
                        }
                        if image_savepath:
                            update_data["image_path"] = image_path
                        result = col.update_one(
                            {"SrNo": sr_no},
                            {"$set": update_data},
                            upsert=False
                        )
                        if result.matched_count:
                            logger.info(f"✔ Updated status to scraped → {sr_no}")
                        else:
                            logger.warning(f"⚠ No document found for SrNo → {sr_no}")
                    except Exception as db_err:
                        logger.exception(f"❌ Mongo update failed for {sr_no}: {db_err}")
                    break
                else:
                    logger.info(f"⚠ Attempt {attempt+1}/{max_retries} failed for {sr_no}: HTTP {response.status_code}")
                    time.sleep(random.uniform(5, 10))
                    session = requests.Session()
            except Exception as e:
                logger.exception(f"⚠ Attempt {attempt+1}/{max_retries} crashed for {sr_no}: {e}")
                time.sleep(random.uniform(5, 10))
                session = requests.Session()
        else:
            logger.info(f"❌ FAILED for {sr_no} after {max_retries} attempts")


def download_certificate(session, project_id, project_name, qstr, cert_type):
    """ step: 7 | Download project registration certificate PDF"""
    if not qstr:
        return None, None
    headers = {
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'QueryStringID': qstr,
    }
    response = session.get(
        'https://rerait.telangana.gov.in/SearchList/GetShowCertificateFileContent',
        params=params,
        headers=headers,
        verify=False
    )
    logger.info(f"certificate response :: {response.status_code}")
    if response.status_code == 200:
        # file_path = build_certificate_path(project_id, project_name, cert_type)
        # with open(file_path, "wb") as f:
        #     f.write(response.content)

        # 1️⃣ Build both paths
        pdf_path = build_certificate_path(project_id, project_name, cert_type)
        # zip_path = build_certificate_path_zip(project_id, project_name, cert_type)
        # 2️⃣ Save PDF
        with open(pdf_path, "wb") as f:
            f.write(response.content)
        # 3️⃣ Get only filename (important for inside zip)
        pdf_filename = os.path.basename(pdf_path)
        # 4️⃣ Create ZIP in separate folder
        # with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        #     zipf.write(pdf_path, arcname=pdf_filename)

        logger.info(f"✔ certificate {cert_type} saved & zipped {project_id}")

        # logger.info(f"✔ certificate {cert_type} saved {project_id}")
        registration_num, filepath = extract_registration_number(pdf_path)

        # return registration_num, pdf_path, zip_path   # ✅ RETURN
        return registration_num, pdf_path   # ✅ RETURN
    else:
        logger.info(f"❌ certificate{cert_type} failed {project_id}")
        return None, None

def extract_registration_number_from_pdf(pdf_path):
    """
    Fallback Function for extract registration number from image(PDF).
    Extract RERA Registration Number from scanned PDF using EasyOCR
    """
    try:
        text = ""
        # Open PDF
        doc = fitz.open(pdf_path)
        for page in doc:
            # Render page to image
            pix = page.get_pixmap(dpi=300)
            # Convert to numpy array
            img = np.frombuffer(pix.samples, dtype=np.uint8)
            img = img.reshape(pix.height, pix.width, pix.n)
            # OCR
            result = reader.readtext(img, detail=0)
            text += " ".join(result) + "\n"
        # Extract registration number
        match = re.search(
            r'project\s+registration\s+number\s*[:\-]?\s*([A-Z0-9\/\-]+)',
            text,
            re.IGNORECASE
        )
        if match:
            return match.group(1).strip(), pdf_path
        else:
            return None, None
    except Exception as e:
        logger.info(f"PDF read error: {e}")
        return None, None


def extract_registration_number(pdf_path):
    """Step: 8 | Extract RERA registration number from certificate PDF"""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # Telangana RERA pattern
        match = re.search(
            r'project registration number\s*[:\-]?\s*([A-Z0-9\/]+)',
            text,
            re.IGNORECASE
        )
        if match:
            return match.group(1).strip(), pdf_path
        else:
            registration_number, path = extract_registration_number_from_pdf(pdf_path)
            return registration_number, path
    except Exception as e:
        logger.info(f"PDF read error: {e}")
        return None, None

def download_extension_certificate(session, project_id, project_name, qstr, cert_type):
    """Step: 9 | Download project extension certificate PDF"""
    if not qstr:
        return None
    headers = {
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    response = session.get(
        f'https://rerait.telangana.gov.in/SearchList/GetShowExtensionCertificateFileContent/{qstr}',
        headers=headers,
        verify=False,
    )
    logger.info(f"certificate ext response ::  {response.status_code}")
    if response.status_code == 200:
        # file_path = build_certificate_path(project_id, project_name, cert_type)
        # with open(file_path, "wb") as f:
        #     f.write(response.content)

        # 1️⃣ Build both paths
        pdf_path = build_certificate_path(project_id, project_name, cert_type)
        # zip_path = build_certificate_path_zip(project_id, project_name, cert_type)
        # 2️⃣ Save PDF
        with open(pdf_path, "wb") as f:
            f.write(response.content)
        # 3️⃣ Get only filename (important for inside zip)
        # pdf_filename = os.path.basename(pdf_path)
        # 4️⃣ Create ZIP in separate folder
        # with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        #     zipf.write(pdf_path, arcname=pdf_filename)

        logger.info(f"✔ extension certificate {cert_type} saved & zipped {project_id}")
        # logger.info(f"✔ extension certificate {cert_type} saved {project_id}")
        return pdf_path   # ✅ RETURN
    else:
        logger.info(f"❌ extension certificate {cert_type} failed {project_id}")
        return None

def process_project(live):
    """Step: 6 | Thread worker to download certificates and update DB"""
    session = requests.Session()   # 🔑 thread-local session
    collection = db.get_mongo_links_collection()
    try:
        project_id = live["project_id"]
        project_name = live["ProjectName"]
        sr_no = live["SrNo"]

        # ---- Download main certificate ----
        registration_num, cert_path = download_certificate(
            session,
            project_id,
            project_name,
            live["ViewCertificate"],
            "view_certificate"
        )
        # ---- Download extension certificate ----
        ext_cert_path = download_extension_certificate(
            session,
            project_id,
            project_name,
            live["ViewExtensionCertificate"],
            "view_extension_certificate"
        )

        # ---- DB update ----
        update_data = {"status": "done"}

        if cert_path:
            update_data["view_certificate_file_path"] = cert_path.replace("J:\\", "")
            # update_data["view_certificate_zip_file_path"] = zip_path.replace("Z:\\", "")
            update_data["Registration_number"] = registration_num

        # if ext_cert_path:
        if isinstance(ext_cert_path, str):
            update_data["view_extension_certificate_file_path"] = ext_cert_path.replace("J:\\", "")
            # update_data["view_extension_certificate_zip_file_path"] = ext_zip_path.replace("Z:\\", "")

        collection.update_one(
            {"SrNo": sr_no},
            {"$set": update_data},
            upsert=True
        )

        logger.info(f"✔ Thread completed → {sr_no}")

    except Exception as e:
        collection.update_one(
            {"SrNo": sr_no},
            {"$set": {"status": "retry_failed"}}
        )
        logger.info(f"❌ Thread failed for SrNo {live.get('SrNo')}: {e}")
    finally:
        session.close()

def reprocess_failed_records():
    """Step : 10 | Retry certificate downloads for failed or partial records"""
    collection = db.get_mongo_links_collection()
    # failed_docs = list(collection.find({
    #     "$or": [
    #         {"status": "scraped"}
    #     ]
    # }))
    failed_docs = list(collection.find({
        "$or": [
            {"status": "retry_failed"}
        ]
    }))
    logger.info(f"🔁 Retrying {len(failed_docs)} failed records")
    MAX_WORKERS = 2
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_project, doc)
            for doc in failed_docs
        ]
        for future in as_completed(futures):
            future.result()
    logger.info("✅ Retry completed")


def create_json_and_excel():
    """Step : 11 | Finall step, Export MongoDB project data to JSON and Excel files"""
    # 🔹 Paths
    JSON_PATH = os.path.join(db.RESULT_PAGE, "project_listing.json")
    excel_path = os.path.join(db.RESULT_PAGE, "project_listing.xlsx")

    # 🔹 Mongo connection
    db_conn = db.get_db_connection()
    collection = db_conn["links"]
    # 🔹 Fetch data
    data = list(collection.find({}))  # add filters if needed
    print(len(data))

    # 🔹 Convert ObjectId → string
    for row in data:
        row["_id"] = str(row["_id"])

    # 🔹 Save JSON
    os.makedirs(db.RESULT_PAGE, exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ JSON file created: {JSON_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ==============================
    # DEFINE EXCEL COLUMNS & MAPPING
    # ==============================
    columns_mapping = {
        "project_id": "project_id",
        "Sr No.": "SrNo",
        "Project Name": "ProjectName",
        "Promoter Name": "PromoterName",
        "View Details": "ViewDetails",
        "Last Modified Date": "LastModifiedDate",
        "View Certificate": "ViewCertificate",
        "View Extension Certificate": "ViewExtensionCertificate",
        "View on Map": "ViewonMap",
        "Directions": "Directions",
        "Latitude": "Latitude",
        "Longitude": "Longitude",
        "view_extension_certificate_file_path": "view_extension_certificate_file_path",
        "view_certificate_file_path": "view_certificate_file_path",
        "Registration_number": "Registration_number",
        "file_path": "file_path",
        "image_path": "image_path",
        "pdp_path": "pdp_path",
        # "cert_zip_path": "view_certificate_zip_file_path",
        # "ext_cert_zip_path": "view_extension_certificate_zip_file_path"
    }

    # ==============================
    # BUILD ROWS
    # ==============================
    rows = []

    for record in data:
        row = {}
        for excel_col, json_key in columns_mapping.items():
            row[excel_col] = record.get(json_key)
        rows.append(row)
    # CREATE DATAFRAME
    df = pd.DataFrame(rows, columns=columns_mapping.keys())
    # SAVE TO EXCEL
    df.replace(to_replace=["", None, "NA"], value="N/A", inplace=True)
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
    # Save Excel
    # df.to_excel(excel_path, index=False)
    with pd.ExcelWriter(
            excel_path,
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_urls": False}}
    ) as writer:
        df.to_excel(writer, index=False)
    logger.info(f"✅ Excel file created successfully: {excel_path}")


if __name__ == "__main__":
    """Main execution flow: scrape, retry failures, export results"""
    db.ensure_indexes()
    # project_count = fetch_registered_project_count()
    # links = fetch_project_links(project_count)
    reprocess_failed_records()
    create_json_and_excel()



