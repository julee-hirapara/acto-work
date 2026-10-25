import os
import pymysql
from slack_sdk import WebClient
import db_config_1 as db
import csv
from datetime import datetime
import requests
import time
import auto_data_count_fill as ac
import json
import re
from urllib.parse import quote


def create_json(rows, output_file):
    json_data = []
    for row in rows:
        item = {
            "title": row.get("title", ""),
            "text": row.get("message", ""),
            "published_date": row.get("created_time", ""),
            "source": row.get("source", ""),
            "domain": row.get("domain", ""),
            "publication_name": row.get("publication_name", ""),
            "author_name": row.get("journalist", ""),
            "country": row.get("country", ""),
            "media_title": row.get("media_title", ""),
            "url": row.get("permalink", ""),
            "reach": row.get("reach", ""),
            "web_share": row.get("web_shares", ""),
            "article_id": row.get("article_id", ""),
            # "Image URLs": row.get("image_urls", "")
        }
        image_urls = row.get("image_urls", "")
        if isinstance(image_urls, str):
            image_urls = image_urls.strip()
            if not image_urls:
                image_urls = ""
            elif image_urls.startswith("["):
                try:
                    image_urls = json.loads(image_urls)
                except json.JSONDecodeError:
                    image_urls = image_urls
            else:
                image_urls = [u.strip() for u in image_urls.split(",") if u.strip()]
        item["images"] = image_urls
        json_data.append(item)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)
    print(f"JSON Created : {output_file}")


def clean_image_urls(value):
    if not value:
        return ""
    # If DB value is a JSON/list string
    if isinstance(value, str):
        value = value.strip()
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            parsed = value
    else:
        parsed = value
    # Convert to list
    if isinstance(parsed, str):
        urls = [parsed]
    elif isinstance(parsed, list):
        urls = parsed
    else:
        return ""
    cleaned_urls = []
    for url in urls:
        if not url:
            continue
        url = str(url).strip()
        # ------------------------------------------------
        # Remove Markdown format:
        # [text](url)
        # ------------------------------------------------
        match = re.match(r'^\[.*?\]\((.*?)\)$', url)
        if match:
            url = match.group(1)
        # ------------------------------------------------
        # Convert literal \uXXXX / \\uXXXX
        # ------------------------------------------------
        url = re.sub(r'\\+u([0-9a-fA-F]{4})',lambda m: chr(int(m.group(1), 16)),url)
        # Remove unnecessary backslashes
        url = url.replace("\\", "")
        # ------------------------------------------------
        # URL encode Unicode characters
        # ------------------------------------------------
        if url.startswith(("http://", "https://")):
            parts = url.split("/", 3)
            if len(parts) == 4:
                scheme = parts[0]
                domain = parts[2]
                path = parts[3]
                path = quote(path, safe="/:@-._~!$&'()*+,;=")
                url = f"{scheme}//{domain}/{path}"
        cleaned_urls.append(url)
    # For CSV, store as comma-separated URLs
    # return ", ".join(cleaned_urls)
    return json.dumps(cleaned_urls, ensure_ascii=False)


def clean_values(values, fields=None):
    cleaned = []
    for index, v in enumerate(values):
        field = fields[index] if fields else None
        if v is None:
            cleaned.append("")
            continue
        if field == "image_urls":
            cleaned.append(clean_image_urls(v))
        else:
            cleaned.append(re.sub(r"\s+", " ", str(v)).strip())
    return cleaned



