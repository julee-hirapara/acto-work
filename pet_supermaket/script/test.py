import requests

TOKEN = "***HIDDEN***"
pdp_url = "https://www.petsupermarket.com/cat/supplies/grooming/shampoos-conditioners/tropiclean-oxymed-hairball-relief-waterless-foaming-cat-shampoo-7.4oz/PSI09598.html"
url = "https://api.scrape.do/"
params = {
    "url": pdp_url,
    "token": TOKEN
}
response = requests.get(url, params=params, timeout=60)

print("Status:", response.status_code)
print("Final URL:", response.url)
print("Response headers:", dict(response.headers))
