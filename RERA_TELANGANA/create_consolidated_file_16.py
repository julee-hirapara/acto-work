# # import pandas as pd
# #
# # # ---------------------------------------
# # # 1️⃣ Load the three Excel files
# # # ---------------------------------------
# #
# # project_listing = pd.read_excel(
# #     r"Z:\dv-bc_52935\03-2026\Projects\Files\project_listing.xlsx"
# # )
# #
# # promoter_info = pd.read_excel(
# #     r"Z:\dv-bc_52935\03-2026\Projects\Files\promoter_info.xlsx"
# # )
# #
# # project_info = pd.read_excel(
# #     r"Z:\dv-bc_52935\03-2026\Projects\Files\project_info_bank_details.xlsx"
# # )
# #
# #
# # # ---------------------------------------
# # # 2️⃣ Clean project_id (VERY IMPORTANT)
# # # ---------------------------------------
# #
# # for df in [project_listing, promoter_info, project_info]:
# #     df["project_id"] = df["project_id"].astype(str).str.strip()
# #
# #
# # # ---------------------------------------
# # # 3️⃣ Find duplicate column names
# # #     (excluding project_id)
# # # ---------------------------------------
# #
# # dup_lp = set(project_listing.columns) & set(promoter_info.columns)
# # dup_lpr = set(project_listing.columns) & set(project_info.columns)
# # dup_pr = set(promoter_info.columns) & set(project_info.columns)
# #
# # duplicate_columns = (dup_lp | dup_lpr | dup_pr) - {"project_id"}
# #
# # print("Duplicate Columns Found:")
# # print(duplicate_columns)
# #
# #
# # # ---------------------------------------
# # # 4️⃣ Rename duplicate columns ONLY
# # # ---------------------------------------
# #
# # promoter_info.rename(
# #     columns={
# #         col: f"promoter_{col}"
# #         for col in duplicate_columns
# #         if col in promoter_info.columns
# #     },
# #     inplace=True
# # )
# #
# # project_info.rename(
# #     columns={
# #         col: f"project_{col}"
# #         for col in duplicate_columns
# #         if col in project_info.columns
# #     },
# #     inplace=True
# # )
# #
# #
# # # ---------------------------------------
# # # 5️⃣ Merge all three files
# # # ---------------------------------------
# #
# # merged_df = (
# #     project_listing
# #     .merge(promoter_info, on="project_id", how="left")
# #     .merge(project_info, on="project_id", how="left")
# # )
# #
# #
# # # ---------------------------------------
# # # 6️⃣ Replace blank / None / NaN with "N/A"
# # # ---------------------------------------
# #
# # merged_df.replace(r'^\s*$', pd.NA, regex=True, inplace=True)  # replace empty strings
# # merged_df.fillna("N/A", inplace=True)  # replace NaN / None
# #
# #
# # # ---------------------------------------
# # # 7️⃣ Save final merged file
# # # ---------------------------------------
# #
# # output_path = r"Z:\dv-bc_52935\03-2026\Projects\Files\final_merged_projects.xlsx"
# # merged_df.to_excel(output_path, index=False)
# #
# # print("\n✅ Files merged successfully!")
# # print(f"📁 Saved at: {output_path}")
#
#
# import pandas as pd
#
# # ---------------------------------------
# # 1️⃣ Load the three Excel files
# # ---------------------------------------
#
# project_listing = pd.read_excel(
#     r"Z:\dv-bc_52935\03-2026\Projects\Files\project_listing.xlsx"
# )
#
# promoter_info = pd.read_excel(
#     r"Z:\dv-bc_52935\03-2026\Projects\Files\promoter_info.xlsx"
# )
#
# project_info = pd.read_excel(
#     r"Z:\dv-bc_52935\03-2026\Projects\Files\project_info_bank_details.xlsx"
# )
#
#
# # ---------------------------------------
# # 2️⃣ Clean project_id (VERY IMPORTANT)
# # ---------------------------------------
#
# for df in [project_listing, promoter_info, project_info]:
#     df["project_id"] = df["project_id"].astype(str).str.strip()
#
# # ---------------------------------------
# # 3️⃣ Find duplicate column names
# # ---------------------------------------
#
# dup_lp = set(project_listing.columns) & set(promoter_info.columns)
# dup_lpr = set(project_listing.columns) & set(project_info.columns)
# dup_pr = set(promoter_info.columns) & set(project_info.columns)
#
# duplicate_columns = (dup_lp | dup_lpr | dup_pr) - {"project_id"}
#
# print("🔍 Duplicate Columns Found:")
# print(duplicate_columns)
#
# # ---------------------------------------
# # 4️⃣ Rename duplicate columns
# # ---------------------------------------
#
# promoter_info.rename(
#     columns={
#         col: f"promoter_{col}"
#         for col in duplicate_columns
#         if col in promoter_info.columns
#     },
#     inplace=True
# )
#
# project_info.rename(
#     columns={
#         col: f"project_{col}"
#         for col in duplicate_columns
#         if col in project_info.columns
#     },
#     inplace=True
# )
#
# # ---------------------------------------
# # 5️⃣ Merge all files
# # ---------------------------------------
#
# merged_df = (
#     project_listing
#     .merge(promoter_info, on="project_id", how="left")
#     .merge(project_info, on="project_id", how="left")
# )
#
# # ---------------------------------------
# # 6️⃣ Clean empty values
# # ---------------------------------------
#
# merged_df.replace(r'^\s*$', pd.NA, regex=True, inplace=True)
# merged_df.fillna("N/A", inplace=True)
#
# # ---------------------------------------
# # 7️⃣ Define EXACT column order
# # ---------------------------------------
#
# final_column_order = [
#     "project_id", "Sr No.", "Project Name", "Promoter Name",
#     "View Details", "Last Modified Date", "View Certificate",
#     "View Extension Certificate", "View on Map", "Directions",
#     "Latitude", "Longitude", "Registration_number",
#
#     "Information Type", "Profile Image", "promoter_Promoter Name",
#     "Promoter_Middle Name", "Promoter_Last Name",
#     "Promoter_Father Name", "Organization Name",
#     "Organization Type", "Do you have any Past Experience ?",
#     "Does Applicant have GST Number ?",
#     "Do you have any registration in other State than registred State?",
#     "Description For Other Type Organization",
#     "Any criminal or police case/ cases pending ?",
#     "Do you have any registration in other States and Union Territories ?",
#     "GST Number",
#
#     "Promoter_House No/Sy. No/Block No/Plot No",
#     "Promoter_Building Name", "Promoter_Street Name",
#     "Promoter_Locality", "Promoter_Landmark",
#     "Promoter_State", "Promoter_District",
#     "Promoter_Mandal", "Promoter_Village/City/Town",
#     "Promoter_Pin Code",
#
#     "Office Number", "Fax Number", "Website URL",
#
#     "project_name", "Project Status",
#
#     "Separate Account of the Project (70%)_Bank A/c Number",
#     "Separate Account of the Project (70%)_IFSC Code",
#     "Total Building Units (as per approved plan)",
#     "Net Area(In sqmts)", "Approved Date", "Locality",
#
#     "Transaction Account of the Project (30%)_Branch Name",
#     "Revised Proposed Date of Completion",
#     "Boundaries West",
#
#     "Collection Account of the Project (100%)_IFSC Code",
#     "Proposed Building Units(as per agreement)",
#     "State", "Pin Code",
#
#     "Are there any Promoter(Land Owner/ Investor) (as defined by Telangana RERA Order) in the project ?",
#     "Sy.No/TS No.",
#
#     "Separate Account of the Project (70%)_Branch Name",
#     "Boundaries East", "Street", "District",
#     "Authority Name",
#
#     "Transaction Account of the Project (30%)_Bank Name",
#     "Transaction Account of the Project (30%)_Bank A/c Number",
#
#     "Village/City/Town",
#     "Approved Built up Area (In Sqmts)",
#     "Mortgage Area  (In Sqmts)",
#
#     "Separate Account of the Project (70%)_Bank Name",
#
#     "Is the project an MSB or a High-Rise?",
#     "Complition Date at the time of Registration in Telangana Rera",
#
#     "Area affected in Road widening/FTL of Tanks/Nala Widening(In sqmts)",
#     "Plot No./House No.", "Boundaries North",
#
#     "Transaction Account of the Project (30%)_IFSC Code",
#     "Boundaries South",
#
#     "Collection Account of the Project (100%)_Branch Name",
#     "Collection Account of the Project (100%)_Bank A/c Number",
#
#     "Proposed Date of Completion",
#
#     "project_Project Name",
#     "Plan Approval Number",
#     "Litigations related to the project ?",
#     "Total Area(In sqmts)",
#     "Project Type",
#
#     "Collection Account of the Project (100%)_Bank Name",
#     "Mandal",
#
#     "cert_zip_path",
#     "ext_cert_zip_path",
#     "image_path"
# ]
# # 👇 ADD HERE
# col_name = "Complition Date at the time of Registration in Telangana Rera"
#
# if col_name not in merged_df.columns:
#     merged_df[col_name] = "N/A"
# # ---------------------------------------
# # 8️⃣ Apply column order safely
# # ---------------------------------------
#
# final_column_order = [col for col in final_column_order if col in merged_df.columns]
#
# merged_df = merged_df[final_column_order]
#
# # ---------------------------------------
# # 9️⃣ Save final file
# # ---------------------------------------
#
# output_path = r"Z:\dv-bc_52935\03-2026\Projects\Files\consolidated.xlsx"
# merged_df.to_excel(output_path, index=False)
#
# print("\n✅ Files merged successfully!")
# print(f"📁 Saved at: {output_path}")
#
#