def write_csv(output_file, rows, headers, fields):
    with open(output_file, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(
            csvfile,
            delimiter=",",
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writerow(headers)
        for row in rows:
            values = [row.get(field) for field in fields]
            writer.writerow(clean_values(values, fields))
            # writer.writerow(
            #     clean_values([row.get(field) for field in fields])
            # )

    print(f"CSV Created : {output_file}")


def create_qa_csv(rows, output_file):
    headers = [
        "Keyword",
        "Title",
        "Message",
        "Created Time",
        "Source",
        "Domain",
        "Publication Name",
        "Journalist",
        "Country",
        "Media Title",
        "Permalink",
        "Reach",
        "Web Shares",
        "Article ID",
        "Image URLs",
        "search_hash_key"
    ]
    fields = [
        "keyword",
        "title",
        "message",
        "created_time",
        "source",
        "domain",
        "publication_name",
        "journalist",
        "country",
        "media_title",
        "permalink",
        "reach",
        "web_shares",
        "article_id",
        "image_urls",
        "search_hash_key"
    ]
    write_csv(output_file, rows, headers, fields)


# def create_json(rows, output_file):
#     json_data = []
#     for row in rows:
#         item = {
#             "Title": row.get("title", ""),
#             "Message": row.get("message", ""),
#             "Created Time": row.get("created_time", ""),
#             "Source": row.get("source", ""),
#             "Domain": row.get("domain", ""),
#             "Publication Name": row.get("publication_name", ""),
#             "Journalist": row.get("journalist", ""),
#             "Country": row.get("country", ""),
#             "Media Title": row.get("media_title", ""),
#             "Permalink": row.get("permalink", ""),
#             "Reach": row.get("reach", ""),
#             "Web Shares": row.get("web_shares", ""),
#             "Article ID": row.get("article_id", ""),
#         }
#         image_urls = row.get("image_urls", "")
#         if isinstance(image_urls, str):
#             image_urls = image_urls.strip()
#             if not image_urls:
#                 image_urls = ""
#             elif image_urls.startswith("["):
#                 try:
#                     image_urls = json.loads(image_urls)
#                 except json.JSONDecodeError:
#                     image_urls = image_urls
#             else:
#                 image_urls = [u.strip() for u in image_urls.split(",") if u.strip()]
#         item["image_urls"] = image_urls
#         json_data.append(item)
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=4)
#     print(f"JSON Created : {output_file}")


def create_csv(rows, output_file):
    headers = [
        # "Keyword",
        "Title",
        "Message",
        "Created Time",
        "Source",
        "Domain",
        "Publication Name",
        "Journalist",
        "Country",
        "Media Title",
        "Permalink",
        "Reach",
        "Web Shares",
        "Article ID",
        "Image URLs"
    ]
    fields = [
        # "keyword",
        "title",
        "message",
        "created_time",
        "source",
        "domain",
        "publication_name",
        "journalist",
        "country",
        "media_title",
        "permalink",
        "reach",
        "web_shares",
        "article_id",
        "image_urls"
    ]
    write_csv(output_file, rows, headers, fields)
    # Create JSON file with the same name
    json_file = os.path.splitext(output_file)[0] + ".json"
    create_json(rows, json_file)

def export_csv():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute(f""" SELECT * FROM {db.data_table} WHERE scrape_status ='extract_{current_date_for_file}_{db.slot}' """)
    # cursor.execute(f""" SELECT * FROM {db.data_table} WHERE scrape_status ='file_2026_10_06_12_00_PM' """)
    rows = cursor.fetchall()
    print(rows)
    filename = f"ConstructionWeekOnline_{db.run_folder}.csv"
    filename_for_QA = f"ConstructionWeekOnline_{db.run_folder}_QA.csv"
    output_file = os.path.join(db.devlivery_file_path, filename)
    output_file_for_QA = os.path.join(db.qa_file_path, filename_for_QA)
    # output_file = os.path.join('D:\Julee\CODE\ConstructionWeekOnline\CODE\Output', filename)
    # output_file_for_QA = os.path.join('D:\Julee\CODE\ConstructionWeekOnline\CODE\Output', filename_for_QA)
    create_csv(rows, output_file)
    create_qa_csv(rows, output_file_for_QA)
    # Get all exported article IDs
    article_ids = list({
        row["article_id"]
        for row in rows
        if row.get("article_id")
    })
    # Current date
    current_date = datetime.now().strftime("%Y_%m_%d")
    status = f"file_{current_date}_{db.slot}"
    if article_ids:
        placeholders = ",".join(["%s"] * len(article_ids))
        query = f"""
            UPDATE {db.data_table}
            SET scrape_status = %s
            WHERE article_id IN ({placeholders})
        """
        cursor.execute(query, [status] + article_ids)
        conn.commit()
        print(f"Updated {cursor.rowcount} records.")
    cursor.close()
    conn.close()
    row = len(rows)
    print("=" * 70)
    print("CSV Export Completed Successfully")
    print(f"Total Articles      : {len(rows)}")
    print(f"Output File         : {output_file}")
    print(f"Output File For QA  : {output_file_for_QA}")
    print("=" * 70)
    return output_file, output_file_for_QA, row


def dashboard_upload(feed_id, project_code, file_path, data_count, user_key, pagesave_path, remark):
    url = "http://***HIDDEN***:5005/api/assign-to-qa"
    headers = {'Content-Type': 'application/json'}
    max_retry = 4
    for batch in range(1, max_retry + 1):
        try:
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
            response = requests.post(url, headers=headers, json=payload)
            print(f"Batch: {batch}")
            print("Status Code:", response.status_code)
            print("Response:", response.text)
            if response.status_code == 200:
                print(f"✅ Upload successful with batch {batch}")
                return response
            print(f"❌ Upload failed. Retrying... ({batch}/{max_retry})")
        except Exception as e:
            print(f"❌ Error with batch {batch}: {e}")
        if batch < max_retry:
            time.sleep(1)
    print(f"❌ Upload failed after {max_retry} attempts.")
    return None

def send_slack_msg():
    # --- Slack Config ---
    slack_bot_token = db.slack_bot_token
    # channel_id = "C09S2JL46EA"  # Slack channel ID
    channel_id = "C0BG33Y8FNG"  # Slack channel ID
    qa_user_id = "U098Z1MVBNW"
    # second_qa_user_id = ""
    pc_user_id = "U09KTAGT6MU"
    # developer_user_id = "U093F9HP8BA"
    developer_user_id = "U0BAQJTN9K3"
    cc_user_ids = ["U05AC040LJU", "U08V35VE4CV"]
    # --- Slack Client ---
    client = WebClient(token=slack_bot_token)
    # Prepare message text
    cc_mentions = " ".join(f"<@{uid}>" for uid in cc_user_ids)
    qa_message = (
        f"<@{qa_user_id}>\nPlease QA this file : `{db.run_folder}`\n"
        f"*Platform:* https://www.constructionweekonline.com/\n"
        # f"Pagesave Path: \\\\***HIDDEN***\\temp-storage\\SynologyBackup\\News\\ConstructionWeekOnline\\UAE\\Web\\Partial run\\Data\\Page save\\{db.current_date_for_file}\\{db.slot}\\PL\n"
        f"*File Path:* \\\\***HIDDEN***\\SynologyBackup\\News\\ConstructionWeekOnline\\UAE\\Web\\Partial run\\Data\\File\\{db.current_date_for_file}\\{db.slot}\\QA\\ConstructionWeekOnline_{db.run_folder}_QA.csv\n"
        f"*Pagesave Path:* \\\\***HIDDEN***\\SynologyBackup\\News\\ConstructionWeekOnline\\UAE\\Web\\Partial run\\Data\\Page save\\{db.current_date_for_file}\\{db.slot}\\PL\n"
        f"*Developer:* <@{developer_user_id}>\n"
        f"*CC:* {cc_mentions}"
    )
    try:
        # Send only message (no file upload)
        client.chat_postMessage(channel=channel_id, text=qa_message)
        print("✅ Message sent successfully")
        return True
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False


if __name__ == "__main__":
    current_date_for_file = (datetime.now()).strftime("%Y_%m_%d")
    output_file, output_file_for_QA, rows = export_csv()
    platform = 'constructionweekonline.com'
    print(current_date_for_file, rows)
    if rows > 0:
        feed_id = "1925"
        project_code = "ACT-YSSSND-8558"
        # file_path = fr"\\***HIDDEN***\temp-storage\SynologyBackup\News\ConstructionWeekOnline\UAE\Web\Partial run\Data\File\{current_date_for_file}\{db.run_folder}\QA\ConstructionWeekOnline_{db.run_folder}_QA.csv"
        file_path = fr"\\***HIDDEN***\SynologyBackup\News\ConstructionWeekOnline\UAE\Web\Partial run\Data\File\{current_date_for_file}\{db.slot}\QA\ConstructionWeekOnline_{db.run_folder}_QA.csv"
        # pagesave_path = fr"\\***HIDDEN***\temp-storage\SynologyBackup\News\ConstructionWeekOnline\UAE\Web\Partial run\Data\Page save\{current_date_for_file}\{db.run_folder}"
        pagesave_path = fr"\\***HIDDEN***\SynologyBackup\News\ConstructionWeekOnline\UAE\Web\Partial run\Data\Page save\{current_date_for_file}\{db.slot}"
        data_count = rows
        # user_key ="cDLNlZ0P%A=_%GP."
        user_key ="Gkg:7h)=.>7l?Y*2"
        dashboard_response  = dashboard_upload(feed_id, project_code, file_path, data_count, user_key, pagesave_path,
                         remark="Please QA this file. search_hash_key is for QA purpose only")
        if dashboard_response is None:
            print("❌ Dashboard upload failed. Sending Slack notification...")
            send_slack_msg()
        else:
            print("✅ Dashboard upload successful. Slack message not required.")
        total_pl_req = 501
        req_count = total_pl_req + data_count
        ac.upload_data_to_sheet(data_count, platform, req_count)





