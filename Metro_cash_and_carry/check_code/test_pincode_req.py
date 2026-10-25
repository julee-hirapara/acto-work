# ------------------------- pincode request --------------------------------------
import requests

url = "https://www.metrorrl.com/api/service/application/logistics/v1.0/localities/pincode/380001"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Authorization": "Bearer ***HIDDEN***",
    "User-Agent": "Mozilla/5.0",
    "x-currency-code": "INR",
    "x-fp-date": "20260410T045613Z",
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": "***HIDDEN***",
    "x-location-detail": '{"country":"INDIA","country_iso_code":"IN","pincode":"380001","state_code":"24","city":"Ahmedabad","state":"Gujarat"}'
}

response = requests.get(url, headers=headers)

print(response.status_code)
print(response.text)

#------------- category request --------------------------
import requests

url = "https://www.metrorrl.com/undefined"

headers = {
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    # "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://www.metrorrl.com/?apkVersion=101501&platform=android",
    "sec-ch-ua": "\"Android WebView\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": "\"Android\"",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36"
}
import requests
import json
import urllib.parse

# Editable location object
location = {
    "country": "INDIA",
    "country_iso_code": "IN",
    "pincode": "110001",
    "state_code": "07",
    "city": "Central Delhi",
    "state": "Delhi"
}

# Encode back to cookie format
encoded_location = urllib.parse.quote(json.dumps(location))

cookies = {
    # "anonymous_id": "***HIDDEN***",
    # "old_browser_anonymous_id": "***HIDDEN***",
    # "_ga": "GA1.1.118439135.1775732663",
    # "f.session": "s%3AhO75Cz3MrJ6SgN_LczTOAHdiMrV2amlw.ux%2F5bAgsevdW0LpI0f4HkpQx6So3vpUqc214TAm8Pco",
    # "x_jmp_session": "vGX3xCX_a4lH1qCu1vJSn",
    "app_location_details": encoded_location
}

# # Example request
# url = "https://www.metrorrl.com/api/service/application/logistics/v1.0/localities/pincode/380001"
#
# response = requests.get(url, cookies=cookies)
# print(response.status_code)
# print(response.text)
# cookies = {
#     "anonymous_id": "***HIDDEN***",
#     "old_browser_anonymous_id": "***HIDDEN***",
#     "_ga": "GA1.1.118439135.1775732663",
#     "f.session": "s%3AhO75Cz3MrJ6SgN_LczTOAHdiMrV2amlw.ux%2F5bAgsevdW0LpI0f4HkpQx6So3vpUqc214TAm8Pco",
#     "x_jmp_session": "vGX3xCX_a4lH1qCu1vJSn",
#     "app_location_details": "%7B%22country%22%3A%22INDIA%22%2C%22country_iso_code%22%3A%22IN%22%2C%22pincode%22%3A%22380001%22%2C%22state_code%22%3A%2224%22%2C%22city%22%3A%22Ahmedabad%22%2C%22state%22%3A%22Gujarat%22%7D"
# }

response = requests.get(url, headers=headers, cookies=cookies)

print("[110001] Status Code:", response.status_code)

# Since it's an image request, use content instead of text
with open("output_image.html", "w", encoding='utf-8') as f:
    f.write(response.text)


# ------------------------------- brand request just get slug in response ----------------------------

import requests
import json
import urllib.parse

url = "https://www.metrorrl.com/api/service/application/catalog/v1.0/brands/maggi/"

# Editable location (change pincode here 👇)
location = {
    "country": "INDIA",
    "country_iso_code": "IN",
    "pincode": "380001",
    "state_code": "24",
    "city": "Ahmedabad",
    "state": "Gujarat"
}

# Encode location for cookie
encoded_location = urllib.parse.quote(json.dumps(location))

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Authorization": "Bearer ***HIDDEN***",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "x-currency-code": "INR",
    "x-fp-date": "20260410T050409Z",
    "x-fp-sdk-version": "1.9.4-13",
    # "x-fp-signature": "***HIDDEN***",
    "x-location-detail": json.dumps(location)
}

cookies = {
    "anonymous_id": "***HIDDEN***",
    "old_browser_anonymous_id": "***HIDDEN***",
    "_ga": "GA1.1.118439135.1775732663",
    "f.session": "s%3AhO75Cz3MrJ6SgN_LczTOAHdiMrV2amlw.ux%2F5bAgsevdW0LpI0f4HkpQx6So3vpUqc214TAm8Pco",
    "x_jmp_session": "vGX3xCX_a4lH1qCu1vJSn",
    "app_location_details": encoded_location
}

response = requests.get(url, headers=headers, cookies=cookies)

print("Status:", response.status_code)
print(response.text)


# --------------------------- pl page request category wise --------------------

import requests
import json
import urllib.parse

# Base URL
url = "https://www.metrorrl.com/ext/catalogueDiscovery/api/search/v1.0/collections/cleaning--hygiene/items/"

# Query parameters (decoded for readability)
params = {
    "f": "is_available:true:::search:true:::source:plp:::app_user_id:69d759119a8fb019a6c5b65d",
    "page_id": "",
    "page_size": "9"
}

# Editable location 👇
location = {
    "country": "INDIA",
    "country_iso_code": "IN",
    "pincode": "380001",
    "state_code": "24",
    "city": "Ahmedabad",
    "state": "Gujarat"
}

# Encode for cookie
encoded_location = urllib.parse.quote(json.dumps(location))

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Authorization": "Bearer ***HIDDEN***",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "x-currency-code": "INR",
    "x-fp-date": "20260410T051646Z",
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": "***HIDDEN***",
    "x-location-detail": json.dumps(location)
}

