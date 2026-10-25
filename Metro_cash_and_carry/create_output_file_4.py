import json
import db_config_1 as db
from openpyxl import Workbook
from openpyxl.styles import Font
import os
import html
from datetime import datetime
import re


def clean_text(val):
    if not val:
        return None
    val = html.unescape(str(val))
    return " ".join(val.split())


def clean_price(val):
    if not val:
        return None
    return re.sub(r"[^\d.]", "", str(val))


def extract_number(value):
    if value is None:
        return None
    value = str(value)
    match = re.search(r'\d+(\.\d+)?', value)
    if match:
        num = match.group()
        return float(num) if "." in num else int(num)
    return None

def clean_dict(d):
    if not isinstance(d, dict):
        return {}
    return {
        k: clean_text(v) if isinstance(v, str) else v
        for k, v in d.items()
    }

def clean_numeric_dict(d):
    return {
        k: extract_number(v) if isinstance(v, (str, int, float)) else v
        for k, v in d.items()
    }

def clean_list_of_dict(lst):
    try:
        return [clean_dict(i) for i in lst if isinstance(i, dict)]
    except:
        return []

# =========================
# FETCH DATA FROM DB
# =========================
def export_all():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT DISTINCT pincode, city
        FROM {db.product_link_table}
        WHERE status='extracted'
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    for r in rows:
        print(f"\n🚀 Exporting: {r['city']} ({r['pincode']})")
        export_products(r["pincode"], r["city"])


def fetch_products(pincode, city):
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor()
    query = f"""
    SELECT * FROM {db.product_link_table}
    WHERE pincode = %s AND city = %s
    """
    cursor.execute(query, (pincode, city))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"📦 Fetched {len(rows)} rows from DB")
    return rows


def parse_delivery_date(delivery_text):
    try:
        if not delivery_text:
            return None
        # extract date part like "Sat, 18 Apr"
        match = re.search(r"\w{3},\s*(\d{1,2}\s+\w{3})", delivery_text)
        if not match:
            return None
        date_str = match.group(1)  # "18 Apr"
        # add current year
        current_year = datetime.now().year
        full_date = f"{date_str} {current_year}"  # "18 Apr 2026"
        # convert to datetime
        dt = datetime.strptime(full_date, "%d %b %Y")
        # return in DD-MM-YYYY
        # return dt.strftime("%d-%m-%Y")
        return dt.strftime("%Y/%m/%d")
    except Exception:
        return None

