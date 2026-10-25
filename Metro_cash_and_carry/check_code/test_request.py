# import requests
#
# url = "https://www.metrorrl.com/api/service/application/logistics/v1.0/pincode/110001"
# # url = "https://www.metrorrl.com/api/service/application/logistics/v1.0/pincode/380001"
#
# headers = {
#     "Accept": "application/json, text/plain, */*",
#     "Accept-Encoding": "gzip, deflate, br",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Authorization": "Bearer ***HIDDEN***",
#     "Connection": "keep-alive",
#     # "Cookie": "***HIDDEN***",
#     # "sec-ch-ua": '"Android WebView";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
#     # "sec-ch-ua-mobile": "?1",
#     # "sec-ch-ua-platform": '"Android"',
#     # "Sec-Fetch-Dest": "empty",
#     # "Sec-Fetch-Mode": "cors",
#     # "Sec-Fetch-Site": "same-origin",
#     "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
#     # "x-currency-code": "INR",
#     "x-fp-date": "20260409T075347Z",
#     "x-fp-sdk-version": "1.9.4-13",
#     # "x-fp-signature": "***HIDDEN***",
#     # "x-location-detail": '{"country_iso_code":"IN","country":"INDIA","pincode":"110001","state_code":"07","city":"Central Delhi","state":"Delhi"}',
#     "X-Requested-With": "in.co.metro.customerappmetro",
#     "x-fp-signature": "***HIDDEN***",
#     # "x-location-detail": '{"country":"INDIA","country_iso_code":"IN","pincode":"380001","state_code":"24","city":"Ahmedabad","state":"Gujarat"}',
#
# }
# # from curl_cffi import requests
# proxy = {
#    "http": f'http://***HIDDEN***:super=true@proxy.scrape.do:8080',
#    "https": f'http://***HIDDEN***:super=true@proxy.scrape.do:8080',
# }
# response = requests.get(url,
#                         proxies=proxy,
#                         verify=False,
#                         # headers=headers
#                         )
# # print("response header : ", response.headers)
# # print("-------------------------------------------------------")
# # print("response cookies :", response.cookies)
# # print("-------------------------------------------------------")
# print("Status Code:", response.status_code)
# # print("-------------------------------------------------------")
# # print("Response Body:", response.text)

import requests

url = "https://www.metrorrl.com/undefined"

headers = {
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    # "Cookie": "***HIDDEN***",
    "Referer": "https://www.metrorrl.com/",
    "sec-ch-ua": '"Android WebView";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "X-Requested-With": "in.co.metro.customerappmetro"
}

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)
with open("categories.html", "w", encoding='utf-8') as f:
    f.write(response.text)
# print("Response Body:", response.text)

import re
import json

# html = open("file.html", "r", encoding="utf-8").read()
html = response.text

# find all gallery_image blocks
pattern = r'"type":"gallery_image".*?"block_title":\{"type":"text","value":"(.*?)"\}.*?"block_link":\{"type":"url","value":"(.*?)"\}'
matches = re.findall(pattern, html)

data = []

for title, url in matches:
    # clean url
    url = url.replace("\\u002F", "/")

    # extract slug
    slug = None
    if "/collection/" in url:
        slug = url.split("/collection/")[1].split("/")[0]

    data.append({
        "name": title,
        "url": url,
        "slug": slug
    })

print(json.dumps(data, indent=2))