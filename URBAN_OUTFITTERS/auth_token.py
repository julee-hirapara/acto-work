import json
import requests

def get_auth_token():
    with open("token_data.json", "r", encoding='utf-8') as f:
        token_data = json.load(f)
    # ✅ Extract tokens
    auth_token = token_data.get("authToken")
    reauth_token = token_data.get("reauthToken")

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Origin': 'https://www.urbanoutfitters.com',
        # 'Referer': 'https://www.urbanoutfitters.com/shop/out-from-under-bec-low-rise-mini-skort',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'authorization': 'Bearer ***HIDDEN***',
        'baggage': 'sentry-environment=production,sentry-release=slipstream%404.39.1,sentry-public_key=***HIDDEN***,sentry-trace_id=30bde788ce73480290bfb69e9daa8c93,sentry-org_id=39832,sentry-transaction=%2Fshop%2F%3Aslug(%5Ba-zA-Z0-9_-%5D%2B),sentry-sampled=false,sentry-sample_rand=0.7775300365610607,sentry-sample_rate=0.01',
        'content-type': 'application/json',
        'sec-ch-device-memory': '8',
        'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Chromium";v="146.0.7680.165", "Not-A.Brand";v="24.0.0.0", "Google Chrome";v="146.0.7680.165"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sentry-trace': '***HIDDEN***',
        'x-urbn-channel': 'web',
        'x-urbn-country': 'IN',
        'x-urbn-currency': 'USD',
        'x-urbn-experience': 'ss',
        'x-urbn-geo-region': 'AS-SG',
        'x-urbn-language': 'en-US',
        'x-urbn-primary-data-center-id': 'US-NV',
        'x-urbn-site-id': 'uo-us',
    }

    json_data = {
        'reauthToken': reauth_token,
    }

    response = requests.put(
        'https://www.urbanoutfitters.com/slipstream/api/token/v0/uo-us/auth',
        headers=headers,
        json=json_data,
    )
    print(response)
    data = response.json()
    with open("token_data.json", "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    auth_token = data.get("authToken")
    return auth_token

def get_datadom_token():
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.urbanoutfitters.com',
        'priority': 'u=1, i',
        'referer': 'https://www.urbanoutfitters.com/',
        'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    }

    data = {
        'jspl': '***HIDDEN***',
        'eventCounters': '{"mousemove":84,"pointermove":84,"click":0,"scroll":38,"touchstart":0,"touchend":0,"touchmove":0,"keydown":0,"keyup":0}',
        'jsType': 'le',
        'cid': '***HIDDEN***',
        'ddk': '***HIDDEN***',
        'Referer': 'https%3A%2F%2Fwww.urbanoutfitters.com',
        'request': '%2Fshop%2Fbdg-rigby-cotton-pull-on-micro-short',
        'responsePage': 'origin',
        'ddv': '5.9.0',
    }
    response = requests.post('https://dd.urbanoutfitters.com/js/', headers=headers, data=data)
    if response.status_code == 200:
        try:
            result = response.json()
            cookie = result.get("cookie")
            if cookie:
                new_token = cookie.split(";")[0].split("=")[1]
                # save_token(new_token)
                return new_token
        except:
            pass
        # return datadom_token

if __name__ == '__main__':
    auth_token = get_auth_token()
    print(auth_token)
    quit()




#################################################################################
# import curlify
# import requests
# from urllib.parse import urlparse, parse_qs, quote
# import db_config_1 as db
# target_url = 'https://api.urbanoutfitters.com/api/content/v1/uo-us/entries'
# params ={
#             'include': '4',
#             'contentfulEnvironment': 'master',
#             'content_type': 'sizeGuideConfiguration',
#             'fields.slug': 'VENDOR_NEWBALANCESHOES',
#         }
# prepared = requests.Request('GET', target_url,params=params).prepare()
# encoded_url = quote(prepared.url, safe='')
# proxy_url = (f"http://api.scrape.do/?token={db.p_token}&url={encoded_url}&super=true")
# response = requests.get(proxy_url, timeout=80)
# print(curlify.to_curl(response.request))
#
# target_url = f"https://api.urbanoutfitters.com/api/review/v0/uo-us/products/UO-84994763-000/reviews"
# params = {
#     "merchandise-class": '0315',
#     "offset": '0',
#     "limit": '50',
#     "filter": "",
#     "sort": "submissionTime:desc"
# }
# # Prepare encoded URL
# prepared = requests.Request("GET", target_url, params=params).prepare()
# encoded_url = quote(prepared.url, safe='')
# proxy_url = f"http://api.scrape.do/?token={db.p_token}&url={encoded_url}&super=true"
# response = requests.get(proxy_url, timeout=60)
# print(curlify.to_curl(response.request))