# =========================
# TRANSFORM DATA
# =========================
def transform_data(rows):
    output = []
    for row in rows:
        try:
            pdp_json = json.loads(row["pdp_data"]) if row.get("pdp_data") else {}
            # name = row.get("product_name")
            name = clean_text(pdp_json.get("product_name") or row.get("product_name"))
            brand = clean_text(pdp_json.get("brand_name") or row.get("brand_name"))
            stock = clean_text(pdp_json.get("stock"))
            if stock == 'in_stock':
                stock= "In Stock"
            else:
                stock ="Sold Out"
            seller = clean_text(pdp_json.get("seller"))
            description = clean_text(pdp_json.get("description"))
            images_list = pdp_json.get("images")
            if not images_list:
                raw_db_images = row.get("images")
                if raw_db_images:
                    try:
                        # try JSON load first
                        images_list = json.loads(raw_db_images)
                    except:
                        try:
                            # fallback: fix single quotes → double quotes
                            images_list = json.loads(raw_db_images.replace("'", '"'))
                        except:
                            # last fallback: treat as single string
                            images_list = [raw_db_images]
                else:
                    images_list = "N/A"
            # final safety
            if not images_list:
                images_list = "N/A"
            # ✅ Ensure it's always a list
            if isinstance(images_list, str):
                images_list = [images_list]
            # ✅ Extract only URLs if dict format
            final_images = []
            for img in images_list:
                if isinstance(img, dict):
                    url = img.get("url")
                    if url:
                        final_images.append(url)
                elif isinstance(img, str):
                    final_images.append(img)
            # ✅ Convert to pipe-separated string
            images_string = "|".join(final_images) if final_images else "N/A"

            mrp = clean_price(row.get("mrp"))
            retail_price = row.get("rrp")
            # discount = row.get("discount")
            discount_raw = str(row.get("discount", ""))
            match = re.search(r'\d+(\.\d+)?', discount_raw)
            discount = float(match.group()) if match else "N/A"
            row_url = row.get("product_slug")
            pdp_url = "https://www.metrorrl.com/product/"+row_url

            promotions = clean_list_of_dict(pdp_json.get("promotions", []))
            if promotions == []:
                promotions = "N/A"

            raw_tiers = pdp_json.get("quantity_price_tiers", [])
            tiers = [clean_numeric_dict(t) for t in raw_tiers if isinstance(t, dict)]
            # tiers = clean_list_of_dict(raw_tiers) if raw_tiers else []
            # 🔥 ADD THIS
            min_qty = None
            max_qty = None
            if tiers:
                try:
                    min_qty = min(int(t.get("min_qty", 0)) for t in tiers if t.get("min_qty"))
                    max_qty = max(int(t.get("max_qty", 0)) for t in tiers if t.get("max_qty"))
                except:
                    min_qty = None
                    max_qty = None
            # keep your old behavior
            if tiers == []:
                tiers = "N/A"

            delivery_text = pdp_json.get("delivery", None)
            delivery = parse_delivery_date(delivery_text)
            created_at = row.get("created_at")
            if created_at:
                try:
                    dt = datetime.strptime(str(created_at), "%Y-%m-%d %H:%M:%S")
                    formatted_dt = dt.strftime("%Y-%m-%dT%H:%M:%S") + ":000"
                except:
                    formatted_dt = created_at
            else:
                formatted_dt = None
            # 🔥 ADD THIS
            if stock == "Sold Out":
                mrp = "N/A"
                retail_price = "N/A"
                discount = "N/A"
                delivery = "N/A"
                promotions = "N/A"
            full_path = row.get("pagesave")
            file_name = os.path.basename(full_path) if full_path else None
            net_quantity = row.get("net_quantity").replace(" ", "")
            if stock == "In Stock":
                stock = "True"
            else:
                stock = "False"
            output.append({
                "platform": "Metro Wholesale",
                "pincode": row.get("pincode"),
                "city": row.get("city"),
                "state": row.get("state"),
                "item_code": row.get("item_code"),
                "name": name,
                "brand": brand,
                "weight": row.get("weight"),
                "net_quantity": net_quantity,
                "url": pdp_url,
                "images": images_string,
                "price": retail_price,
                "discount": discount,
                "mrp": mrp,
                "availability": stock,
                "promotions": promotions,
                "description": description,
                "price_quantity_tiers": tiers,
                "minimum_quantity": min_qty,
                "maximum_quantity": max_qty,
                "country_of_origin": row.get("country_of_origin"),
                "store_id": row.get("store_id"),
                "arrival_date": delivery,
                # "seller": seller,
                "scrap_date_time": formatted_dt,
                "pagesave": file_name
            })
        except Exception as e:
            print("⚠️ Error processing row:", e)
    return output


def save_to_excel(data, pincode, city):
    file_path = os.path.join(db.RESULT_PATH, f"{city}_{pincode}.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"
    headers = [
        "sr.no","platform", "pincode", "city", "state", "item_code", "name", "brand",
        "weight", "net_quantity", "url", "images", "price", "discount", "mrp",
        "availability", "promotions", "description", "price_quantity_tiers",
        "minimum_quantity", "maximum_quantity", "country_of_origin", "store_id",
        "arrival_date", "scrap_date_time", "pagesave"
    ]
    # Header bold
    bold_font = Font(bold=True)
    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        ws.cell(row=1, column=col_num).font = bold_font

    for idx, row in enumerate(data, start=1):
        ws.append([
            idx,
            *[
                json.dumps(row.get(col), ensure_ascii=False)
                if isinstance(row.get(col), (list, dict))
                else clean_text(row.get(col)) if row.get(col)
                else "N/A"
                for col in headers[1:]
            ]
        ])
    wb.save(file_path)
    print(f"✅ Excel saved: {file_path}")


def export_products(pincode, city):
    rows = fetch_products(pincode, city)
    if not rows:
        print("❌ No data found")
        return
    data = transform_data(rows)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    save_to_excel(data, pincode, city)


if __name__ == "__main__":
    export_all()
