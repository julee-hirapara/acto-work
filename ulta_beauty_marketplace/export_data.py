import db_config as db
import pandas as pd
import ftfy
import unicodedata
from unidecode import unidecode

column_order = ["S.No.",
"Website",
"PID",
"Name",
"Short Description",
"Description",
"Category",
"Image URL",
"Price",
"Price Currency",
"Sale Price",
"Final Price",
"Discount",
"IsOnSale",
"IsInStock",
"Keywords",
"Brand",
"Manufacturer",
"MPN",
"UPC or EAN",
"SKU",
"Colour",
"Others",
"Gender",
"Size",
"Varint_Price",
"Alternate Image URLs",
"Link URL",
"Num Ratings",
"Average Ratings",
"hash_id",
"page_save_id"]


def clean_text(text: str) -> str:
    if pd.isna(text):  # Handle nulls first
        return "N/A"
    try:
        # Convert to string to be safe
        text = str(text)
        text = ftfy.fix_text(text)
        text = unicodedata.normalize("NFC", text)
        text = unidecode(text)
        return text.strip()
    except Exception as e:
        print(f"Error processing text: {e}")
        return str(text)

def make_page_id(url):
    pdp_id = url.split("?")[0].split("-")[-1]
    sku_id = url.split("?sku=")[-1]
    return f"{pdp_id}_{sku_id}"

data_collection = db.mongo_db[db.pdp_table_name]
data = data_collection.find({}, {"_id":0})
df = pd.DataFrame(data)
df['Category'] = df['Category'].str.strip()
df['Category'] = df['Category'].replace("", None)
df['page_save_id'] = df['Link URL'].apply(make_page_id)
df.rename(columns={'short_description':"Short Description",
                   'Color':"Colour",
                   'Other':"Others"
                   }, inplace=True)
# df.drop('_id', axis=1, inplace=True)
for col in ['Category', 'Name', 'Brand', "Short Description", "Others"]:
    df[col] = df[col].apply(clean_text)
df['IsInStock'] = df['IsInStock'].replace("True", "TRUE")
df['IsInStock'] = df['IsInStock'].replace("False", "FALSE")
df.insert(0,"S.No.",  range(1, len(df)+1))
df.replace(r'\s+', ' ', regex=True, inplace=True)
df = df.fillna("N/A")
price_mask = (
    (df["Price"].notna() & (df["Price"] != "N/A")) |
    (df["Final Price"].notna() & (df["Final Price"] != "N/A")) |
    (df["Sale Price"].notna() & (df["Sale Price"] != "N/A"))
)
currency_mask = (df["Price Currency"].isna() | (df["Price Currency"] == "") | (df["Price Currency"] == "N/A"))

df.loc[price_mask & currency_mask, "Price Currency"] = "USD"
df = df[column_order]
df.to_excel("ulta-beauty_20260703.xlsx", index=False, engine='openpyxl')
df.to_csv("ulta-beauty_20260703.csv", index=False, encoding="utf-8-sig")
print("data exported....")

