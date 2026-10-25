import json

import requests

url = "https://www.metrorrl.com/ext/catalogueDiscovery/api/search/v1.0/collections/cleaning--hygiene/items/"

params = {
    # "f": "is_available:true:::search:true:::source:plp:::app_user_id:69d759119a8fb019a6c5b65d",
    "filters": "false",
    "page_id": "1",
    "page_size": "9"
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Authorization": "Bearer ***HIDDEN***",
    "Connection": "keep-alive",
    # "Cookie": "***HIDDEN***",
    "sec-ch-ua": '"Android WebView";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "x-currency-code": "INR",
    "x-fp-date": "20260409T101127Z",
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": "***HIDDEN***",
    "x-location-detail": '{"country":"INDIA","country_iso_code":"IN","pincode":"380001","state_code":"24","city":"Ahmedabad","state":"Gujarat"}',
    "X-Requested-With": "in.co.metro.customerappmetro"
}

response = requests.get(url,
                        headers=headers,
                        params=params)

print("Status Code:", response.status_code)
print("Response JSON:", json.dumps(response.json()))