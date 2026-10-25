import os
import json
import re
import time
import random
import hashlib
from parsel import Selector
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient
import db_config_1 as db
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("✅ Script started")
# ======================================================
# MONGO SETUP (THREAD-SAFE, GLOBAL)
# ======================================================

def get_promoter_collection():
    mongo_db = db.get_db_connection()
    return mongo_db["promoter_info"]

def ensure_promoter_indexes():
    col = get_promoter_collection()
    col.create_index("Project_url", unique=True)
    col.create_index("project_id", unique=True)


def build_profile_image_path(project_id, project_name, sr_no):
    # project_folder = f"{project_id} - {clean_name(project_name)}"
    project_folder = f"General Information - profile"
    hash_id = generate_hash(project_id, sr_no, "profile")
    project_name = db.clean_project_name(project_name)
    filename = f"{project_name} - {hash_id}_{sr_no}_profile_image.jpg"
    path = os.path.join(db.assets_path, project_folder)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, filename)

# ======================================================
# UTILS
# ======================================================

def generate_hash(*args):
    raw = "|".join([str(a) for a in args if a])
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def generate_promoter_excel_from_json(json_path, excel_path):
    """
    Reads promoter JSON from RESULT_PAGE and generates Excel.
    Missing values are filled with 'N/A'.
    """

    # json_path = os.path.join(db.RESULT_PAGE, json_filename)

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    columns = [
        "Project Name", "Project URL", "Information Type", "Profile Image",

        "Promoter Name", "Promoter_Middle Name", "Promoter_Last Name",
        "Promoter_Father Name",

        "Organization Name", "Organization Type",

        "Do you have any Past Experience ?",
        "Does Applicant have GST Number ?",
        "Do you have any registration in other State than registred State?",
        "Description For Other Type Organization",
        "Any criminal or police case/ cases pending ?",
        "Do you have any registration in other States and Union Territories ?",
        "GST Number",

        "Promoter_House No/Sy. No/Block No/Plot No",
        "Promoter_Building Name",
        "Promoter_Street Name",
        "Promoter_Locality",
        "Promoter_Landmark",
        "Promoter_State",
        "Promoter_District",
        "Promoter_Mandal",
        "Promoter_Village/City/Town",
        "Promoter_Pin Code",

        "Office Number",
        "Fax Number",
        "Website URL",
        "file_name",
        "project_id",
        "image_path"
    ]

    rows = []

    for item in data:
        row = {col: "N/A" for col in columns}

        # ---------- Project ----------
        row["Project Name"] = item.get("Project_name", "N/A")
        row["Project URL"] = item.get("Project_url", "N/A")
        row["project_id"] = item.get("project_id", "N/A")
        row["image_path"] = item.get("image_path", "N/A")
        # ---------- General ----------
        general = item.get("General Information", {})
        row["Information Type"] = general.get("Information Type", "N/A")
        row["Profile Image"] = general.get("Profile Image", "N/A")

        # ---------- Individual ----------
        individual = item.get("Promoter Information - Individual", {})
        row["Promoter Name"] = individual.get("Promoter Name", "N/A")
        row["Promoter_Middle Name"] = individual.get("Middle Name", "N/A")
        row["Promoter_Last Name"] = individual.get("Last Name", "N/A")
        row["Promoter_Father Name"] = individual.get("Father Full Name", "N/A")

        row["Do you have any Past Experience ?"] = individual.get(
            "Do you have any Past Experience ?", "N/A"
        )
        row["Does Applicant have GST Number ?"] = individual.get(
            "Does Applicant have GST Number ?", "N/A"
        )
        row["Do you have any registration in other State than registred State?"] = individual.get(
            "Do you have any registration in other State than registred State?", "N/A"
        )
        row["GST Number"] = individual.get("GST Number", "N/A")

        # ---------- Organization ----------
        org = item.get("Promoter Information - Organization", {})
        row["Organization Name"] = org.get("Name", "N/A")
        row["Organization Type"] = org.get("Organization Type", "N/A")
        row["GST Number"] = org.get("GST Number", row["GST Number"])
        row["Description For Other Type Organization"] = org.get(
            "Description For Other Type Organization", "N/A"
        )
        row["Any criminal or police case/ cases pending ?"] = org.get(
            "Any criminal or police case/ cases pending ?", "N/A"
        )
        row["Do you have any registration in other States and Union Territories ?"] = org.get(
            "Do you have any registration in other States and Union Territories ?", "N/A"
        )
        row["Does Applicant have GST Number ?"] = org.get(
            "Does Applicant have GST Number ?", "N/A"
        )
        row["Do you have any Past Experience ?"] = org.get(
            "Do you have any Past Experience ?", row["Do you have any Past Experience ?"]
        )
        # row["Do you have any registration in other State than registred State?"] = org.get(
        #     "Do you have any registration in other State than registred State?", "N/A"
        # )
        if org.get("Do you have any registration in other State than registred State?"):
            row["Do you have any registration in other State than registred State?"] = \
                org.get("Do you have any registration in other State than registred State?")

        # ---------- Address ----------
        address = (
            item.get("Address Details")
            or item.get("Address For Official Communication")
            or {}
        )

        row["Promoter_House No/Sy. No/Block No/Plot No"] = (
            address.get("House Number")
            or address.get("House No/Sy. No/Block No/Plot No", "N/A")
        )
        row["Promoter_Building Name"] = address.get("Building Name", "N/A")
        row["Promoter_Street Name"] = address.get("Street Name") or address.get(
            "Street  Name", "N/A"
        )
        row["Promoter_Locality"] = address.get("Locality", "N/A")
        row["Promoter_Landmark"] = address.get("Landmark") or address.get(
            "Land mark", "N/A"
        )
        row["Promoter_State"] = address.get("State", "N/A")
        row["Promoter_District"] = address.get("District", "N/A")
        row["Promoter_Mandal"] = address.get("Mandal", "N/A")
        row["Promoter_Village/City/Town"] = address.get("Village/City/Town", "N/A")
        row["Promoter_Pin Code"] = address.get("Pin Code", "N/A")

        # ---------- Contact ----------
        contact = (
            item.get("Contact Details")
            or item.get("Organization Contact Details")
            or {}
        )
        row["Office Number"] = contact.get("Office Number", "N/A")
        row["Fax Number"] = contact.get("Fax Number", "N/A")
        row["Website URL"] = contact.get("Website URL", "N/A")

        row["file_name"] = item.get("file_name", "N/A")
        rows.append(row)

    df = pd.DataFrame(rows, columns=columns)
    # Replace empty, dash, or null values with N/A
    df.replace(to_replace=["-", "", None], value="N/A", inplace=True)
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
    print(f"Excel created successfully → {excel_path}")
    # print(f"✅ Excel created successfully → {excel_path}")
    return excel_path

