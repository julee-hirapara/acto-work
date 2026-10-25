import json
import os
import html
import orjson
from parsel import Selector
from concurrent.futures import ProcessPoolExecutor
import db_config_1 as db

# -----------------------------
# CONFIG
# -----------------------------
# PDP_FOLDER = r"D:\julee\PAGESAVES\pet_supermarket\042026\PDP"
# VAR_FOLDER = r"D:\julee\PAGESAVES\pet_supermarket\042026\PDP\variation_pagesave"

# -----------------------------
# HELPERS
# -----------------------------
def normalize_size(val):
    return val.replace(" ", "").lower() if val else ""

from lxml import html as lxml_html

def clean_html_proper(raw_html):
    if not raw_html:
        return "N/A"
    try:
        raw_html = html.unescape(raw_html)
        tree = lxml_html.fromstring(raw_html)
        # First try specific tags (old logic)
        texts = tree.xpath('//p//text() | //li//text()')
        # Fallback to all text if empty
        if not texts:
            texts = tree.xpath('//text()')
        return " | ".join(t.strip() for t in texts if t.strip())
    except Exception:
        return "N/A"

# def clean_html_proper(raw_html):
#     if not raw_html:
#         return ""
#     sel = Selector(text=html.unescape(raw_html))
#     texts = sel.xpath('//p//text() | //li//text()').getall()
#     return " | ".join(t.strip() for t in texts if t.strip())

# -----------------------------
# INSERT QUERY
# -----------------------------

INSERT_QUERY = f"""
INSERT IGNORE INTO {db.data_table} (
    website, pid, name, short_description, description, category,
    image_url, price, price_currency, sale_price, final_price,
    discount, is_on_sale, is_in_stock, keywords, brand,
    manufacturer, mpn, upc_ean, sku, colour, gender, size,
    variant_price, alternate_image_urls, link_url,
    num_ratings, avg_ratings, hash_id, main_url
) VALUES (
    %s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,
    %s,%s,%s,%s
)
"""

