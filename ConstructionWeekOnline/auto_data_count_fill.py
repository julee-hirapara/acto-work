from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime


now = datetime.now()

hour = now.hour
if 0 <= hour < 6:
    slot = "00:00"
elif 6 <= hour < 12:
    slot = "06:00"
elif 12 <= hour < 18:
    slot = "12:00"
else:  # 18 <= hour < 24
    slot = "18:00"


def upload_data_to_sheet(data_count,platform,req_count):
    # Step 1: Read JSON
    # with open(json_file_path, "r", encoding="utf-8") as f:
    #     data = json.load(f)
    #
    # # Step 2: Count total reviews
    # data_count = sum(len(item.get("reviews", [])) for item in data)
    # print(data_count)

    # Step 3: Google Sheets authentication
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        r"D:\Julee\CODE\ConstructionWeekOnline\CODE\service_account.json", scopes=scope
    )

    client = gspread.authorize(creds)

    # Step 4: Open sheet
    sheet_name = "ACT-YSSSND-8558"
    # sheet = client.open(sheet_name).sheet1
    sheet = client.open_by_key("**Hidden**").worksheet("ACT-YSSSND-8558")
    # current_date = datetime.utcnow().strftime("%d-%m-%Y")
    current_date = datetime.now().strftime("%d-%m-%Y")

    # Step 5: Prepare row data
    row = [
        "ACT-YSSSND-8568",  # project_code
        "News/Article Data Collection from different websites – Daily",
        platform,
        current_date,
        # "00:05",
        slot,
        data_count,  # total reviews count
        req_count,
        # "Julee Hirapara"
        "Hiren Chauhan"
    ]
    # Step 6: Append row
    sheet.append_row(row)
    print(f"Data uploaded successfully! Total reviews: {data_count}")