cookies = {
    "anonymous_id": "***HIDDEN***",
    "old_browser_anonymous_id": "***HIDDEN***",
    "_ga": "GA1.1.118439135.1775732663",
    "f.session": "s%3AhO75Cz3MrJ6SgN_LczTOAHdiMrV2amlw.ux%2F5bAgsevdW0LpI0f4HkpQx6So3vpUqc214TAm8Pco",
    "x_jmp_session": "vGX3xCX_a4lH1qCu1vJSn",
    "app_location_details": encoded_location
}

# Make request
response = requests.get(url, headers=headers, cookies=cookies, params=params)

print("Status:", response.status_code)
print(response.text)


# ----------------------- PDP page request ---------------------------------
import requests
import json
import urllib.parse

# Product URL
url = "https://www.metrorrl.com/ext/catalogueDiscovery/api/search/v1.0/products/harpic-power-plus-refreshing-marine-toilet-cleaner-500-ml-lkpjts-7544545/"

# Editable location 👇
location = {
    "country": "INDIA",
    "country_iso_code": "IN",
    "pincode": "380001",
    "state_code": "24",
    "city": "Ahmedabad",
    "state": "Gujarat"
}

# Encode for cookie
encoded_location = urllib.parse.quote(json.dumps(location))

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Authorization": "Bearer ***HIDDEN***",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "x-currency-code": "INR",
    "x-fp-date": "20260410T052102Z",
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": "***HIDDEN***",
    "x-location-detail": json.dumps(location),
    "X-Requested-With": "in.co.metro.customerappmetro"
}

cookies = {
    "anonymous_id": "***HIDDEN***",
    "old_browser_anonymous_id": "***HIDDEN***",
    "_ga": "GA1.1.118439135.1775732663",
    "f.session": "s%3AhO75Cz3MrJ6SgN_LczTOAHdiMrV2amlw.ux%2F5bAgsevdW0LpI0f4HkpQx6So3vpUqc214TAm8Pco",
    "x_jmp_session": "vGX3xCX_a4lH1qCu1vJSn",
    "app_location_details": encoded_location
}

# Make request
response = requests.get(url, headers=headers, cookies=cookies)

print("Status:", response.status_code)
print(response.text)

# ------------------------ different unit wise price ----------------------------

import requests
import json
import urllib.parse

# Base URL
url = "https://www.metrorrl.com/api/service/application/cart/v1.0/available-ladder-prices"

# Query parameters (cleaned)
params = {
    "slug": "harpic-power-plus-refreshing-marine-toilet-cleaner-500-ml-lkpjts-7544545",
    "store_id": "458"
}

# Editable location 👇
location = {
    "country": "INDIA",
    "country_iso_code": "IN",
    "pincode": "380001",
    "state_code": "24",
    "city": "Ahmedabad",
    "state": "Gujarat"
}

# Encode location for cookie
encoded_location = urllib.parse.quote(json.dumps(location))

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Authorization": "Bearer ***HIDDEN***",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "x-currency-code": "INR",
    "x-fp-date": "20260410T052103Z",
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": "***HIDDEN***",
    "x-location-detail": json.dumps(location)
}

cookies = {
    "anonymous_id": "***HIDDEN***",
    "old_browser_anonymous_id": "***HIDDEN***",
    "_ga": "GA1.1.118439135.1775732663",
    "f.session": "s%3AhO75Cz3MrJ6SgN_LczTOAHdiMrV2amlw.ux%2F5bAgsevdW0LpI0f4HkpQx6So3vpUqc214TAm8Pco",
    "x_jmp_session": "vGX3xCX_a4lH1qCu1vJSn",
    "app_location_details": encoded_location
}

# Make request
response = requests.get(url, headers=headers, cookies=cookies, params=params)

print("Status:", response.status_code)
print(response.text)

# ------------------------ Expected delivery data -------------------------------
import requests
import json
import urllib.parse

url = "https://www.metrorrl.com/api/service/application/logistics/v1.0/"

# Editable location 👇
location = {
    "country": "INDIA",
    "country_iso_code": "IN",
    "pincode": "380001",
    "state_code": "24",
    "city": "Ahmedabad",
    "state": "Gujarat"
}

# Encode location for cookie
encoded_location = urllib.parse.quote(json.dumps(location))

headers = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Authorization": "Bearer ***HIDDEN***",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "Origin": "https://www.metrorrl.com",
    "x-currency-code": "INR",
    "x-fp-date": "20260410T052103Z",
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": "***HIDDEN***",
    "x-location-detail": json.dumps(location),
    "X-Requested-With": "i"
}

cookies = {
    "anonymous_id": "***HIDDEN***",
    "old_browser_anonymous_id": "***HIDDEN***",
    "_ga": "GA1.1.118439135.1775732663",
    "f.session": "s%3AhO75Cz3MrJ6SgN_LczTOAHdiMrV2amlw.ux%2F5bAgsevdW0LpI0f4HkpQx6So3vpUqc214TAm8Pco",
    "x_jmp_session": "vGX3xCX_a4lH1qCu1vJSn",
    "app_location_details": encoded_location
}

# Request payload (body)
payload = {
    "to_pincode": location["pincode"],  # 👈 dynamic
    "location_details": [
        {
            "fulfillment_id": 458,
            "from_pincode": "382210",
            "articles": [
                {
                    "category": {
                        "level": "l3",
                        "id": 1009
                    }
                }
            ]
        }
    ]
}

# Make POST request
response = requests.post(url, headers=headers, cookies=cookies, json=payload)

print("Status:", response.status_code)
print(response.text)