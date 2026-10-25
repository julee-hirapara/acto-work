import os
import time
import pymysql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import db_config_1 as db
from parsel import Selector
import re
import json


# =========================
# SAFE UTIL HELPERS
# =========================

def safe_text(sel, xpath, default=None):
    try:
        val = sel.xpath(xpath).get()
        return val.strip() if val else default
    except Exception:
        return default


def safe_all(sel, xpath):
    try:
        return [v.strip() for v in sel.xpath(xpath).getall() if v]
    except Exception:
        return []


def clean_number(value):
    if not value:
        return None
    return re.sub(r"[^\d.]", "", value)


def parse_qty_range(qty_range):
    try:
        if not qty_range:
            return None, None
        nums = re.findall(r"\d+", qty_range)
        if len(nums) == 1:
            return int(nums[0]), int(nums[0])
        if len(nums) >= 2:
            return int(nums[0]), int(nums[1])
        return None, None
    except Exception:
        return None, None


def update_location_if_needed(driver, wait, target_pincode):
    """
    Handles initial modal priority, then falls back to 'Change' button logic.
    """
    try:
        # 1. PRIORITY: Check for the OLD/Initial modal (First-time visitor)
        # We look for the 'field' ID which appears on the very first load.
        field_elements = driver.find_elements(By.ID, "field")
        if field_elements and field_elements[0].is_displayed():
            print(f"📍 Handling initial Pincode modal: {target_pincode}")
            field_elements[0].clear()
            field_elements[0].send_keys(target_pincode)
            # Use JS click on the 'Apply' div
            apply_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Apply')]")))
            driver.execute_script("arguments[0].click();", apply_btn)
            # Wait for modal to disappear
            wait.until(EC.invisibility_of_element_located((By.ID, "field")))
            driver.refresh()
            time.sleep(2)
            return True

        # 2. SECONDARY: Check for the 'Change' button (City switching)
        time.sleep(1)
        change_elements = driver.find_elements(By.CLASS_NAME, "change-pincode")
        if change_elements and change_elements[0].is_displayed():
            print(f"🔄 Switching existing location to: {target_pincode}")
            driver.execute_script("arguments[0].scrollIntoView(true);", change_elements[0])
            driver.execute_script("arguments[0].click();", change_elements[0])
            # Wait for the POPUP input field
            pin_input = wait.until(EC.visibility_of_element_located((By.ID, "change-pincode")))
            pin_input.clear()
            pin_input.send_keys(target_pincode)
            # JS Click for APPLY button in the popup
            apply_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "apply-btn")))
            driver.execute_script("arguments[0].click();", apply_btn)
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "jio-pincode-content")))
            # driver.refresh()
            time.sleep(3)
            return True
        return True  # If neither is found, assume pincode is already correct
    except Exception as e:
        print(f"⚠️ Location update failed: {str(e)[:100]}")
        return False

