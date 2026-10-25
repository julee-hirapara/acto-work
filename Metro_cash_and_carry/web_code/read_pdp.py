import os
import json
import pymysql
from parsel import Selector
import db_config_1 as db
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================
# REUSE HELPERS
# =========================

def safe_text(sel, xpath, default=None):
    try:
        val = sel.xpath(xpath).get()
        return val.strip() if val else default
    except Exception:
        return default


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


# =========================
# EXTRACT FUNCTION (same)
# =========================

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
        # # mrp = clean_number(
        # #     safe_text(sel, "//span[contains(@class,'display-price')]/text()")
        # # )
        # mrp = clean_number(
        #     safe_text(sel,
        #               "(//span[contains(@class,'display-price')] | //span[contains(@class,'price-value')])[1]/text()")
        # )
        mrp = clean_number("".join(
            sel.xpath("""
                //span[contains(text(),'MRP')]/parent::span//span[contains(@class,'display-price')]//text()
                | //span[contains(@class,'display-price')]//text()
                | //span[contains(@class,'price-value')]//text()
            """).getall()
        ))
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
        # # ---------------------
        # # PROMOTIONS
        # # ---------------------
        promotions = []

        try:
            promo_blocks = sel.xpath("//div[contains(@class,'accordion-box')]")

            for block in promo_blocks:
                title = block.xpath(".//p[contains(@class,'title')]/text()").get()
                discount = block.xpath(".//span[contains(@class,'title-left-savings')]/text()").get()
                expiry = block.xpath(".//p[contains(@class,'validTill')]/text()").get()

                promotions.append({
                    "title": title.strip() if title else None,
                    "discount": discount.strip() if discount else None,
                    "expiry": expiry.strip() if expiry else None
                })

        except Exception as e:
            print(f"Error extracting promotions: {e}")
            promotions = []
        # promotions = []
        # try:
        #     promo_blocks = sel.xpath("//div[contains(@class,'accordion-item')]")
        #     for block in promo_blocks:
        #         title = block.xpath(".//p[contains(@class,'title')]/text()").get()
        #         discount = block.xpath(".//span[contains(@class,'title-left-savings')]/text()").get()
        #         expiry = block.xpath(".//p[contains(@class,'validTill')]/text()").get()
        #         if title or discount or expiry:
        #             promotions.append({
        #                 "title": title.strip() if title else None,
        #                 "discount": discount.strip() if discount else None,
        #                 "expiry": expiry.strip() if expiry else None
        #             })
        # except:
        #     promotions = []
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

# =========================
# THREAD WORKER
# =========================

def process_file(file_path, pincode, item_code):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        data = extract_product(html_text)
        pdp_data = json.dumps(data, ensure_ascii=False)

        return (pdp_data, "extracted", pincode, item_code)

    except Exception as e:
        print(f"❌ Failed: {item_code} → {str(e)[:60]}")
        return None


# =========================
# MAIN PROCESS (THREADED)
# =========================

def process_saved_html():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()

    base_folder = os.path.join(db.PDP_PAGESAVE, "pdp_pages")

    tasks = []

    # collect all files first
    for pincode in os.listdir(base_folder):
        pincode_path = os.path.join(base_folder, pincode)

        if not os.path.isdir(pincode_path):
            continue
    # target_pincode = "110032"
    # pincode_path = os.path.join(base_folder, target_pincode)
    #
    # if not os.path.isdir(pincode_path):
    #     print(f"❌ Pincode folder not found: {target_pincode}")
    #     return
    #
    # for file in os.listdir(pincode_path):
    #     if file.endswith(".html"):
    #         item_code = file.replace(".html", "")
    #         file_path = os.path.join(pincode_path, file)
    #
    #         tasks.append((file_path, target_pincode, item_code))

        for file in os.listdir(pincode_path):
            if file.endswith(".html"):
                item_code = file.replace(".html", "")
                file_path = os.path.join(pincode_path, file)

                tasks.append((file_path, pincode, item_code))

    print(f"🚀 Total files: {len(tasks)}")

    results = []

    # THREAD EXECUTION
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(process_file, fp, pc, ic)
            for fp, pc, ic in tasks
        ]

        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    print(f"✅ Extracted: {len(results)}")

    # =========================
    # BULK DB UPDATE
    # =========================

    update_query = f"""
        UPDATE `{db.product_link_table}`
        SET pdp_data = %s, status = %s
        WHERE pincode = %s AND item_code = %s
    """

    cursor.executemany(update_query, results)
    conn.commit()

    print(f"🔥 DB Updated in bulk: {len(results)}")

    cursor.close()
    conn.close()


# =========================
# RUN
# =========================

if __name__ == "__main__":
    process_saved_html()