import pandas as pd
import db_config as db
import os

url = os.path.join(db.input_file_path, "jn-bk_47321-product-analysis-from-q-commerce-poc.xlsx")

df = pd.read_excel(
    url,
    sheet_name="Flipkart Grocery",
    skiprows=1
)

print(df.head())
# Normalize headers
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

def clean(val):
    return "N/A" if pd.isna(val) else str(val).strip()

def is_separator_row(row):
    brand_missing = pd.isna(row.get("brand")) or clean(row["brand"]) == "N/A"
    url_missing = pd.isna(row.get("product_url")) or clean(row["product_url"]) == "N/A"
    return row.isna().all() or (brand_missing and url_missing)

final_rows = []
i = 0
n = len(df)

while i < n:
    while i < n and is_separator_row(df.iloc[i]):
        i += 1
    if i >= n:
        break

    base_row = df.iloc[i]
    i += 1

    competitors = []
    while i < n and not is_separator_row(df.iloc[i]):
        competitors.append(df.iloc[i])
        i += 1

    base_data = {
        "base_brand": clean(base_row["brand"]),
        "base_targeted_sku": clean(base_row["targetd_sku"]),
        "base_product_name": clean(base_row["product_name"]),
        "base_url": clean(base_row["product_url"]),
        "base_sku": clean(base_row["sku"]),
        "base_gramage": clean(base_row["gramage"]),
    }

    if not competitors:
        final_rows.append({
            **base_data,
            "competitor_brand": "N/A",
            "competitor_targeted_sku": "N/A",
            "competitor_product_name": "N/A",
            "competitor_url": "N/A",
            "competitor_sku": "N/A",
            "competitor_gramage": "N/A",
        })
    else:
        for comp_row in competitors:
            final_rows.append({
                **base_data,
                "competitor_brand": clean(comp_row["brand"]),
                "competitor_targeted_sku": clean(comp_row["targetd_sku"]),
                "competitor_product_name": clean(comp_row["product_name"]),
                "competitor_url": clean(comp_row["product_url"]),
                "competitor_sku": clean(base_row["sku"]),
                "competitor_gramage": clean(comp_row["gramage"]),
            })

final_df = pd.DataFrame(final_rows)
# --- Availability flags ---
final_df["client_available"] = final_df["base_url"].apply(
    lambda x: "AVAILABLE" if x != "N/A" and x != "" else "NOT_AVAILABLE"
)

final_df["competitor_available"] = final_df["competitor_url"].apply(
    lambda x: "AVAILABLE" if x != "N/A" and x != "" else "NOT_AVAILABLE"
)

# --- Scrape decision ---
final_df["scrape_required"] = final_df.apply(
    lambda r: "YES"
    if r["client_available"] == "AVAILABLE"
       or r["competitor_available"] == "AVAILABLE"
    else "NO",
    axis=1
)
excel_file_path = os.path.join(db.input_file_path, "sample_fkgrocery_comp_data.xlsx")
final_df.to_excel(excel_file_path, index=False)

# -------- CREATE BASE-ONLY FILE --------

base_df = final_df[
    [
        "base_brand",
        "base_targeted_sku",
        "base_product_name",
        "base_url",
        "base_sku",
        "base_gramage",
        "client_available",
        "scrape_required",
    ]
].drop_duplicates()

# Rename columns to match required output
base_df = base_df.rename(
    columns={
        "base_brand": "brand",
        "base_targeted_sku": "targeted_sku",
        "base_product_name": "product_name",
        "base_url": "url",
        "base_sku": "sku",
        "base_gramage": "gramage",
    }
)

# Save second Excel file
base_excel_path = os.path.join(
    db.input_file_path, "sample_fkgrocery_product_data.xlsx"
)

base_df.to_excel(base_excel_path, index=False)

print(f"Product Base-only file created: {base_excel_path}")
