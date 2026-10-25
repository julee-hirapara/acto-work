import os
import json
import pandas as pd
import re
from parsel import Selector
from datetime import datetime
import db_config_1 as db


# -----------------------------
# CLEAN DATAFRAME
# -----------------------------
def clean_dataframe(df):
    df = df.fillna("N/A")

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
            )
    return df


# -----------------------------
# EXTRACT FUNCTION
# -----------------------------
def extract_data(html_text, api_json):

    sel = Selector(text=html_text)

    # ---------- SEO ----------
    seo_raw = sel.xpath('//script[@type="application/ld+json"]/text()').get()
    seo = json.loads(seo_raw) if seo_raw else {}

    # ---------- PROVIDER PROPS ----------
    provider_raw = sel.xpath('//script[contains(text(),"__PROVIDER_PROPS__")]/text()').get()
    provider_data = {}

    if provider_raw:
        match = re.search(r'window\.__PROVIDER_PROPS__\s*=\s*(\{.*\})', provider_raw, re.DOTALL)
        if match:
            raw_json = match.group(1).replace(':undefined', ':null')
            try:
                provider_data = json.loads(raw_json)
            except:
                pass

    # ---------- ADDRESS ----------
    address_data = seo.get("address") or {}

    address = address_data.get("streetAddress", "N/A")
    post_code = address_data.get("postalCode", "N/A")
    city = address_data.get("addressLocality", "N/A")

    # ---------- OPENING HOURS ----------
    opening_hours = {}
    for spec in seo.get("openingHoursSpecification", []):
        for d in spec.get("dayOfWeek", []):
            opening_hours[d.lower()] = f"{spec.get('opens')}-{spec.get('closes')}"

    # ---------- API ----------
    data = api_json.get("data", {})

    vendor_id = data.get("id")

    vendor_common = {
        "vendor_id": vendor_id,
        "url": seo.get("url"),
        "restaurant_name": seo.get("name"),
        "restaurant_image": (seo.get("image") or [None])[0],
        "cuisine": ", ".join(seo.get("servesCuisine", [])),
        "currency": "RM",

        "country_code": provider_data.get("countryConfig"),
        "opening_hours": json.dumps(opening_hours),
        "phone_number": seo.get("telephone"),

        "address": address,
        "post_code": post_code,
        "city": city,

        "latitude": seo.get("geo", {}).get("latitude"),
        "longitude": seo.get("geo", {}).get("longitude"),

        "rating": seo.get("aggregateRating", {}).get("ratingValue"),
        "rating_count": seo.get("aggregateRating", {}).get("ratingCount"),

        "brand": provider_data.get("brand"),
        "minimum_order_value": (
            (data.get("discounts") or [{}])[0].get("minimum_order_value")
        )
    }

    # ---------- MENU ----------
    rows = []
    menus = data.get("menus", [])

    for menu in menus:
        for category in menu.get("menu_categories", []):

            category_name = category.get("name")

            for product in category.get("products", []):

                tags = ", ".join(
                    [t for t in (product.get("tags") or []) if not t.startswith("system:")]
                ) or "N/A"

                for var in product.get("product_variations", []):

                    # price = var.get("price") or "N/A"
                    price = var.get("price", 0) or 0
                    mrp = var.get("price_before_discount", 0) or 0
                    discount = 0
                    if mrp and price and mrp > price:
                        discount = mrp - price  # absolute discount
                    # format to 2 decimal places
                    price = round(price, 2) if price else "N/A"
                    mrp = round(mrp, 2) if mrp else "N/A"
                    discount = round(discount, 2) if discount else "N/A"
                    row = {
                        **vendor_common,
                        "category_name": category_name,
                        "menu_name": product.get("name"),
                        "price": price,
                        "mrp": mrp,
                        "discount": discount,
                        "menu_image": product.get("file_path"),
                        "description": product.get("description"),
                        "tags": tags
                    }

                    rows.append(row)

    return rows


# -----------------------------
# MAIN
# -----------------------------
def main():

    HTML_FOLDER = fr"{db.PDP_PAGESAVE}\html_pages"
    JSON_FOLDER = fr"{db.PDP_PAGESAVE}\json_pages"

    all_rows = []

    files = os.listdir(JSON_FOLDER)

    for file in files:
        try:
            code = file.replace(".json", "")

            json_path = os.path.join(JSON_FOLDER, file)
            html_path = os.path.join(HTML_FOLDER, f"{code}.html")

            if not os.path.exists(html_path):
                print(f"❌ Missing HTML for {code}")
                continue

            # LOAD FILES
            with open(json_path, "r", encoding="utf-8") as f:
                api_json = json.load(f)

            with open(html_path, "r", encoding="utf-8") as f:
                html_text = f.read()

            # EXTRACT
            rows = extract_data(html_text, api_json)

            if rows:
                all_rows.extend(rows)

            print(f"✅ Done: {code}")

        except Exception as e:
            print(f"❌ Error {file}: {e}")

    # -----------------------------
    # SAVE EXCEL
    # -----------------------------
    if all_rows:
        df = pd.DataFrame(all_rows)

        # CLEAN
        df = clean_dataframe(df)

        # ADD SERIAL NUMBER
        df.insert(0, "sr. no", range(1, len(df) + 1))
        # FILL EMPTY VALUES
        df = df.fillna("N/A")
        # SAVE
        with pd.ExcelWriter(
            "final_output.xlsx",
            engine="xlsxwriter",
            engine_kwargs={"options": {"strings_to_urls": False}}
        ) as writer:
            df.to_excel(writer, index=False)

        print("🎉 Excel created: final_output.xlsx")

    else:
        print("❌ No data found")


# -----------------------------
if __name__ == "__main__":
    main()