# -----------------------------
# SINGLE ROW PROCESSOR
# -----------------------------
def process_single(row):
    results = []
    try:
        hash_key = row['hash_key']
        print(f"processing for {hash_key} ...")
        url = row['url']
        pdp_path = os.path.join(db.PDP_PAGESAVE, f"{hash_key}.html")
        print(pdp_path)
        try:
            if os.path.exists(pdp_path):
                with open(pdp_path, "r", encoding="utf-8") as f:
                    pdp_html = f.read()
        except FileNotFoundError:
            return results
        sel = Selector(text=pdp_html)
        # -----------------------------
        # MPN
        # -----------------------------
        mpn = "N/A"
        p_url = "N/A"
        scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
        for script in scripts:
            try:
                data = orjson.loads(script)
                # Handle list JSON-LD
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Product':
                            data = item
                            break
                if data.get('@type') == 'Product':
                    mpn = data.get('mpn', 'N/A')
                    offers = data.get('offers', {})
                    # Case 1: nested offers
                    if isinstance(offers, dict) and offers.get('offers'):
                        inner = offers.get('offers')
                        if isinstance(inner, list) and inner:
                            p_url = inner[0].get('url') or "N/A"
                    # Case 2: direct offer url
                    if p_url == "N/A" and isinstance(offers, dict):
                        p_url = offers.get('url') or "N/A"
                    # Case 3: fallback
                    if p_url == "N/A":
                        p_url = data.get('url') or data.get('@id') or "N/A"
                    break
            except Exception:
                continue

        # scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
        # for script in scripts:
        #     try:
        #         data = orjson.loads(script)
        #         if data.get('@type') == 'Product':
        #             mpn = data.get('mpn', 'N/A')
        #             p_url = data.get('url', '@id')
        #             break
        #     except:
        #         continue
        # -----------------------------
        # PDP JSON
        # -----------------------------
        raw_json = sel.xpath('//div[@class="pr-pdp-components"]/@data-pr-pdp-components').get()
        if not raw_json:
            return results
        pdp_data = orjson.loads(html.unescape(raw_json))
        product_block = pdp_data.get('product', {})
        variants = product_block.get('variants', [])
        product_url = product_block.get('url', "")
        # -----------------------------
        # HTML SIZES
        # -----------------------------
        html_sizes = sel.xpath('//button[contains(@class,"size-attribute")]/@data-attr-value').getall()
        html_sizes_clean = set(normalize_size(s) for s in html_sizes)
        # -----------------------------
        # LOOP VARIANTS
        # -----------------------------
        for var in variants:
            variant_id = var.get('page_id_variant')
            if not variant_id:
                continue
            var_file = os.path.join(db.variation_folder, f"{variant_id}.json")
            try:
                with open(var_file, "rb") as f:
                    var_data = orjson.loads(f.read())
            except:
                continue
            product = var_data.get('product', {})
            if product.get('id') != variant_id:
                continue
            # SIZE FILTER
            json_size = ""
            if product.get('variationAttributes'):
                json_size = product['variationAttributes'][0].get('displayValue', "")
            json_size_clean = normalize_size(json_size)
            if html_sizes_clean and json_size_clean not in html_sizes_clean:
                continue
            # -----------------------------
            # BASIC FIELDS
            # -----------------------------
            pid = product.get("masterProduct", {}).get("ID", "")
            name = product.get('productName', '')
            brand = product.get('brand', 'N/A')
            # PRICE
            price_block = product.get('price', {})
            sales_price = (price_block.get('sales') or {}).get('value')
            list_price = (price_block.get('list') or {}).get('value')
            final_price = sales_price or 0
            price = list_price or sales_price or 0
            sale_price = sales_price or 0
            discount = round(list_price - sales_price, 2) if list_price and sales_price else "N/A"
            currency = (price_block.get('sales') or {}).get('currency', '')
            # STOCK
            messages = product.get('availability', {}).get('messages', [])
            is_in_stock = "TRUE" if any("In Stock" in m for m in messages) else "FALSE"
            # DESCRIPTION
            description = clean_html_proper(product.get('shortDescription', ''))
            # CATEGORY
            category = product.get('powerReviewsComponents', {}).get('product', {}).get('category_name', '')
            category = category.replace(" > ", "/")
            # IMAGES
            images = product.get('images', {}).get('large', [])
            valid_images = [
                img['url'] for img in images
                if 'missing' not in img.get('url', '').lower()
            ]
            main_image = valid_images[0] if valid_images else "N/A"
            alt_images = " | ".join(valid_images[1:]) if len(valid_images) > 1 else "N/A"
            # images = product.get('images', {}).get('large', [])
            # main_image = images[0]['url'] if images else ''
            # alt_images = " | ".join(img['url'] for img in images[1:]) if len(images) > 1 else "N/A"
            # SIZE
            size = json_size or "N/A"
            # UPC
            upc = "N/A"
            pr_variants = product.get("powerReviewsComponents", {}).get("product", {}).get("variants", [])
            for v in pr_variants:
                if str(v.get("page_id_variant")) == str(product.get("id")):
                    upc = v.get("upc") or "N/A"
                    break
            # RATINGS
            avg_rating = product.get('customRating', {}).get('bvAverageRating') or "N/A"
            num_rating = product.get('customRating', {}).get('bvReviewCount') or "N/A"
            # SKU
            sku = product.get('id')
            import re
            new_link = re.sub(r'/[A-Z0-9]+\.html$', f'/{sku}.html', p_url) if sku else "N/A"
            # -----------------------------
            # APPEND DATA
            # -----------------------------
            results.append((
                "Pet Supermarket",
                pid,
                name,
                "N/A",
                description,
                category,
                main_image,
                price,
                currency,
                sale_price,
                final_price,
                discount,
                "No",
                is_in_stock,
                "N/A",
                brand,
                "N/A",
                mpn,
                upc,
                sku,
                "N/A",
                "N/A",
                size,
                final_price,
                alt_images,
                product_url,
                num_rating,
                avg_rating,
                hash_key,
                new_link
            ))
    except Exception as e:
        print(f"❌ Error processing {row.get('hash_key')}: {e}")
    # print(json.dumps(results))
    return results