import pandas as pd
import db_config_1 as db
import os

# ==============================
# 1️⃣ LOAD ALL FILES
# ==============================
listing_excel_path = os.path.join(db.RESULT_PAGE, "project_listing.xlsx")
listing_df = pd.read_excel(listing_excel_path)
promoter_excel_path = os.path.join(db.RESULT_PAGE, "promoter_info.xlsx")
promoter_df = pd.read_excel(promoter_excel_path)
details_excel_path = os.path.join(db.RESULT_PAGE, "project_info_bank_details.xlsx")
details_df = pd.read_excel(details_excel_path)

# ==============================
# 2️⃣ MERGE USING project_id
# ==============================

df = listing_df.merge(
    promoter_df,
    on="project_id",
    how="left",
    suffixes=("", "_promoter")
)

df = df.merge(
    details_df,
    on="project_id",
    how="left",
    suffixes=("", "_details")
)

# ==============================
# 3️⃣ COLUMN MAPPING (Rename)
# ==============================

df.rename(columns={

    # General Information
    "Sr No.": "Sr No.",
    "Project Name": "Project Name",
    "Project URL": "Project URL",
    "Promoter Name": "Promoter Name",
    "Last Modified Date": "Last Modified Date",
    "View Certificate": "View Certificate",
    "View Extension Certificate": "View Extension Certificate",
    "View on Map": "View on Map",
    "Directions": "Directions",
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    "Registration_number": "Registration_number",

    # Promoter Info
    "Information Type": "Information Type",
    "Promoter_Name": "Promoter Name",
    "Promoter_Middle Name": "Middle Name",
    "Promoter_Last Name": "Last Name",
    "Promoter_Father Name": "Father Full Name",
    "Organization Name": "Organization Name",
    "Do you have any Past Experience ?": "Do you have any Past Experience ?",
    "GST Number": "GST Number",
    "Does Applicant have GST Number ?": "Does Applicant have GST Number ?",
    "Organization Type": "Organization Type",
    "Any criminal or police case/ cases pending ?": "Any criminal or police case/ cases pending ?",
    "Do you have any registration in other States and Union Territories ?":
        "Do you have any registration in other States and Union Territories ?",

    # Address
    "Promoter_House No/Sy. No/Block No/Plot No": "Promoter_House Number",
    "Promoter_Street Name": "Promoter_Street Name",
    "Promoter_Landmark": "Promoter_Landmark",
    "Promoter_District": "Promoter_District",
    "Promoter_Village/City/Town": "Promoter_Village/City/Town",
    "Promoter_Building Name": "Promoter_Building Name",
    "Promoter_Locality": "Promoter_Locality",
    "Promoter_State": "Promoter_State",
    "Promoter_Mandal": "Promoter_Mandal",
    "Promoter_Pin Code": "Promoter_Pin Code",
    "Office Number": "Office Number",
    "Website URL": "Website URL",
    "Fax Number": "Fax Number",

    # Project Details
    "Authority Name": "Authority Name",
    "Plan Approval Number": "Plan Approval Number",
    "Project Status": "Project Status",
    "Approved Date": "Approved Date",
    "Proposed Date of Completion": "Proposed Date of Completion",
    "Revised Proposed Date of Completion": "Revised Proposed Date of Completion",
    "Litigations related to the project ?": "Litigations related to the project ?",
    "Project Type": "Project Type",
    "Are there any Promoter(Land Owner/ Investor) (as defined by Telangana RERA Order) in the project ?":
        "Are there any Promoter(Land Owner/ Investor) (as defined by Telangana RERA Order) in the project ?",
    "Is the project an MSB or a High-Rise?":
        "Is the project an MSB or a High-Rise?",

    # Land
    "Sy.No/TS No.": "Sy.No/TS No.",
    "Total Area(In sqmts)": "Total Area (In sqmts)",
    "Net Area(In sqmts)": "Net Area (In sqmts)",
    "Proposed Building Units(as per agreement)": "Proposed Building Units (as per agreement)",
    "Plot No./House No.": "Plot No./House No.",
    "Area affected in Road widening/FTL of Tanks/Nala Widening(In sqmts)":
        "Area affected in Road widening/FTL of Tanks/Nala Widening (In sqmts)",
    "Total Building Units (as per approved plan)":
        "Total Building Units (as per approved plan)",

    # Boundaries
    "Boundaries East": "Boundaries East",
    "Boundaries North": "Boundaries North",
    "Boundaries West": "Boundaries West",
    "Boundaries South": "Boundaries South",

    # Area
    "Approved Built up Area (In Sqmts)": "Approved Built up Area (In Sqmts)",
    "Mortgage Area (In Sqmts)": "Mortgage Area (In Sqmts)",

    # Address Details
    "State_details": "State",
    "District_details": "District",
    "Mandal_details": "Mandal",
    "Street": "Street",
    "Village/City/Town": "Village/City/Town",
    "Locality_details": "Locality",
    "Pin Code_details": "Pin Code",

}, inplace=True)