# # ======================================================
# # PROMOTER INFO EXTRACTION
# # ======================================================
# def extract_promoter_information(sel):
#     final_result = {}
#     sections = sel.xpath('//div[@id="DivPInfo"]//div[contains(@class, "x_panel")]')
#
#     for panel in sections:
#         main_title = panel.xpath(
#             ".//div[@class='x_title']/h2/text() | .//div[@class='x_title']/h3/text()"
#         ).get()
#
#         if not main_title:
#             continue
#
#         main_title = main_title.strip()
#         final_result.setdefault(main_title, {})
#
#         # Profile Image
#         img_src = panel.xpath(".//div[contains(@class,'profile-img')]/img/@src").get()
#         if img_src:
#             if img_src.startswith("/"):
#                 img_src = "https://rerait.telangana.gov.in" + img_src
#             final_result[main_title]["Profile Image"] = img_src
#
#         # Subsections inside panel
#         subsection_positions = []
#         for sub in panel.xpath(".//h3"):
#             title = sub.xpath("normalize-space(text())").get()
#             if title:
#                 subsection_positions.append((sub.root.sourceline, title.strip()))
#
#         subsection_positions.sort(key=lambda x: x[0])
#         current_sub = None
#
#         for row in panel.xpath(".//div[contains(@class,'row')]"):
#             row_line = row.root.sourceline
#
#             # Detect subsection
#             for line, sub_title in subsection_positions:
#                 if line <= row_line:
#                     current_sub = sub_title
#                 else:
#                     break
#
#             # IMPORTANT: Subsection nested under main_title
#             if current_sub:
#                 final_result[main_title].setdefault(current_sub, {})
#                 target_dict = final_result[main_title][current_sub]
#             else:
#                 target_dict = final_result[main_title]
#
#             columns = row.xpath(".//div[contains(@class,'col-md')]")
#
#             if len(columns) >= 2:
#                 label = columns[0].xpath("normalize-space(.//label/text())").get()
#                 value = columns[1].xpath("normalize-space(.)").get()
#
#                 if label:
#                     label = label.strip().replace(":", "")
#                     value = value.strip() if value else None
#
#                     # PIN correction case
#                     if (
#                         label == "Village/City/Town"
#                         and value
#                         and value.isdigit()
#                         and len(value) == 6
#                     ):
#                         if not target_dict.get("Pin Code"):
#                             target_dict["Pin Code"] = value
#                         target_dict["Village/City/Town"] = None
#                         continue
#
#                     if label == "Pin Code" and not value:
#                         continue
#
#                     # Safe assign (do not overwrite existing)
#                     if label not in target_dict or not target_dict.get(label):
#                         target_dict[label] = value
#
#             # -----------------------------
#             # SPECIAL FIELD PATCH (SAFE)
#             # -----------------------------
#             special_field = "Do you have any registration in other State than registred State?"
#
#             row_text = row.xpath("normalize-space(.)").get()
#             if row_text and special_field in row_text:
#                 special_value = row.xpath(
#                     ".//div[contains(@class,'col-md')][last()]//text()"
#                 ).get()
#
#                 special_value = special_value.strip() if special_value else None
#
#                 if special_field not in target_dict:
#                     target_dict[special_field] = special_value
#
#     return final_result

