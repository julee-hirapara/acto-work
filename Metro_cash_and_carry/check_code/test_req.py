import requests

url = "https://www.metrorrl.com/ext/jpm-mas/onboarding/v1/getUserDetails"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Cookie": "***HIDDEN***",
    "Origin": "https://www.metrorrl.com",
    "sec-ch-ua": '"Android WebView";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "x-fp-date": "20260409T075317Z",
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": "***HIDDEN***",
    "X-Requested-With": "in.co.metro.customerappmetro"
}

payload = {
    "type": "phoneNo",
    "phoneNo": "9979329547"
}

response = requests.post(url,
                         # headers=headers,
                         json=payload)

print("Status Code:", response.status_code)
print("Response Body:", response.text)

import requests

url = "https://www.metrorrl.com/ext/jpm-mas/user/is-registered"

params = {
    "mobile": "9033320598"
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Cookie": "***HIDDEN***",
    "sec-ch-ua": '"Android WebView";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "x-fp-date": "20260409T075319Z",
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": "***HIDDEN***",
    "X-Requested-With": "in.co.metro.customerappmetro"
}

response = requests.get(url, headers=headers, params=params)

print("Status Code:", response.status_code)
print("Response Body:", response.text)

import requests

url = "https://www.metrorrl.com/ext/jpm-mas/merchant/login/otp"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Cookie": "***HIDDEN***",
    "Origin": "https://www.metrorrl.com",
    "sec-ch-ua": '"Android WebView";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G965N Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
    "x-fp-date": "20260409T075319Z",
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": "***HIDDEN***",
    "X-Requested-With": "in.co.metro.customerappmetro"
}

payload = {
    "mobile": "9979329547",
    "country_code": "91"
}

response = requests.post(url, headers=headers, json=payload)

print("Status Code:", response.status_code)
print("Response Body:", response.text)