# ==============================
# 4️⃣ DEFINE FINAL COLUMN ORDER
# ==============================
final_columns = [
    "project_id",
    # General Info
    "Sr No.", "Project Name", "Project URL", "Promoter Name",
    "Last Modified Date", "View Certificate", "View Extension Certificate",
    "View on Map", "Directions","Latitude", "Longitude", "Registration_number",
# project_id	Sr No.	Project Name	Promoter Name	View Details
#     Last Modified Date	View Certificate	View Extension Certificate
#     View on Map	Directions	Latitude	Longitude	Registration_number
#
#     Information Type	Profile Image	Promoter Name	Promoter_Middle Name	Promoter_Last Name	Promoter_Father Name	Organization Name	Organization Type	Do you have any Past Experience ?	Does Applicant have GST Number ?	Do you have any registration in other State than registred State?	Description For Other Type Organization	Any criminal or police case/ cases pending ?	Do you have any registration in other States and Union Territories ?	GST Number	Promoter_House No/Sy. No/Block No/Plot No	Promoter_Building Name	Promoter_Street Name	Promoter_Locality	Promoter_Landmark	Promoter_State	Promoter_District	Promoter_Mandal	Promoter_Village/City/Town	Promoter_Pin Code	Office Number	Fax Number	Website URL	project_name	Project Status	Separate Account of the Project (70%)_Bank A/c Number	Separate Account of the Project (70%)_IFSC Code	Total Building Units (as per approved plan)	Net Area(In sqmts)	Approved Date	Locality	Transaction Account of the Project (30%)_Branch Name	Revised Proposed Date of Completion	Boundaries West	Collection Account of the Project (100%)_IFSC Code	Proposed Building Units(as per agreement)	State	Pin Code	Are there any Promoter(Land Owner/ Investor) (as defined by Telangana RERA Order) in the project ?	Sy.No/TS No.	Separate Account of the Project (70%)_Branch Name	Boundaries East	Street	District	Authority Name	Transaction Account of the Project (30%)_Bank Name	Transaction Account of the Project (30%)_Bank A/c Number	Village/City/Town	Approved Built up Area (In Sqmts)	Mortgage Area (In Sqmts)	Separate Account of the Project (70%)_Bank Name	Is the project an MSB or a High-Rise?	Complition Date at the time of Registration in Telangana Rera	Area affected in Road widening/FTL of Tanks/Nala Widening(In sqmts)	Plot No./House No.	Boundaries North	Transaction Account of the Project (30%)_IFSC Code	Boundaries South	Collection Account of the Project (100%)_Branch Name	Collection Account of the Project (100%)_Bank A/c Number	Proposed Date of Completion	project_Project Name	Plan Approval Number	Litigations related to the project ?	Total Area(In sqmts)	Project Type	Collection Account of the Project (100%)_Bank Name	Mandal	cert_zip_path	ext_cert_zip_path	image_path

    # Promoter
    "Information Type",
    "Promoter Name",  # ✅ fixed
    "Middle Name",
    "Last Name",
    "Father Full Name",
    "Do you have any Past Experience ?",
    "GST Number",
    "Does Applicant have GST Number ?",
    "Organization Name",
    "Organization Type",
    "Any criminal or police case/ cases pending ?",
    "Do you have any registration in other States and Union Territories ?",

    # Address (USE RENAMED NAMES)
    "Promoter_House Number",
    "Promoter_Street Name",
    "Promoter_Landmark",
    "Promoter_District",
    "Promoter_Village/City/Town",
    "Promoter_Building Name",
    "Promoter_Locality",
    "Promoter_State",
    "Promoter_Mandal",
    "Promoter_Pin Code",

    # Contact
    "Office Number", "Website URL", "Fax Number",

    # Project Info
    "Authority Name", "Plan Approval Number", "Project Status",
    "Approved Date", "Proposed Date of Completion",
    "Revised Proposed Date of Completion",
    "Litigations related to the project ?",
    "Project Type",
    "Are there any Promoter(Land Owner/ Investor) (as defined by Telangana RERA Order) in the project ?",
    "Is the project an MSB or a High-Rise?",

    # Land
    "Sy.No/TS No.", "Total Area (In sqmts)", "Net Area (In sqmts)",
    "Proposed Building Units (as per agreement)",
    "Plot No./House No.",
    "Area affected in Road widening/FTL of Tanks/Nala Widening (In sqmts)",
    "Total Building Units (as per approved plan)",
    "Boundaries East", "Boundaries North",
    "Boundaries West", "Boundaries South",

    # Area
    "Approved Built up Area (In Sqmts)",
    "Mortgage Area (In Sqmts)",

    "State",
    "District",
    "Mandal",
    "Street",
    "Village/City/Town",
    "Locality",
    "Pin Code",
]


