from curl_cffi import requests
from datetime import datetime, timezone
import hmac
import hashlib

def get_fp_date():
    now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%dT%H%M%SZ")


def generate_metro_signature(secret_key, method, path, fp_date, body=""):
    body_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
    signing_string = f"{method.upper()}\n{path}/\n\n{fp_date}\n{body_hash}"
    signature = hmac.new(
        secret_key.encode('utf-8'),
        signing_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"v1.1:{signature}"

pincode = "380001"
path = f"/api/service/application/logistics/v1.0/localities/pincode/{pincode}"
current_fp_date = get_fp_date()
secret = "***HIDDEN***"
new_sig = generate_metro_signature(secret, "GET", path, current_fp_date)
print(new_sig)

url = f"https://www.metrorrl.com/api/service/application/logistics/v1.0/localities/pincode/{pincode}"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
    "Authorization": "Bearer ***HIDDEN***",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Linux; Android 15; moto g45 5G Build/V1UGS35H.75-14-9-1; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/146.0.7680.177 Mobile Safari/537.36",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Android WebView";v="146"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "x-currency-code": "INR",
    "x-fp-date": current_fp_date,
    "x-fp-sdk-version": "1.9.4-13",
    "x-fp-signature": new_sig,
    "x-location-detail": '{"country_iso_code":"IN"}',
    "X-Requested-With": "in.co.metro.customerappmetro"
}

cookies  = {
    "anonymous_id": "***HIDDEN***",
    "old_browser_anonymous_id": "***HIDDEN***",
    "_ga": "GA1.1.1935749978.1775732774",
    "_clck": "1j5yvys^2^g52^0^2290",
    "f.session": "s:DQ2J4mo6WZQzBXNT4W2LY95aiIYAba6X.dpV9V/LM79WVDobfLlKOVVv3scHXHUILvmeyk2+/cKc",
    "x_jmp_session": "AtoWjnhpBATMPom2KMobt",
    "_ga_01PYHVEWE6": "GS2.1.s1775732773$o1$g1$t1775732831$j2$l0$h0",
    "_clsk": "1ccvrwn^1775732832790^3^1^l.clarity.ms/collect"
}

response = requests.get(url,
                        headers=headers,
                        # cookies=cookies,
                        impersonate='chrome101'
                        )

print(response.status_code)
print(response.text)