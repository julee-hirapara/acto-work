import os
import requests
from parsel import Selector
# TOKEN_FILE = "datadome_token.txt"
# import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "datadome_token.txt")

def save_token(token):
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(token.strip())


def read_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def update_token(datadom_token=None):
    # Read token from file if not passed
    if datadom_token is None:
        datadom_token = read_token()

    if not datadom_token:
        raise Exception("No DataDome token found.")

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.constructionweekonline.com',
        'priority': 'u=1, i',
        'referer': 'https://www.constructionweekonline.com/',
        'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    }

    data = {
        # 'jspl': '***HIDDEN***',
        'jspl': '',
        'eventCounters': '{"mousemove":11,"pointermove":1,"click":0,"scroll":0,"touchstart":0,"touchend":0,"touchmove":0,"keydown":0,"keyup":0}',
        'jsType': 'le',
        'cid': '***HIDDEN***',
        # 'cid': '***HIDDEN***',
        'ddk': '***HIDDEN***',
        'Referer': 'https%3A%2F%2Fwww.constructionweekonline.com%2F',
        'request': '%2F',
        'responsePage': 'origin',
        'ddv': '5.9.0',
    }
    response = requests.post('https://api-js.datadome.co/js/', headers=headers, data=data)
    if response.status_code == 200:
        try:
            result = response.json()
            cookie = result.get("cookie")
            if cookie:
                new_token = cookie.split(";")[0].split("=")[1]
                save_token(new_token)
                return new_token
        except:
            pass
        return datadom_token
#
# datadom_token = update_token()
# print(datadom_token)
#
#
# url = "https://www.constructionweekonline.com/"
# params = {
#     # "s": 'ADNOC Drilling',
#     "s": '타북 석유 시설',
#     # "s": 'Iraqi National Oil Company',
#     "cat_name": ""
# }
# cookies = {
#         'datadome': '***HIDDEN***',
#         # 'datadome': '***HIDDEN***',
#         # 'datadome': '***HIDDEN***',
#     }
# headers = {
#     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#     'accept-language': 'en-US,en;q=0.9',
#     'cache-control': 'max-age=0',
#     'priority': 'u=0, i',
#     'referer': 'https://www.constructionweekonline.com/',
#     'sec-ch-device-memory': '32',
#     'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
#     'sec-ch-ua-arch': '"x86"',
#     'sec-ch-ua-full-version-list': '"Not;A=Brand";v="8.0.0.0", "Chromium";v="150.0.7871.127", "Google Chrome";v="150.0.7871.127"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-model': '""',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'document',
#     'sec-fetch-mode': 'navigate',
#     'sec-fetch-site': 'same-origin',
#     'sec-fetch-user': '?1',
#     'upgrade-insecure-requests': '1',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
# }
# response = requests.get(
#     # final_url,
#     'https://www.constructionweekonline.com/', params=params,
#     cookies=cookies,
#     headers=headers
# )
# print(response)
# print(response.text)
# selector = Selector(response.text)
# # No result page
# articles = selector.xpath('//main[contains(@id, "main")]//article')
# print(articles)
# page_title = selector.xpath('//main[contains(@id, "main")]//h1[contains(@class, "page-title")]/text()').get()
# if page_title == 'Nothing Found':
#     print("keyword not found")
# print(f"page_title ::: {page_title}")

# # #
#
# # import requests
# #
# # def update_token(datadom_token):
# #     headers = {
# #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
# #         "Accept": "*/*",
# #         "Content-Type": "application/x-www-form-urlencoded",
# #         "Origin": "https://www.constructionweekonline.com",
# #         "Referer": "https://www.constructionweekonline.com/"
# #     }
# #     data = {
# #         'jspl': '***HIDDEN***',
# #         'eventCounters': '{"mousemove":2,"pointermove":1,"click":0,"scroll":0,"touchstart":0,"touchend":0,"touchmove":0,"keydown":0,"keyup":0}',
# #         'jsType': 'ch',
# #         # 'cid': '***HIDDEN***',
# #         'cid': '***HIDDEN***',
# #         # 'cid': f"{datadom_token}",
# #         'ddk': '***HIDDEN***',
# #         'Referer': 'https%3A%2F%2Fwww.constructionweekonline.com%2F',
# #         'request': '%2F%3Fs%3Dlayoffs%26cat_name%3D',
# #         'responsePage': 'origin',
# #         'ddv': '5.9.0',
# #     }
# #     response = requests.post('https://api-js.datadome.co/js/',  headers=headers, data=data)
# #     print(response)
# #     if response.status_code == 200:
# #         result = response.json()
# #         # Full cookie string
# #         cookie = result.get("cookie", "")
# #         # Extract only the datadome token
# #         datadome_token = cookie.split(";")[0].split("=", 1)[1]
# #         print("\nDataDome Token:")
# #         print(datadome_token)
# #         return datadome_token
# #
# #
# # datadom_token = update_token(datadom_token='***HIDDEN***')
# # # datadom_token = update_token(datadom_token='***HIDDEN***')
# #
# #
# # cookies ={
# #     # 'datadome': '***HIDDEN***',
# #     'datadome': '***HIDDEN***',
# #     # 'aws-waf-token': '***HIDDEN***',
# # }
# #
# # headers = {
# #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
# #     'accept-language': 'en-US,en;q=0.9',
# #     'cache-control': 'max-age=0',
# #     'priority': 'u=0, i',
# #     'referer': 'https://www.constructionweekonline.com/?s=layoffs&cat_name=',
# #     'sec-ch-device-memory': '32',
# #     'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
# #     'sec-ch-ua-arch': '"x86"',
# #     'sec-ch-ua-full-version-list': '"Not;A=Brand";v="8.0.0.0", "Chromium";v="150.0.7871.127", "Google Chrome";v="150.0.7871.127"',
# #     'sec-ch-ua-mobile': '?0',
# #     'sec-ch-ua-model': '""',
# #     'sec-ch-ua-platform': '"Windows"',
# #     'sec-fetch-dest': 'document',
# #     'sec-fetch-mode': 'navigate',
# #     'sec-fetch-site': 'same-origin',
# #     'sec-fetch-user': '?1',
# #     'upgrade-insecure-requests': '1',
# #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
# #     # 'cookie': '***HIDDEN***',
# # }
# #
# # params = {
# #     's': 'layoffs',
# #     # 's': "A'ali",
# #     'cat_name': '',
# # }
# #
# # for i in range(100):
# #     response = requests.request(method='GET',url='https://www.constructionweekonline.com/',
# #                             params=params,
# #                             cookies=cookies,
# #                             headers=headers
# #                             )
# #     print(f"{i} :: {response.status_code}")