def extract_promoter_information(sel):
    final_result = {}
    sections = sel.xpath('//div[@id="DivPInfo"]//div[contains(@class, "x_panel")]')

    for panel in sections:
        main_title = panel.xpath(
            ".//div[@class='x_title']/h2/text() | .//div[@class='x_title']/h3/text()"
        ).get()

        if not main_title:
            continue

        main_title = main_title.strip()
        final_result.setdefault(main_title, {})

        # Profile Image
        img_src = panel.xpath(".//div[contains(@class,'profile-img')]/img/@src").get()
        if img_src:
            if img_src.startswith("/"):
                img_src = "https://rerait.telangana.gov.in" + img_src
            final_result[main_title]["Profile Image"] = img_src

        subsection_positions = []
        for sub in panel.xpath(".//h3"):
            subsection_positions.append(
                (sub.root.sourceline, sub.xpath("text()").get().strip())
            )

        subsection_positions.sort(key=lambda x: x[0])
        current_sub = None

        for row in panel.xpath(".//div[contains(@class,'row')]"):
            row_line = row.root.sourceline

            for line, sub_title in subsection_positions:
                if line <= row_line:
                    current_sub = sub_title
                else:
                    break

            if current_sub:
                final_result.setdefault(current_sub, {})

            # ---------------------------
            # LABEL EXTRACTION
            # ---------------------------
            labels = row.xpath(
                ".//label[contains(@for, 'PersonalInfoModel')]/text() | .//label/text()"
            ).getall()

            labels = [
                l.strip().replace(":", "")
                for l in labels
                if l.strip() and l.strip().lower() not in ["yes", "no"]
            ]

            # ---------------------------
            # VALUE EXTRACTION (original)
            # ---------------------------
            value_divs = row.xpath(
                ".//div[contains(@class,'col-md')][not(.//label)]"
            )

            values = []
            for div in value_divs:
                text = div.xpath("normalize-space(.)").get()
                if text:
                    values.append(text)

            for i, label in enumerate(labels):
                value = values[i] if i < len(values) else None

                # 🔥 FIX FOR RADIO BUTTON FIELD
                if value is None:
                    # get second label (Yes/No)
                    radio_value = row.xpath(
                        ".//div[contains(@class,'col-md')][2]//label/text()"
                    ).get()

                    if radio_value:
                        value = radio_value.strip()

                # PIN correction
                if (
                    label == "Village/City/Town"
                    and value
                    and value.isdigit()
                    and len(value) == 6
                ):
                    if current_sub:
                        if not final_result[current_sub].get("Pin Code"):
                            final_result[current_sub]["Pin Code"] = value
                        final_result[current_sub]["Village/City/Town"] = None
                    else:
                        if not final_result[main_title].get("Pin Code"):
                            final_result[main_title]["Pin Code"] = value
                        final_result[main_title]["Village/City/Town"] = None
                    continue

                if label == "Pin Code" and not value:
                    continue

                if current_sub:
                    final_result[current_sub][label] = value
                else:
                    final_result[main_title][label] = value

    return final_result


