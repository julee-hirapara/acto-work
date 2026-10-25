import pymysql
import db_config_1 as db
from slack_sdk import WebClient
import sys
import shutil
import os
import auto_data_count_fill as ac


def delete_slot_folders():
    folders = [
        os.path.dirname(db.file_base_path),
        os.path.dirname(db.PDP_pagesave_path),
    ]
    for folder in folders:
        try:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                print(f"✅ Deleted folder: {folder}")
            else:
                print(f"Folder does not exist: {folder}")
        except Exception as e:
            print(f"❌ Failed to delete {folder}: {e}")


def send_slack_msg():
    # --- Slack Config ---
    slack_bot_token = '**Hidden**'

    # channel_id = "C09S2JL46EA"  # Slack channel ID
    channel_id = "C0BG33Y8FNG"  # Slack channel ID
    qa_user_id = "U098Z1MVBNW"
    pc_user_id = "U09KTAGT6MU"
    # developer_user_id = "U093F9HP8BA"
    developer_user_id = "U0BAQJTN9K3"
    cc_user_ids = ["U05AC040LJU", "U08V35VE4CV"]

    # --- Slack Client ---
    client = WebClient(token=slack_bot_token)

    # Prepare message text
    cc_mentions = " ".join(f"<@{uid}>" for uid in cc_user_ids)

    qa_message = (
        f"<@{qa_user_id}> <@{pc_user_id}> There is no news found or unique data found for delivery: `{db.run_folder}`\n"
        f"Platform: https://www.constructionweekonline.com/\n"
        # f"Pagesave Path: \\\\***HIDDEN***\\temp-storage\\SynologyBackup\\News\\ConstructionWeekOnline\\UAE\\Web\\Partial run\\Data\\Page save\\{db.current_date_for_file}\\{db.slot}\\PL\n"
        f"Pagesave Path: \\\\***HIDDEN***\\SynologyBackup\\News\\ConstructionWeekOnline\\UAE\\Web\\Partial run\\Data\\Page save\\{db.current_date_for_file}\\{db.slot}\\PL\n"
        f"Developer: <@{developer_user_id}>\n"
        f"CC: {cc_mentions}"
    )

    try:
        # Send only message (no file upload)
        client.chat_postMessage(
            channel=channel_id,
            text=qa_message
        )
        print("✅ Message sent successfully")
        return True
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False


def delete_last_bot_message():
    slack_bot_token = '**Hidden**'

    # channel_id = "C09S2JL46EA"  # Slack channel ID
    channel_id = "C0BG33Y8FNG"  # Slack channel ID
    # --- Slack Client ---
    client = WebClient(token=slack_bot_token)
    try:
        client.chat_delete(
            channel="C0BG33Y8FNG",
            ts="1785373270.172119"
        )
        print(f"✅ Deleted message: 1785373270.172119")

    except Exception as e:
        print(f"❌ Error deleting message: {e}")
        return False




if __name__ == "__main__":
    conn = db.get_db_connection(db.db_name)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cur.execute(f""" SELECT COUNT(*) AS total FROM {db.link_table} WHERE STATUS = 'pending' """)
        pending_count = cur.fetchone()["total"]
        if pending_count > 0:
            print(f"{pending_count} pending records found. Not sending Slack message.")
            sys.exit(0)  # Continue with PDP script
        else:
            # delete_slot_folders()
            print("No pending records found. Sending Slack message.")
            if send_slack_msg():
                delete_slot_folders()
                platform = 'constructionweekonline.com'
                ac.upload_data_to_sheet(0, platform, 501)
                sys.exit(100)  # Stop the batch file
            else:
                sys.exit(1)    # Slack failed
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


