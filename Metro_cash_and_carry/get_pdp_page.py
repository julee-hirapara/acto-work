from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import db_config_1 as db
import pymysql
import time


def get_pdp_page(driver, wait, pincode, slug, item_code, current_active_pin):
    BASE_URL = "https://www.metrorrl.com/product/"
    url = f"{BASE_URL}{slug}/"
    try:
        driver.get(url)
        # --- PINCODE ROUTING LOGIC ---
        # Only trigger pincode entry if it's NOT already set to the one we want
        if current_active_pin != pincode:
            try:
                print(f"🔄 Switching location to: {pincode}")
                pin_input = wait.until(EC.presence_of_element_located((By.ID, "field")))
                pin_input.clear()
                pin_input.send_keys(pincode)
                apply_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Apply')]")))
                apply_btn.click()
                wait.until(EC.invisibility_of_element_located((By.ID, "field")))
                # driver.refresh()  # Refresh once to lock in the new city
                current_active_pin = pincode  # Update our tracker
            except Exception as pin_error:
                print(f"⚠️ Pincode modal didn't appear or failed: {pin_error}")

        time.sleep(1)
        # --- SCRAPING LOGIC ---
        wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@class,'add-to-cart-btn')]")))

        folder_path = os.path.join(db.PDP_PAGESAVE, "pdp_pages", pincode)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{item_code}.html")
        time.sleep(2)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        print(f"✅ Saved: {item_code} ({pincode})")
        return "done", current_active_pin

    except Exception as e:
        print(f"❌ Failed {item_code}: {str(e)[:50]}")
        return "invalid", current_active_pin


def main():
    # ... (Driver Setup same as before) ...
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    # Track which pincode is currently active in the browser session
    active_pincode = None
    try:
        conn = db.get_db_connection(db.db_name)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        # CRITICAL: ORDER BY pincode ensures all same-city items run together
        query = f"""
            SELECT * FROM {db.product_link_table} 
            WHERE status = 'pending' AND pincode='700099'
            ORDER BY pincode
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for r in rows:
            # Pass the active_pincode and get the updated one back
            status, active_pincode = get_pdp_page(
                driver, wait, r["pincode"], r["product_slug"], r["item_code"], active_pincode
            )
            update_query = f"UPDATE `{db.product_link_table}` SET status = %s WHERE pincode = %s AND product_slug = %s"
            cursor.execute(update_query, (status, r["pincode"], r["product_slug"]))
            conn.commit()
    finally:
        driver.quit()
        if conn: conn.close()

if __name__ == '__main__':
    main()



# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
# import os
# import db_config_1 as db
# import pymysql
#
# def get_pdp_page(pincode, slug, item_code):
#     BASE_URL = "https://www.metrorrl.com/product/"
#     # PINCODE = "110001"
#
#     # product_slug = "maaza-mango-drink-12-l-g6s8htdrg736"
#     url = BASE_URL + slug + "/"
#     # ---- DRIVER SETUP ----
#     service = Service()
#     options = webdriver.ChromeOptions()
#     options.add_argument("--start-maximized")
#     driver = webdriver.Chrome(service=service, options=options)
#     wait = WebDriverWait(driver, 15)
#     try:
#         driver.get(url)
#
#         # ---- STEP 1: Wait for PIN input ----
#         pin_input = wait.until(
#             EC.presence_of_element_located((By.ID, "field"))
#         )
#         # ---- STEP 2: Enter PINCODE ----
#         pin_input.clear()
#
#         pin_input.send_keys(pincode)
#         # ---- STEP 3: Wait for APPLY button and click ----
#         apply_btn = wait.until(
#             EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Apply')]"))
#         )
#         apply_btn.click()
#         time.sleep(5)
#         wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
#         try:
#             # Wait for Add to Cart
#             wait.until(
#                 EC.presence_of_element_located(
#                     (By.XPATH, "//button[contains(@class,'add-to-cart-btn')]")
#                 )
#             )
#             # ---- STEP 5: Save HTML ----
#             folder_path = os.path.join(db.PDP_PAGESAVE, "pdp_pages", pincode)
#             os.makedirs(folder_path, exist_ok=True)
#             file_path = os.path.join(folder_path, f"{item_code}.html")
#             # Save only if valid
#             with open(file_path, "w", encoding="utf-8") as f:
#                 f.write(driver.page_source)
#             print(f"✅ Saved: {file_path}")
#             status = "done"
#         except Exception as e:
#             print(f"❌ Validation failed: {e}")
#             status = "invalid"
#         return status
#     finally:
#         driver.quit()
#
# def main():
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor(pymysql.cursors.DictCursor)
#     query = f""" SELECT * FROM {db.product_link_table} WHERE status = 'pending' AND pincode='422001' """
#     cursor.execute(query)
#     rows = cursor.fetchall()
#     cursor.close()
#     conn.close()
#     if not rows:
#         print("No pending product found.")
#     for r in rows:
#         try:
#             pincode = r["pincode"]
#             slug = r["product_slug"]
#             item_code = r["item_code"]
#             status = get_pdp_page(pincode, slug, item_code)
#             try:
#                 conn = db.get_db_connection(db.db_name)
#                 cursor = conn.cursor()
#                 query = f""" UPDATE `{db.product_link_table}` SET status = %s WHERE pincode = %s AND product_slug = %s """
#                 cursor.execute(query, (status, pincode, slug))
#                 conn.commit()
#                 print(f"✅ Marked DONE → {slug} -> ({pincode})")
#             except Exception as e:
#                 print(f"❌ Error updating status: {e}")
#             finally:
#                 cursor.close()
#                 conn.close()
#         except Exception as e:
#             print(f"❌ Error for {r}: {e}")
#
# if __name__ == '__main__':
#     main()