# def extract_promoter_information(sel):
#     final_result = {}
#     sections = sel.xpath('//div[@id="DivPInfo"]//div[contains(@class, "x_panel")]')
#     for panel in sections:
#         main_title = panel.xpath(".//div[@class='x_title']/h2/text() | .//div[@class='x_title']/h3/text()").get()
#         if not main_title:
#             continue
#         main_title = main_title.strip()
#         final_result.setdefault(main_title, {})
#         # Profile Image
#         img_src = panel.xpath(".//div[contains(@class,'profile-img')]/img/@src").get()
#         if img_src:
#             if img_src.startswith("/"):
#                 img_src = "https://rerait.telangana.gov.in" + img_src
#             final_result[main_title]["Profile Image"] = img_src
#         # subsection detection
#         subsection_positions = []
#         for sub in panel.xpath(".//h3"):
#             subsection_positions.append((sub.root.sourceline, sub.xpath("text()").get().strip()))
#         subsection_positions.sort(key=lambda x: x[0])
#         current_sub = None
#         for row in panel.xpath(".//div[contains(@class,'row')]"):
#             row_line = row.root.sourceline
#             for line, sub_title in subsection_positions:
#                 if line <= row_line:
#                     current_sub = sub_title
#                 else:
#                     break
#             if current_sub:
#                 final_result.setdefault(current_sub, {})
#
#             labels = row.xpath(
#                 ".//label[contains(@for, 'PersonalInfoModel')]/text() | .//label/text()").getall()
#             labels = [
#                 l.strip().replace(":", "")
#                 for l in labels
#                 if l.strip() and l.strip().lower() not in ["yes", "no"]
#             ]
#             # 🔑 FIX IS HERE
#             value_divs = row.xpath(".//div[contains(@class,'col-md')][not(.//label)]")
#             values = []
#             for div in value_divs:
#                 text = div.xpath("normalize-space(.)").get()
#                 if text:
#                     values.append(text)
#             # # Extract all columns
#             # columns = row.xpath(".//div[contains(@class,'col-md')]")
#             #
#             # if len(columns) >= 2:
#             #     # First column = question
#             #     label = columns[0].xpath("normalize-space(.//label/text())").get()
#             #
#             #     # Second column = value (even if inside label tag like Yes/No)
#             #     value = columns[1].xpath("normalize-space(.)").get()
#             #
#             #     if label:
#             #         label = label.strip().replace(":", "")
#             #
#             #         # Assign properly
#             #         if current_sub:
#             #             final_result[current_sub][label] = value
#             #         else:
#             #             final_result[main_title][label] = value
#
#             for i, label in enumerate(labels):
#                 value = values[i] if i < len(values) else None
#
#                 # ✅ CASE 1: 6-digit PIN wrongly in Village
#                 if (
#                         label == "Village/City/Town"
#                         and value
#                         and value.isdigit()
#                         and len(value) == 6
#                 ):
#                     if current_sub:
#                         # set only if Pin Code not already set
#                         if not final_result[current_sub].get("Pin Code"):
#                             final_result[current_sub]["Pin Code"] = value
#                         final_result[current_sub]["Village/City/Town"] = None
#                     else:
#                         if not final_result[main_title].get("Pin Code"):
#                             final_result[main_title]["Pin Code"] = value
#                         final_result[main_title]["Village/City/Town"] = None
#                     continue
#
#                 # ✅ CASE 2: Normal Pin Code row → do NOT overwrite valid value with null
#                 if label == "Pin Code" and not value:
#                     continue
#
#                 # normal assignment
#                 if current_sub:
#                     final_result[current_sub][label] = value
#                 else:
#                     final_result[main_title][label] = value
#
#     return final_result


def extract_data(page):
    sr_no = page["SrNo"]
    project_id = page["project_id"]
    pdp_path = page.get("pdp_path")

    if not pdp_path:
        # print(f"❌ pdp_path missing for project: {project_id}")
        print(f"pdp_path missing for project: {project_id}")
        return None
    file_path = os.path.join("X:", page["pdp_path"])
    file_path = pdp_path.replace("J:", "X:", 1)

    image_path = page.get("image_path")
    # file_path = f"{db.DATA_PAGESAVE}\\{project_id}_{sr_no}.html"
    if not os.path.exists(file_path):
        # print(f"❌ Missing file: {file_path}")
        print(f"Missing file: {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    sel = Selector(html_content)
    promoter_data = extract_promoter_information(sel)
    final_result = promoter_data if promoter_data else {}
    final_result.update({
        "Project_url": page["ViewDetails"],
        "Project_name": page["ProjectName"],
        "file_name": f"{project_id}_{sr_no}.html",
        "project_id": project_id,
        "image_path": image_path if image_path else None
    })
    # print(f"{project_id} - final_result ::::::{json.dumps(final_result)}")
    col = get_promoter_collection()
    col.update_one(
        {"Project_url": final_result["Project_url"]},
        {"$set": final_result},
        upsert=True
    )
    print(f"✔ Saved → {final_result['Project_name']}")
    return final_result


# ======================================================
# MAIN RUNNER
# ======================================================


if __name__ == "__main__":
    ensure_promoter_indexes()

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
            try:
                result = future.result()
                if result:
                    ALL_ROWS.append(result)
            except Exception as e:
                # print(f"❌ Thread failed: {e}")
                print(f"Thread failed: {e}")
    #
    # # # Save JSON backup
    os.makedirs(db.RESULT_PAGE, exist_ok=True)
    json_path = os.path.join(db.RESULT_PAGE, "promoter_info.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ALL_ROWS, f, indent=2, ensure_ascii=False)
    excel_path = os.path.join(db.RESULT_PAGE, "promoter_info.xlsx")
    generate_promoter_excel_from_json(json_path, excel_path)
    # print(f"✅ Total saved: {len(ALL_ROWS)}")
    print(f"Total saved: {len(ALL_ROWS)}")

