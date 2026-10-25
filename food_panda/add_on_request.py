import requests

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'apollographql-client-name': 'web',
    'apollographql-client-version': 'VENDOR-DETAILS-MICROFRONTEND.26.20.0006',
    'content-type': 'application/json;charset=UTF-8',
    'customer-latitude': '3.14789',
    'customer-longitude': '101.69405',
    'display-context': 'ITEM_MODIFIER',
    'locale': 'en_MY',
    'origin': 'https://www.foodpanda.my',
    'perseus-client-id': '1777874806175.306314031362213428.yva1tod3yd',
    'perseus-session-id': '1778739501957.026372450550022513.ldmwztz84l',
    'platform': 'web',
    'priority': 'u=1, i',
    'referer': 'https://www.foodpanda.my/',
    'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'x-apollo-operation-name': 'RestaurantProductQuery',
    'x-language-id': '1',
    'x-pd-language-id': '1',
}

json_data = {
    'extensions': {
        'persistedQuery': {
            'sha256Hash': '***HIDDEN***',
            'version': 1,
        },
    },
    'variables': {
        'isPreconfiguredToppingsEnabled': False,
        'recommendedChoiceGroupsInput': {
            'isMealForOne': False,
            'expeditionType': 'DELIVERY',
        },
        'input': {
            'productID': '1975900033',
            'vendorCode': 'uia0',
            'expeditionType': 'DELIVERY',
            'menuID': '5892814',
        },
        'discountedPriceInput': {
            'expeditionType': 'DELIVERY',
        },
        'includeVendor': True,
    },
}

response = requests.post('https://my.fd-api.com/graphql', headers=headers, json=json_data)

# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
#data = '{"extensions":{"persistedQuery":{"sha256Hash":"***HIDDEN***","version":1}},"variables":{"isPreconfiguredToppingsEnabled":false,"recommendedChoiceGroupsInput":{"isMealForOne":false,"expeditionType":"DELIVERY"},"input":{"productID":"1975900033","vendorCode":"uia0","expeditionType":"DELIVERY","menuID":"5892814"},"discountedPriceInput":{"expeditionType":"DELIVERY"},"includeVendor":true}}'
#response = requests.post('https://my.fd-api.com/graphql', headers=headers, data=data)