# -----------------------------
# MAIN PROCESS
# -----------------------------
def process():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    cursor.execute(f"SELECT id, url, hash_key FROM {db.link_table} WHERE status ='redirect' limit 1000")
    links = cursor.fetchall()
    all_data = []
    # MULTIPROCESSING
    with ProcessPoolExecutor(max_workers=6) as executor:
        for res in executor.map(process_single, links):
            if res:
                all_data.extend(res)
    print(f"Total rows to insert: {len(all_data)}")
    # BATCH INSERT
    if all_data:
        cursor.executemany(INSERT_QUERY, all_data)
        conn.commit()
        # Update processed records to done
        ids = [link['id'] for link in links]  # assuming id is first column
        if ids:
            placeholders = ",".join(["%s"] * len(ids))
            cursor.execute(
                f"UPDATE {db.link_table} SET status='done' WHERE id IN ({placeholders})",
                ids
            )
            conn.commit()
    conn.close()
    print("✅ ALL DONE")
    # if all_data:
    #     cursor.executemany(INSERT_QUERY, all_data)
    #     conn.commit()
    # conn.close()
    # print("✅ ALL DONE")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    process()


# import os
# import json
# import html
# import re
# from parsel import Selector
# import db_config as db
#
#
# # -----------------------------
# # CONFIG
# # -----------------------------
# PDP_FOLDER = r"D:\julee\PAGESAVES\pet_supermarket\042026\PDP"
# VAR_FOLDER = r"D:\julee\PAGESAVES\pet_supermarket\042026\PDP\variation_pagesave"
#
# def normalize_size(val):
#     if not val:
#         return ""
#     return val.replace(" ", "").lower()
#
# # -----------------------------
# # CLEAN DESCRIPTION
# # -----------------------------
# def clean_html_proper(raw_html):
#     if not raw_html:
#         return ""
#     # 1️⃣ Unescape (handles encoded HTML safely)
#     text = html.unescape(raw_html)
#     # 2️⃣ Parse HTML
#     sel = Selector(text=text)
#     parts = []
#     # 3️⃣ Extract structured text
#     for tag in sel.xpath('//p | //li'):
#         t = " ".join([x.strip() for x in tag.xpath('.//text()').getall() if x.strip()])
#         if t:
#             parts.append(t)
#     # 4️⃣ Fallback (plain text case)
#     if not parts:
#         parts = [t.strip() for t in sel.xpath('//text()').getall() if t.strip()]
#     # 5️⃣ Final clean
#     final = " | ".join(parts)
#     final = " ".join(final.split())
#     return final
#
# # def clean_html_proper(raw_html):
# #     sel = Selector(text=raw_html)
# #     parts = []
# #     for p in sel.xpath('//p'):
# #         text = " ".join([t.strip() for t in p.xpath('.//text()').getall() if t.strip()])
# #         if text:
# #             parts.append(text)
# #     for li in sel.xpath('//li'):
# #         text = " ".join([t.strip() for t in li.xpath('.//text()').getall() if t.strip()])
# #         if text:
# #             parts.append(text)
# #     return " | ".join(parts)
#
# # -----------------------------
# # INSERT QUERY
# # -----------------------------
# INSERT_QUERY = f"""
# INSERT IGNORE INTO {db.data_table} (
#     website, pid, name, short_description, description, category,
#     image_url, price, price_currency, sale_price, final_price,
#     discount, is_on_sale, is_in_stock, keywords, brand,
#     manufacturer, mpn, upc_ean, sku, colour, gender, size,
#     variant_price, alternate_image_urls, link_url,
#     num_ratings, avg_ratings, hash_id, main_url
# ) VALUES (
#     %s,%s,%s,%s,%s,%s,
#     %s,%s,%s,%s,%s,
#     %s,%s,%s,%s,%s,
#     %s,%s,%s,%s,%s,%s,%s,
#     %s,%s,%s,
#     %s,%s,%s,%s
# )
# """
#
# from concurrent.futures import ProcessPoolExecutor
#
# def process_single(row):
#     try:
#         hash_key = row['hash_key']
#         url = row['url']
#
#         pdp_path = os.path.join(PDP_FOLDER, f"{hash_key}.html")
#         if not os.path.exists(pdp_path):
#             return None
#
#         with open(pdp_path, "r", encoding="utf-8") as f:
#             pdp_html = f.read()
#
#         sel = Selector(text=pdp_html)
#
#         # ---- DO ALL YOUR EXISTING LOGIC ----
#         # return list of rows to insert
#         results = []
#
#         # append tuples (data) instead of inserting here
#         return results
#
#     except Exception as e:
#         print("Error:", e)
#         return None
#
# def process():
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor()
#     query = f"SELECT id, url, hash_key FROM {db.link_table} WHERE status ='done'"
#     cursor.execute(query)
#     links = cursor.fetchall()
#
#     for row in links:
#         try:
#             hash_key = row['hash_key']
#             url = row['url']
#             pdp_path = os.path.join(PDP_FOLDER, f"{hash_key}.html")
#             if not os.path.exists(pdp_path):
#                 print("Missing PDP:", hash_key)
#                 continue
#             with open(pdp_path, "r", encoding="utf-8") as f:
#                 pdp_html = f.read()
#             sel = Selector(text=pdp_html)
#             # MPN
#             mpn = "N/A"
#             scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
#             for script in scripts:
#                 try:
#                     data = json.loads(script)
#                     if data.get('@type') == 'Product':
#                         mpn = data.get('mpn', 'N/A')
#                         break
#                 except:
#                     pass
#             # PDP JSON
#             raw_json = sel.xpath('//div[@class="pr-pdp-components"]/@data-pr-pdp-components').get()
#             if not raw_json:
#                 continue
#             pdp_data = json.loads(html.unescape(raw_json))
#             product_block = pdp_data.get('product', {})
#             variants = product_block.get('variants', [])
#             product_url = product_block.get('url', "")
#             # HASH ID
#             # # -----------------------------
#             # # LOOP VARIANTS
#             # # -----------------------------
#             # for var in variants:
#             #     variant_id = var.get('page_id_variant')
#             #     if not variant_id:
#             #         continue
#             #     var_file = os.path.join(VAR_FOLDER, f"{variant_id}.json")
#             #     if not os.path.exists(var_file):
#             #         print("Missing VAR:", variant_id)
#             #         continue
#             #     with open(var_file, "r", encoding="utf-8") as f:
#             #         var_data = json.load(f)
#             #     product = var_data.get('product', {})
#             #     if product.get('id') != variant_id:
#             #         continue
#             html_sizes = sel.xpath(
#                 '//button[contains(@class,"size-attribute")]/@data-attr-value'
#             ).getall()
#             html_sizes_clean = [normalize_size(s) for s in html_sizes]
#             print("HTML sizes:", html_sizes_clean)
#
#             # -----------------------------
#             # LOOP VARIANTS
#             # -----------------------------
#             for var in variants:
#                 variant_id = var.get('page_id_variant')
#                 if not variant_id:
#                     continue
#                 var_file = os.path.join(VAR_FOLDER, f"{variant_id}.json")
#                 if not os.path.exists(var_file):
#                     print("Missing VAR:", variant_id)
#                     continue
#                 with open(var_file, "r", encoding="utf-8") as f:
#                     var_data = json.load(f)
#                 product = var_data.get('product', {})
#                 if product.get('id') != variant_id:
#                     continue
#                 # 👉 JSON SIZE
#                 json_size = ""
#                 if product.get('variationAttributes'):
#                     json_size = product['variationAttributes'][0].get('displayValue', "")
#                 json_size_clean = normalize_size(json_size)
#                 # 👉 FILTER: ONLY TAKE SIZES PRESENT IN HTML
#                 if html_sizes_clean:
#                     if json_size_clean not in html_sizes_clean:
#                         print(f"❌ Skipping (not in HTML): {variant_id} | Size: {json_size}")
#                         continue
#                 print(f"✔ Taking: {variant_id} | Size: {json_size}")
#                 # BASIC FIELDS
#                 pid = product.get("masterProduct", {}).get("ID", "")
#                 name = product.get('productName', '')
#                 brand = product.get('brand', 'N/A')
#                 # PRICE
#                 price_block = product.get('price', {})
#                 sales_price = (price_block.get('sales') or {}).get('value')
#                 list_price = (price_block.get('list') or {}).get('value')
#                 final_price = sales_price or 0
#                 price = list_price or sales_price or 0
#                 sale_price = sales_price or 0
#                 discount = round(list_price - sales_price, 2) if list_price and sales_price else "N/A"
#                 currency = (price_block.get('sales') or {}).get('currency', '')
#                 # STOCK
#                 messages = product.get('availability', {}).get('messages', [])
#                 is_in_stock = "TRUE" if any("In Stock" in m for m in messages) else "FALSE"
#                 # DESCRIPTION
#                 raw_desc = product.get('shortDescription', '')
#                 description = clean_html_proper(raw_desc)
#                 # CATEGORY
#                 category = product.get('powerReviewsComponents', {}).get('product', {}).get('category_name', '')
#                 category = category.replace(" > ", "/")
#                 # IMAGES
#                 images = product.get('images', {}).get('large', [])
#                 main_image = images[0]['url'] if images else ''
#                 alt_images = " | ".join([img['url'] for img in images[1:]]) if len(images) > 1 else "N/A"
#                 # SIZE
#                 size = "N/A"
#                 if product.get('variationAttributes'):
#                     size = product['variationAttributes'][0].get('displayValue') or "N/A"
#                 # UPC
#                 upc = "N/A"
#                 pr_variants = product.get("powerReviewsComponents", {}).get("product", {}).get("variants", [])
#                 for v in pr_variants:
#                     if str(v.get("page_id_variant")) == str(product.get("id")):
#                         upc = v.get("upc") or "N/A"
#                         break
#                 # RATINGS
#                 avg_rating = product.get('customRating', {}).get('bvAverageRating') or "N/A"
#                 num_rating = product.get('customRating', {}).get('bvReviewCount') or "N/A"
#                 # SKU
#                 sku = product.get('id')
#                 # INSERT
#                 data = (
#                     "Pet Supermarket",
#                     pid,
#                     name,
#                     "N/A",
#                     description,
#                     category,
#                     main_image,
#                     price,
#                     currency,
#                     sale_price,
#                     final_price,
#                     discount,
#                     "N/A",
#                     is_in_stock,
#                     "N/A",
#                     brand,
#                     "N/A",
#                     mpn,
#                     upc,
#                     sku,
#                     "N/A",
#                     "N/A",
#                     size,
#                     final_price,
#                     alt_images,
#                     product_url,
#                     num_rating,
#                     avg_rating,
#                     hash_key,
#                     url
#                 )
#
#                 cursor.execute(INSERT_QUERY, data)
#
#             conn.commit()
#             print("✅ Done:", hash_key)
#
#         except Exception as e:
#             print("❌ Error:", e)
#
#     conn.close()
#
#
# # -----------------------------
# # RUN
# # -----------------------------
# if __name__ == "__main__":
#     process()
#
#
#
#
#
#
#
#
#
#
#
#
# # import hashlib
# # import os
# # import json
# # import html
# # from parsel import Selector
# # from openpyxl import Workbook
# #
# # def clean_html_proper(raw_html):
# #     sel = Selector(text=raw_html)
# #     parts = []
# #     # 1️⃣ Handle <p> properly (join all text inside it FIRST)
# #     for p in sel.xpath('//p'):
# #         text = " ".join(
# #             [t.strip() for t in p.xpath('.//text()').getall() if t.strip()]
# #         )
# #         if text:
# #             parts.append(text)
# #     # 2️⃣ Handle <li>
# #     for li in sel.xpath('//li'):
# #         text = " ".join(
# #             [t.strip() for t in li.xpath('.//text()').getall() if t.strip()]
# #         )
# #         if text:
# #             parts.append(text)
# #     # 3️⃣ Final join
# #     return " | ".join(parts)
# # # -----------------------------
# # # FOLDERS
# # # -----------------------------
# # PDP_FOLDER = r"D:\Julee\PAGESAVES\pet_supermarket\032026\PDP"
# # VAR_FOLDER = r"D:\Julee\PAGESAVES\pet_supermarket\032026\PDP\variation_pagesave"
# #
# # # -----------------------------
# # # EXCEL SETUP
# # # -----------------------------
# # wb = Workbook()
# # ws = wb.active
# # ws.title = "Data"
# #
# # headers = [
# #     "S.No","Website","PID","Name","Short Description","Description",
# #     "Category","Image URL","Price","Price Currency","Sale Price",
# #     "Final Price","Discount","IsOnSale","IsInStock","Keywords",
# #     "Brand","Manufacturer","MPN","UPC or EAN","SKU","Colour",
# #     "Others","Gender","Size","Varint_Price","Alternate Image URLs",
# #     "Link URL","Num Ratings","Average Ratings","hash_id"
# # ]
# #
# # ws.append(headers)
# #
# # # -----------------------------
# # # LOOP PDP FILES
# # # -----------------------------
# # sno = 1
# #
# # for file in os.listdir(PDP_FOLDER):
# #     if not file.endswith(".html"):
# #         continue
# #     try:
# #         pdp_path = os.path.join(PDP_FOLDER, file)
# #         with open(pdp_path, "r", encoding="utf-8") as f:
# #             pdp_html = f.read()
# #         sel = Selector(text=pdp_html)
# #         # -----------------------------
# #         # MPN FROM JSON-LD
# #         # -----------------------------
# #         mpn = "N/A"
# #         scripts = sel.xpath('//script[@type="application/ld+json"]/text()').getall()
# #         for script in scripts:
# #             try:
# #                 data = json.loads(script)
# #                 if data.get('@type') == 'Product':
# #                     mpn = data.get('mpn', 'N/A')
# #                     break
# #             except:
# #                 pass
# #
# #         # -----------------------------
# #         # VARIANT ID
# #         # -----------------------------
# #         raw_json = sel.xpath('//div[@class="pr-pdp-components"]/@data-pr-pdp-components').get()
# #
# #         if not raw_json:
# #             continue
# #
# #         clean_json = html.unescape(raw_json)
# #         pdp_data = json.loads(clean_json)
# #
# #         # variant_id = pdp_data['product']['variants'][0]['page_id_variant']
# #         product_block = pdp_data.get('product', {})
# #         variants = product_block.get('variants', [])
# #         product_url = product_block.get('url', "")
# #         for var in variants:
# #
# #             variant_id = var.get('page_id_variant')
# #
# #             if not variant_id:
# #                 continue
# #
# #             var_file = os.path.join(VAR_FOLDER, f"{variant_id}.json")
# #
# #             if not os.path.exists(var_file):
# #                 print(f"Variation file missing: {variant_id}")
# #                 continue
# #
# #             with open(var_file, "r", encoding="utf-8") as f:
# #                 var_data = json.load(f)
# #
# #             product = var_data['product']
# #
# #             if product['id'] != variant_id:
# #                 continue
# #
# #             # ✅ FIXED HASH ID
# #             h = hashlib.sha256(product_url.encode()).hexdigest()
# #             num = int(h, 16)
# #             hash_id = str(num)[0:16]
# #
# #             # -----------------------------
# #             # EXTRACT DATA (SAME AS BEFORE)
# #             # -----------------------------
# #             # pid = product['id']
# #             pid = product.get('masterProduct', {}).get('ID')
# #             if not pid:
# #                 pid = product['id']
# #             name = product['productName']
# #             brand = product.get('brand', 'N/A')
# #
# #             # price = product['price']['sales']['value']
# #             currency = product['price']['sales']['currency']
# #
# #             # sale_price = price
# #             # final_price = price
# #             # discount = 0
# #             #
# #             # # IsOnSale
# #             # list_price = product.get('price', {}).get('list')
# #             # if list_price and list_price.get('value'):
# #             #     is_on_sale = "YES"
# #             # else:
# #             #     is_on_sale = "N/A"
# #             is_on_sale = "N/A"
# #             price_block = product.get('price', {})
# #             sales_price = (price_block.get('sales') or {}).get('value')
# #             list_price = (price_block.get('list') or {}).get('value')
# #             # sales_price = price_block.get('sales', {}).get('value')
# #             # list_price = price_block.get('list', {}).get('value')
# #             # Final Price (always sales)
# #             final_price = sales_price if sales_price else "N/A"
# #             # Base Price (MRP)
# #             price = list_price if list_price else sales_price
# #             # Sale Price
# #             # sale_price = sales_price if list_price else "N/A"
# #             sale_price = sales_price
# #             # Discount
# #             if list_price and sales_price:
# #                 discount = round(list_price - sales_price, 2)
# #             else:
# #                 discount = "N/A"
# #
# #             # IsInStock
# #             messages = product.get('availability', {}).get('messages', [])
# #             if any("In Stock" in msg for msg in messages):
# #                 is_in_stock = "TRUE"
# #             else:
# #                 is_in_stock = "FALSE"
# #
# #             # Description
# #             raw_desc = product.get('shortDescription', '')
# #             description = clean_html_proper(raw_desc)
# #
# #             # Category
# #             category = var_data['product']['powerReviewsComponents']['product']['category_name']
# #             category = category.replace(" > ", "/")
# #             # Images
# #             images = product['images']['large']
# #             main_image = images[0]['url']
# #             alt_images = " | ".join([img['url'] for img in images[1:]])
# #             alt_images = alt_images if alt_images else "N/A"
# #             # Size / Color (dynamic)
# #             # product.variationAttributes[0].displayValue
# #             size = product['variationAttributes'][0]['displayValue'] if product['variationAttributes'][0]['displayValue'] else "N/A"
# #
# #             # for attr in product.get('variationAttributes', []):
# #             #     if attr.get('attributeId') == 'size':
# #             #         size = attr.get('displayValue')
# #
# #             # UPC
# #             product_id = product.get("id", "")
# #             variants = product.get("powerReviewsComponents", {}).get("product", {}).get("variants", [])
# #             for v in variants:
# #                 if str(v.get("page_id_variant")) == product_id:
# #                     upc = v.get("upc") if v.get("upc") else "N/A"
# #             sku = product['id']
# #             # upc = var_data['product']['powerReviewsComponents']['product']['variants'][0]['upc']
# #
# #             # Ratings
# #             # avg_rating = product.get('rating', 'N/A')
# #             avg_rating = product.get('customRating', {}).get('bvAverageRating', 'N/A')
# #             num_rating = product.get('customRating', {}).get('bvReviewCount', 'N/A')
# #             if num_rating == "0":
# #                 num_rating = "N/A"
# #             if avg_rating == "0.0":
# #                 avg_rating = "N/A"
# #             # -----------------------------
# #             # WRITE ROW
# #             # -----------------------------
# #             row = [
# #                 sno,
# #                 "petsupermarket.com",
# #                 pid,
# #                 name,
# #                 "N/A",
# #                 description,
# #                 category,
# #                 main_image,
# #                 price,
# #                 currency,
# #                 sale_price,
# #                 final_price,
# #                 discount,
# #                 is_on_sale,
# #                 is_in_stock,
# #                 "N/A",
# #                 brand,
# #                 "N/A",
# #                 mpn,
# #                 upc,
# #                 sku,
# #                 "N/A",
# #                 "N/A",
# #                 "N/A",
# #                 size,
# #                 final_price,
# #                 alt_images,
# #                 product_url,
# #                 num_rating,
# #                 avg_rating,
# #                 hash_id
# #             ]
# #
# #             ws.append(row)
# #             sno += 1
# #         print(f"Processed: {file}")
# #
# #     except Exception as e:
# #         print(f"Error in {file}: {e}")
# #
# # # -----------------------------
# # # SAVE FILE
# # # -----------------------------
# # output_path = r"D:\Julee\PAGESAVES\pet_supermarket\output.xlsx"
# # wb.save(output_path)
# #
# # print("\n✅ Excel Created:", output_path)
#
#
