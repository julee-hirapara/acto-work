from datetime import datetime
import requests
import csv
import pandas as pd

# def get_csv_record_count(file_path):
#     with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
#         reader = csv.reader(f)
#         next(reader, None)  # Skip header
#         return sum(1 for _ in reader)


def dashboard_upload(feed_id, project_code, file_path, data_count, user_key,pagesave_path, remark, batch=1):
    try:
        url = "http://***HIDDEN***:5005/api/assign-to-qa"
        payload = {
            "feed_id": feed_id,
            "project_code": project_code,
            "file_path": file_path,
            "html_path": pagesave_path,
            "remark": remark,
            "data_count": data_count,
            "user_key": user_key,
            "batch": batch,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, json=payload)
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return response

    except Exception as e:
        print("❌ Error in assign_to_qa:", e)
        return None


def get_csv_record_count(file_path):
    return len(pd.read_csv(file_path))

if __name__ == '__main__':
    # Example
    file_path = r"J:\Team_Neela\Julee\Files\URBAN_OUTFITS\07_2026\results\Urban_outfitter_20260728.csv"
    count = get_csv_record_count(file_path)
    print(f"Total Records: {count}")
    # quit()
    feed_id = "8932"
    project_code = "AM-AG-42769"
    file_path = fr"\\***HIDDEN***\temp-storage\SynologyBackup\Team_Neela\Julee\Files\URBAN_OUTFITS\07_2026\results\Urban_outfitter_20260728.csv"
    # file_path_2 = fr"\\***HIDDEN***\temp-storage\SynologyBackup\Team_Neela\Projects\act-ysssnd-8558-news-articles-data-collection-from-different-websites-daily\constructionweekonline\19-07-2026\ConstructionWeekOnline_20260719_002734.csv"
    pagesave_path = fr"\\***HIDDEN***\temp-storage\SynologyBackup\Team_Neela\Julee\Pagesaves\URBAN_OUTFITTERS\07_2026"
    data_count = count
    user_key ="cDLNlZ0P%A=_%GP."
    dashboard_upload(feed_id, project_code, file_path, data_count, user_key, pagesave_path,
                     remark="Please QA this file. For PageSave verification, please refer to the hash_id and product_id fields.", batch=1)