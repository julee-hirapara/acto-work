import os.path
import re
from parsel import Selector
import pandas as pd
import requests
import urllib.parse
import json
import time
import db_config_1 as db

# Load Excel file
file_path = "City_Pincodes.xlsx"   # change this to your file path
df = pd.read_excel(file_path)
# Output list
results = []
# Base headers (keep minimal unless required)
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

# Loop through each row
for index, row in df.iterrows():
    city = str(row["City"])
    if city == "Chennai":
        break
    pincode = str(row["Pincode"])
    state_code = str(row["state_code"])
    state = str(row["state"])

    # Create location dictionary
    location_data = {
        "country": "INDIA",
        "country_iso_code": "IN",
        "pincode": pincode,
        "state_code": state_code,
        "city": city,
        "state": state
    }
    # Convert to JSON string
    location_json = json.dumps(location_data)
    # URL encode it
    encoded_location = urllib.parse.quote(location_json)
    # Build cookies
    cookies = {
        "app_location_details": encoded_location
    }
    file_path = os.path.join(db.Count_PAGESAVE, f"{pincode}.html")

    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as f:
                html = f.read()
        else:
            response = requests.get(
                "https://www.metrorrl.com/products/",
                headers=headers,
                cookies=cookies,
                timeout=10
            )
            item_total = None
            location_details = None
            if response.status_code == 200:
                print(f"{city} ({pincode}) -> {response.status_code}")
                with open(file_path, "w", encoding='utf-8') as f:
                    f.write(response.text)
                html = response.text
        # Parse HTML
        sel = Selector(html)

        script_text = sel.xpath(
            "//script[contains(text(),'__INITIAL_STATE__')]/text()"
        ).get()
        if script_text:
            match = re.search(
                r'window\.__INITIAL_STATE__\s*=\s*(\{.*\})\s*;',
                script_text,
                re.DOTALL
            )
            if match:
                json_text = match.group(1)
                # Fix possible JS issues
                json_text = json_text.replace("undefined", "null")
                data = json.loads(json_text)
                # Extract values safely
                item_total = (
                    data.get("productListingPage", {})
                    .get("productlists", {})
                    .get("page", {})
                    .get("item_total")
                )
                print(f"pincode ::: {pincode} || item_total ::: {item_total} ")
                location_details = (
                    data.get("appmeta", {})
                    .get("appconfig", {})
                    .get("location_details")
                )
        # Small delay to avoid blocking
        time.sleep(1)
        # Store results
        results.append({
            "city": city,
            "pincode": pincode,
            "state": state,
            "item_total": item_total,
            "location_details": json.dumps(location_details) if location_details else None
        })
    except Exception as e:
        print(f"Error for {city} ({pincode}): {e}")


# Save final output
output_file = "output_results.xlsx"
pd.DataFrame(results).to_excel(output_file, index=False)
print("✅ Done! Data saved to", output_file)

