import html
import os
import db_config_1 as db
import pymysql
from parsel import Selector
import json
import re


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


# =========================
# MAIN SCRAPER FUNCTION
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

def main():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        query = f""" SELECT * FROM {db.product_link_table}
                     WHERE status = 'pending' AND pincode='700099' """
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("No pending product found.")
            return
        for r in rows:
            try:
                pincode = r["pincode"]
                slug = r["product_slug"]
                item_code = r["item_code"]
                folder_path = os.path.join(db.PDP_PAGESAVE, "pdp_pages", pincode)
                os.makedirs(folder_path, exist_ok=True)
                file_path = os.path.join(folder_path, f"{item_code}.html")
                # file_path = os.path.join(r"Z:\Team_Neela\Projects\act-hkssnd-7673-sku-mapping-and-price-benchmarking\metro_cash_and_carry\Pagesaves\04_2026\pdp_pages", pincode, f"{item_code}.html")
                with open(file_path, encoding="utf-8") as f:
                    html_text = f.read()
                data = extract_product(html_text)
                pdp_data = json.dumps(data, indent=2, ensure_ascii=False)
                # print(pdp_data)
                # update DB
                update_cursor = conn.cursor()
                update_query = f"""
                    UPDATE `{db.product_link_table}`
                    SET pdp_data = %s, status = %s
                    WHERE pincode = %s AND product_slug = %s
                """
                update_cursor.execute(update_query, (pdp_data, "extracted", pincode, slug))
                conn.commit()
                update_cursor.close()
                print(f"✅ Marked DONE → {slug} -> ({pincode})")
            except Exception as e:
                print(f"❌ Error for row: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()








# import html
# import os
# import db_config_1 as db
# import pymysql
# from parsel import Selector
# import json
# import re
#
#
# # =========================
# # SAFE UTIL HELPERS
# # =========================
#
# def safe_text(sel, xpath, default=None):
#     try:
#         val = sel.xpath(xpath).get()
#         return val.strip() if val else default
#     except Exception:
#         return default
#
#
# def safe_all(sel, xpath):
#     try:
#         return [v.strip() for v in sel.xpath(xpath).getall() if v]
#     except Exception:
#         return []
#
#
# def clean_number(value):
#     if not value:
#         return None
#     return re.sub(r"[^\d.]", "", value)
#
#
# def parse_qty_range(qty_range):
#     try:
#         if not qty_range:
#             return None, None
#         nums = re.findall(r"\d+", qty_range)
#         if len(nums) == 1:
#             return int(nums[0]), int(nums[0])
#         if len(nums) >= 2:
#             return int(nums[0]), int(nums[1])
#         return None, None
#     except Exception:
#         return None, None
#
#
# # =========================
# # MAIN SCRAPER FUNCTION
# # =========================
#
# def extract_product(html_text):
#     try:
#         sel = Selector(text=html_text)
#         # ---------------------
#         # PRODUCT INFO
#         # ---------------------
#         product_name = safe_text(sel, "//h2[contains(@class,'productName')]/text()")
#         brand_name = safe_text(sel, "//h4[contains(@class,'brandName')]/text()")
#         # STOCK (fallback safe)
#         stock = "in_stock"
#         try:
#             # if sel.xpath("//span[contains(@class,'soldOut')]").get():
#             #     stock = "sold_out"
#             if sel.xpath("//*[contains(text(),'Sold Out') or contains(text(),'Out of stock')]").get():
#                 stock = "sold_out"
#         except:
#             stock = "unknown"
#         # ---------------------
#         # PRICE
#         # ---------------------
#         mrp = clean_number(
#             safe_text(sel, "//span[contains(@class,'display-price')]/text()")
#         )
#         # ---------------------
#         # IMAGES (FILTERED)
#         # ---------------------
#         try:
#             images = sel.xpath(
#                 "//div[contains(@class,'sliderComponent')]//img/@src | "
#                 "//div[contains(@class,'mainImage')]//img/@src | "
#                 "//picture//img/@src"
#             ).getall()
#             images = list(set([
#                 img for img in images
#                 if img and (
#                         "products/pictures" in img or
#                         "products/pictures" in img
#                 )
#             ]))
#             # images = [
#             #     img for img in images
#             #     if img and "products/pictures" in img
#             # ]
#         except:
#             images = []
#         main_image = images[0] if images else None
#         # ---------------------
#         # DELIVERY
#         # ---------------------
#         delivery = safe_text(sel, "//div[contains(@class,'delivery-content-mb')]/text()")
#         # ---------------------
#         # SELLER
#         # ---------------------
#         seller = safe_text(sel, "//span[contains(@class,'seller-name')]/text()")
#         tiers = []
#
#         try:
#             # STRICT selector → only actual rows
#             tier_rows = sel.xpath("//div[contains(@class,'pdp-scroll-wrapper')]/div[contains(@class,'box')]")
#             # tier_rows = sel.xpath("//span[contains(@class,'qty-range')]/ancestor::div[contains(@class,'box')]")
#
#             seen = set()
#
#             for row in tier_rows:
#                 qty_range = row.xpath(".//span[contains(@class,'qty-range')]/text()").get()
#                 price = row.xpath(".//span[contains(@class,'qty-price')]/text()").get()
#                 profit = row.xpath(".//span[contains(@class,'qty-profit')]/text()").get()
#
#                 if not qty_range or not price:
#                     continue
#
#                 qty_range = qty_range.strip()
#                 price = price.strip()
#                 profit = profit.strip() if profit else None
#
#                 # ❌ skip header (extra safety)
#                 if qty_range.lower() == "qty" or "₹/pc" in price:
#                     continue
#
#                 # ❌ remove duplicates
#                 key = (qty_range, price)
#                 if key in seen:
#                     continue
#                 seen.add(key)
#
#                 min_qty, max_qty = parse_qty_range(qty_range)
#
#                 tiers.append({
#                     "min_qty": min_qty,
#                     "max_qty": max_qty,
#                     "margin": profit,
#                     "mrp": mrp,
#                     "retail_price_per_pc": price
#                 })
#
#         except Exception as e:
#             print("Tier error:", e)
#             tiers = []
#         # # ---------------------
#         # # TIERS
#         # # ---------------------
#         # tiers = []
#         # try:
#         #     # tier_rows = sel.xpath(
#         #     #     "//div[contains(@class,'box') or contains(@class,'pdp-scroll-wrapper')]"
#         #     # )
#         #     tier_rows = sel.xpath("//div[contains(@class,'pdp-scroll-wrapper')]//div[contains(@class,'box')]")
#         #     for row in tier_rows:
#         #         qty_range = row.xpath(".//span[contains(@class,'qty-range')]/text()").get()
#         #         price = row.xpath(".//span[contains(@class,'qty-price')]/text()").get()
#         #         profit = row.xpath(".//span[contains(@class,'qty-profit')]/text()").get()
#         #         if qty_range and price:
#         #             min_qty, max_qty = parse_qty_range(qty_range)
#         #             tiers.append({
#         #                 "min_qty": min_qty,
#         #                 "max_qty": max_qty,
#         #                 "margin": profit,
#         #                 # "margin": clean_number(profit),
#         #                 "mrp": mrp,
#         #                 # "retail_price_per_pc": clean_number(price)
#         #                 "retail_price_per_pc": price
#         #             })
#         # except:
#         #     tiers = []
#         # ---------------------
#         # PROMOTIONS
#         # ---------------------
#         promotions = []
#
#         try:
#             promo_blocks = sel.xpath("//div[contains(@class,'accordion-item')]")
#
#             for block in promo_blocks:
#                 title = block.xpath(".//p[contains(@class,'title')]/text()").get()
#                 discount = block.xpath(".//span[contains(@class,'title-left-savings')]/text()").get()
#                 expiry = block.xpath(".//p[contains(@class,'validTill')]/text()").get()
#
#                 if title or discount or expiry:
#                     promotions.append({
#                         "title": title.strip() if title else None,
#                         "discount": discount.strip() if discount else None,
#                         "expiry": expiry.strip() if expiry else None
#                     })
#         except:
#             promotions = []
#
#         # ---------------------
#         # DESCRIPTION (CLEAN HTML)
#         # ---------------------
#         description = None
#         try:
#             desc_html = sel.xpath("//div[@id='pdpDesc']").get()
#
#             if desc_html:
#                 # remove HTML tags
#                 description = re.sub(r"<[^>]+>", " ", desc_html)
#
#                 # remove extra spaces, newlines, tabs
#                 description = re.sub(r"\s+", " ", description).strip()
#
#         except:
#             description = None
#         # ---------------------
#         # FINAL STRUCTURE
#         # ---------------------
#         return {
#             "product_name": product_name,
#             "brand_name": brand_name,
#             "stock": stock,
#             "mrp": mrp,
#             "main_image": main_image,
#             "images": images,
#             "description": description,
#             "delivery": delivery,
#             "seller": seller,
#             "promotions": promotions,
#             "quantity_price_tiers": tiers
#         }
#
#     except Exception as e:
#         return {
#             "error": str(e)
#         }
#
#
#     # try:
#     #     with open("490000002.html", encoding="utf-8") as f:
#     #         html_text = f.read()
#     #
#     #     data = extract_product(html_text)
#     #
#     #     print(json.dumps(data, indent=2, ensure_ascii=False))
#     #
#     # except Exception as e:
#     #     print(json.dumps({"error": str(e)}, indent=2))
#
# def main():
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor(pymysql.cursors.DictCursor)
#     try:
#         query = f""" SELECT * FROM {db.product_link_table}
#                      WHERE status = 'done' AND pincode='700099'"""
#         cursor.execute(query)
#         rows = cursor.fetchall()
#         if not rows:
#             print("No pending product found.")
#             return
#         for r in rows:
#             try:
#                 pincode = r["pincode"]
#                 slug = r["product_slug"]
#                 item_code = r["item_code"]
#                 file_path = os.path.join(db.PDP_PAGESAVE, "pdp_pages", pincode, f"{item_code}.html")
#                 with open(file_path, encoding="utf-8") as f:
#                     html_text = f.read()
#                 data = extract_product(html_text)
#                 pdp_data = json.dumps(data, indent=2, ensure_ascii=False)
#                 # print(pdp_data)
#                 # update DB
#                 update_cursor = conn.cursor()
#                 update_query = f"""
#                     UPDATE `{db.product_link_table}`
#                     SET pdp_data = %s, status = %s
#                     WHERE pincode = %s AND product_slug = %s
#                 """
#                 update_cursor.execute(update_query, (pdp_data, "extracted", pincode, slug))
#                 conn.commit()
#                 update_cursor.close()
#                 print(f"✅ Marked DONE → {slug} -> ({pincode})")
#             except Exception as e:
#                 print(f"❌ Error for row: {e}")
#     finally:
#         cursor.close()
#         conn.close()
#
# if __name__ == '__main__':
#     main()