def extract_product(html_text):
    try:
        sel = Selector(text=html_text)
        # ---------------------
        # PRODUCT INFO
        # ---------------------
        product_name = safe_text(sel, "//h2[contains(@class,'productName')]/text()")
        brand_name = safe_text(sel, "//h4[contains(@class,'brandName')]/text()")
        # STOCK (fallback safe)
        stock = "in_stock"
        try:
            # if sel.xpath("//span[contains(@class,'soldOut')]").get():
            #     stock = "sold_out"
            if sel.xpath("//*[contains(text(),'Sold Out') or contains(text(),'Out of stock')]").get():
                stock = "sold_out"
        except:
            stock = "unknown"
        # ---------------------
        # PRICE
        # ---------------------
        mrp = clean_number(
            safe_text(sel, "//span[contains(@class,'display-price')]/text()")
        )
        # ---------------------
        # IMAGES (FILTERED)
        # ---------------------
        try:
            images = sel.xpath(
                "//div[contains(@class,'sliderComponent')]//img/@src | "
                "//div[contains(@class,'mainImage')]//img/@src | "
                "//picture//img/@src"
            ).getall()
            images = list(set([
                img for img in images
                if img and (
                        "products/pictures" in img or
                        "products/pictures" in img
                )
            ]))
            # images = [
            #     img for img in images
            #     if img and "products/pictures" in img
            # ]
        except:
            images = []
        main_image = images[0] if images else None
        # ---------------------
        # DELIVERY
        # ---------------------
        delivery = safe_text(sel, "//div[contains(@class,'delivery-content-mb')]/text()")
        # ---------------------
        # SELLER
        # ---------------------
        seller = safe_text(sel, "//span[contains(@class,'seller-name')]/text()")
        # ---------------------
        # MOQ (Minimum Order Quantity)
        # ---------------------
        moq_text = safe_text(sel, "//span[contains(@class,'moq')]/text()")
        moq_min, moq_max = parse_qty_range(moq_text)
        tiers = []
        try:
            # STRICT selector → only actual rows
            tier_rows = sel.xpath("//div[contains(@class,'pdp-scroll-wrapper')]/div[contains(@class,'box')]")
            # tier_rows = sel.xpath("//span[contains(@class,'qty-range')]/ancestor::div[contains(@class,'box')]")
            seen = set()
            for row in tier_rows:
                qty_range = row.xpath(".//span[contains(@class,'qty-range')]/text()").get()
                price = row.xpath(".//span[contains(@class,'qty-price')]/text()").get()
                profit = row.xpath(".//span[contains(@class,'qty-profit')]/text()").get()
                if not qty_range or not price:
                    continue
                qty_range = qty_range.strip()
                price = price.strip()
                profit = profit.strip() if profit else None
                # ❌ skip header (extra safety)
                if qty_range.lower() == "qty" or "₹/pc" in price:
                    continue
                # ❌ remove duplicates
                key = (qty_range, price)
                if key in seen:
                    continue
                seen.add(key)
                min_qty, max_qty = parse_qty_range(qty_range)
                tiers.append({
                    "min_qty": min_qty,
                    "max_qty": max_qty,
                    "margin": profit,
                    "mrp": mrp,
                    "retail_price_per_pc": price
                })
        except Exception as e:
            print("Tier error:", e)
            tiers = []
        # ---------------------
        # PROMOTIONS
        # ---------------------
        promotions = []
        try:
            promo_blocks = sel.xpath("//div[contains(@class,'accordion-item')]")
            for block in promo_blocks:
                title = block.xpath(".//p[contains(@class,'title')]/text()").get()
                discount = block.xpath(".//span[contains(@class,'title-left-savings')]/text()").get()
                expiry = block.xpath(".//p[contains(@class,'validTill')]/text()").get()
                if title or discount or expiry:
                    promotions.append({
                        "title": title.strip() if title else None,
                        "discount": discount.strip() if discount else None,
                        "expiry": expiry.strip() if expiry else None
                    })
        except:
            promotions = []
        # ---------------------
        # DESCRIPTION (CLEAN HTML)
        # ---------------------
        description = None
        try:
            desc_html = sel.xpath("//div[@id='pdpDesc']").get()
            if desc_html:
                # remove HTML tags
                description = re.sub(r"<[^>]+>", " ", desc_html)
                # remove extra spaces, newlines, tabs
                description = re.sub(r"\s+", " ", description).strip()
        except:
            description = None
        # ---------------------
        # FINAL STRUCTURE
        # ---------------------
        return {
            "product_name": product_name,
            "brand_name": brand_name,
            "stock": stock,
            "mrp": mrp,
            "main_image": main_image,
            "images": images,
            "description": description,
            "delivery": delivery,
            "seller": seller,
            "moq_text": moq_text,
            "moq_min": moq_min,
            "moq_max": moq_max,
            "promotions": promotions,
            "quantity_price_tiers": tiers
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def get_pdp_page(driver, wait, conn, pincode, slug, item_code, current_active_pin):
    BASE_URL = "https://www.metrorrl.com/product/"
    url = f"{BASE_URL}{slug}/"
    try:
        driver.get(url)
        # We trigger the logic if it's the first run (active_pin is None)
        # OR if the city has changed.
        if str(current_active_pin) != str(pincode):
            if update_location_if_needed(driver, wait, pincode):
                current_active_pin = pincode
            else:
                return "invalid", current_active_pin
        # Final verification that product loaded
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@class,'add-to-cart-btn')]")))
        folder_path = os.path.join(db.PDP_PAGESAVE, "pdp_pages", str(pincode))
        time.sleep(1)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{item_code}.html")
        html_text = driver.page_source
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_text)
        # 🔥 EXTRACT
        data = extract_product(html_text)
        pdp_data = json.dumps(data, ensure_ascii=False)
        # 🔥 UPDATE DB
        cursor = conn.cursor()
        update_query = f"""
                UPDATE `{db.product_link_table}`
                SET pdp_data = %s, status = %s
                WHERE pincode = %s AND product_slug = %s
            """
        cursor.execute(update_query, (pdp_data, "extracted", pincode, slug))
        conn.commit()
        cursor.close()
        print(f"✅ Extracted + Saved → {item_code} ({pincode})")
        return "done", current_active_pin
    except Exception as e:
        print(f"❌ Scraping failed for {item_code}: {str(e)[:50]}")
        return "invalid", current_active_pin


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    })
    wait = WebDriverWait(driver, 15)
    active_pincode = None
    try:
        conn = db.get_db_connection(db.db_name)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        # Pull records grouped by pincode
        # query = f"SELECT * FROM {db.product_link_table} WHERE status = 'pending' AND pincode='700099' ORDER BY id DESC limit 50"
        # query = f"SELECT * FROM {db.product_link_table} WHERE status = 'pending' order by id DESC limit 110"
        query = f"SELECT * FROM {db.product_link_table} WHERE status = 'pending' AND pincode IN ('580030', '422007', '302018')"
        cursor.execute(query)
        rows = cursor.fetchall()
        for r in rows:
            status, active_pincode = get_pdp_page(
                driver, wait, conn, r["pincode"], r["product_slug"], r["item_code"], active_pincode
            )
    finally:
        driver.quit()
        if conn:
            conn.close()


if __name__ == '__main__':
    main()