# df["Sr No."] = pd.to_numeric(df["Sr No."], errors="coerce")
# df = df[df["Sr No."].between(1, 10)]

# final_columns = [
#
#     # General Info
#     "Sr No.", "Project Name", "Project URL", "Promoter Name",
#     "Last Modified Date", "View Certificate", "View Extension Certificate",
#     "View on Map", "Directions",
#
#     # Promoter
#     "Information Type", "Promoter_Name",  "Middle Name", "Last Name", "Father Full Name",
#     "Do you have any Past Experience ?", "GST Number",
#     "Does Applicant have GST Number ?", "Organization Type",
#     "Any criminal or police case/ cases pending ?",
#     "Do you have any registration in other States and Union Territories ?",
#
#     # Address
#     "House Number", "Street Name", "Landmark", "District",
#     "Village/City/Town", "Building Name", "Locality",
#     "State", "Mandal", "Pin Code",
#
#     # Contact
#     "Office Number", "Website URL", "Fax Number",
#
#     # Project Info
#     "Authority Name", "Plan Approval Number", "Project Status",
#     "Approved Date", "Proposed Date of Completion",
#     "Revised Proposed Date of Completion",
#     "Litigations related to the project ?",
#     "Project Type",
#     "Are there any Promoter(Land Owner/ Investor) (as defined by Telangana RERA Order) in the project ?",
#     "Is the project an MSB or a High-Rise?",
#
#     # Land
#     "Sy.No/TS No.", "Total Area (In sqmts)", "Net Area (In sqmts)",
#     "Proposed Building Units (as per agreement)",
#     "Plot No./House No.",
#     "Area affected in Road widening/FTL of Tanks/Nala Widening (In sqmts)",
#     "Total Building Units (as per approved plan)",
#     "Boundaries East", "Boundaries North",
#     "Boundaries West", "Boundaries South",
#
#     # Area
#     "Approved Built up Area (In Sqmts)",
#     "Mortgage Area (In Sqmts)",
#
# ]

# Keep only available columns
final_columns = [col for col in final_columns if col in df.columns]
print(final_columns)
df = df[final_columns]
print(df)

# Replace NaN
df = df.fillna("N/A")

# ==============================
# 5️⃣ EXPORT TO EXCEL
# ==============================
output_file = os.path.join(db.RESULT_PAGE, "Consolidated_File.xlsx")
df.to_excel(output_file, index=False)

print("✅ Consolidated_File.xlsx created successfully!")
