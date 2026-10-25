import requests
import tls_client
from parsel import Selector
import json

cookies = {
    'vtc': 'b5HhmfcgvErfaYcyD-rLZY',
    'AID': 'wmlspartner=0:reflectorid=0000000000000000000000:lastupd=1778216813501',
    'ACID': '90cf83c9-b4a9-41e8-80c7-64b1a635c663',
    '_m': '9',
    'hasACID': 'true',
    'abqme': 'true',
    '_pxvid': '***HIDDEN***',
    'pxcts': '***HIDDEN***',
    'adblocked': 'false',
    'io_id': '4d50f54f-038c-4436-ae9c-17aca359ea13',
    'isoLoc': 'US_NJ_t3',
    '_pxhd': '***HIDDEN***',
    'bm_mi': '***HIDDEN***',
    'bm_sv': '***HIDDEN***',
    'ak_bmsc': '***HIDDEN***',
    'bstc': 'YNoZA2oaGmemppyFJnp5VM',
    'xpa': '0Mud_|4EdRR|5caGU|6MG6f|9KAV1|BeUOj|Bvar_|CA1jM|H5i94|J0bU2|J0eUl|LmatO|Nb_Ip|Swr3R|WW07u|ZloIH|_yYS_|a7hKP|aphrF|fdm-7|jAjGm|jIKKp|jM1ax|lQjpJ|nDuV2|qQ9d7',
    'exp-ck': '4EdRR36MG6f19KAV13Bvar_1CA1jM2H5i941J0bU21J0eUl1Nb_Ip1Swr3R1ZloIH2aphrF2fdm-71jIKKp1nDuV21',
    'xpth': 'x-o-mart%2BB2C~x-o-mverified%2Bfalse',
    '_intlbu': 'false',
    '_shcc': 'US',
    'hasLocData': '1',
    '_astc': '***HIDDEN***',
    'dimensionData': '440',
    'userAppVersion': '***HIDDEN***',
    'assortmentStoreId': '2152',
    'locDataV3': '***HIDDEN***',
    'locGuestData': '***HIDDEN***',
    'akavpau_p1': '***HIDDEN***',
    'xpm': '1%2B1778220706%2Bb5HhmfcgvErfaYcyD-rLZY~%2B0',
    'if_id': '***HIDDEN***',
    'TS016ef4c8': '***HIDDEN***',
    'TS01f89308': '***HIDDEN***',
    'TS8cb5a80e027': '***HIDDEN***',
    'xptwj': '***HIDDEN***',
    'akavpau_p2': '***HIDDEN***',
    'xptc': '_m%2B9~assortmentStoreId%2B2152',
    'com.wm.reflector': '"reflectorid:0000000000000000000000@lastupd:1778221294000@firstcreate:1778160210330"',
    'xptwg': '3723120819:126DCA6E7CA0070:2C82F54:35F85410:55C2E97C:F0BE2ABC:',
    'TS012768cf': '***HIDDEN***',
    'TS01a90220': '***HIDDEN***',
    'TS2a5e0c5c027': '***HIDDEN***',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'device-memory': '16',
    'downlink': '1.4',
    'dpr': '1.5',
    'priority': 'u=0, i',
    'sec-ch-device-memory': '16',
    'sec-ch-dpr': '1.5',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    # 'cookie': '***HIDDEN***',
}

params = {
    'q': 'soda',
}
session = tls_client.Session(
    client_identifier="chrome_142",
    random_tls_extension_order=True
)
response = session.get('https://www.walmart.com/search',
                        params=params,
                        cookies=cookies,
                        headers=headers
                        )
print(response)
with open("pl.html", "w", encoding='utf-8') as f:
    f.write(response.text)
html = response.text

sel = Selector(text=html)

# extract json text from script tag
json_text = sel.xpath('//script[@id="__NEXT_DATA__"]/text()').get()

# print(json_text[:500])  # preview

# convert to python dict
data = json.loads(json_text)
# print("data ::: ", data)
print(type(data))

import requests

cookies = {
    'vtc': 'b5HhmfcgvErfaYcyD-rLZY',
    'AID': 'wmlspartner=0:reflectorid=0000000000000000000000:lastupd=1778216813501',
    'ACID': '90cf83c9-b4a9-41e8-80c7-64b1a635c663',
    '_m': '9',
    'hasACID': 'true',
    'abqme': 'true',
    '_pxvid': '***HIDDEN***',
    'pxcts': '***HIDDEN***',
    'adblocked': 'false',
    'io_id': '4d50f54f-038c-4436-ae9c-17aca359ea13',
    'isoLoc': 'US_NJ_t3',
    '_pxhd': '***HIDDEN***',
    'bm_mi': '***HIDDEN***',
    'bm_sv': '***HIDDEN***',
    'ak_bmsc': '***HIDDEN***',
    '_intlbu': 'false',
    '_shcc': 'US',
    'hasLocData': '1',
    'dimensionData': '440',
    'userAppVersion': '***HIDDEN***',
    'assortmentStoreId': '2152',
    'locDataV3': '***HIDDEN***',
    'akavpau_p1': '***HIDDEN***',
    'xptwj': '***HIDDEN***',
    '_astc': '***HIDDEN***',
    'locGuestData': '***HIDDEN***',
    'com.wm.reflector': '"reflectorid:0000000000000000000000@lastupd:1778221312000@firstcreate:1778160210330"',
    'xptwg': '748776469:C7A5B3F2F01D60:1E2361C:989A4211:50F3E4C1:EE4D2B79:',
    'TS01a90220': '***HIDDEN***',
    'TS012768cf': '***HIDDEN***',
    'TS2a5e0c5c027': '***HIDDEN***',
    'if_id': '***HIDDEN***',
    'TS016ef4c8': '***HIDDEN***',
    'TS01f89308': '***HIDDEN***',
    'TS8cb5a80e027': '***HIDDEN***',
    'akavpau_p2': '***HIDDEN***',
    'bstc': 'UeH_BFH8Ur3iGQeBwhZ_f4',
}

headers = {
    'accept': 'application/json',
    'accept-language': 'en-US',
    'baggage': '***HIDDEN***',
    'content-type': 'application/json',
    'device-memory': '16',
    'downlink': '10',
    'dpr': '1.5',
    'priority': 'u=1, i',
    'referer': 'https://www.walmart.com/search?q=soda&page=2&affinityOverride=store_led',
    'sec-ch-device-memory': '16',
    'sec-ch-dpr': '1.5',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'tenant-id': 'elh9ie',
    'traceparent': '***HIDDEN***',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'wm-client-traceid': '***HIDDEN***',
    'wm_mp': 'true',
    'wm_page_url': 'https://www.walmart.com/search?q=soda&page=2&affinityOverride=store_led',
    'wm_qos.correlation_id': 'rDdlmjnXlUtRn7Gn50cizaUwXpK6WoGfBE-P',
    'x-apollo-operation-name': 'Search',
    'x-enable-server-timing': '1',
    'x-latency-trace': '1',
    'x-o-bu': 'WALMART-US',
    'x-o-ccm': 'server',
    'x-o-correlation-id': 'rDdlmjnXlUtRn7Gn50cizaUwXpK6WoGfBE-P',
    'x-o-gql-query': 'query Search',
    'x-o-mart': 'B2C',
    'x-o-platform': 'rweb',
    'x-o-platform-version': '***HIDDEN***',
    'x-o-segment': 'oaoh',
    # 'cookie': '***HIDDEN***',
}
variables = {
    "id": "",
    "affinityOverride": "store_led",
    "query": "soda",
    "page": 2,
    "ps": 40,
    "limit": 40,
    "sort": "best_match",

    "additionalQueryParams": {
        "hidden_facet": None,
        "translation": None,
        "isMoreOptionsTileEnabled": True,
        "isGenAiEnabled": False
    },

    "searchArgs": {
        "query": "soda",
        "cat_id": "",
        "prg": "desktop",
        "facet": ""
    },

    "pageType": "SearchPage"
}

params = {
    "variables": json.dumps(variables, separators=(",", ":"))
}

response = requests.get(
    "https://www.walmart.com/orchestra/snb/graphql/Search/7bf57a3d34085376704f3b81b0a118cedef00b02cc8b6fe0b512c7fc5d9e80fc/search",
    params=params,
    cookies=cookies,
    headers=headers,
)

print(response.status_code)
print("-------------------------------------------------------------")
# params = {
#     #     'variables': '{"id":"","affinityOverride":"store_led","dealsId":"","query":"soda","nudgeContext":"","page":2,"prg":"desktop","catId":"","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"isGenAiEnabled":false,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isModuleArrayReq":false,"isLMPBrowsePage":false},"searchArgs":{"query":"soda","cat_id":"","prg":"desktop","facet":""},"enableDesktopHighlights":false,"enableVolumePricing":false,"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":false,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"fitmentFieldParams":{"powerSportEnabled":true,"dynamicFitmentEnabled":true,"extendedAttributesEnabled":false,"extendedAttributesV2Enabled":false,"fuelTypeEnabled":false},"fitmentSearchParams":{"id":"","affinityOverride":"store_led","dealsId":"","query":"soda","nudgeContext":"","page":2,"prg":"desktop","catId":"","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"isGenAiEnabled":false,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isModuleArrayReq":false,"isLMPBrowsePage":false},"searchArgs":{"query":"soda","cat_id":"","prg":"desktop","facet":""},"enableDesktopHighlights":false,"enableVolumePricing":false,"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":false,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":"","_be_shelf_id":""},"searchParams":{"id":"","affinityOverride":"store_led","dealsId":"","query":"soda","nudgeContext":"","page":2,"prg":"desktop","catId":"","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"isGenAiEnabled":false,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isModuleArrayReq":false,"isLMPBrowsePage":false},"searchArgs":{"query":"soda","cat_id":"","prg":"desktop","facet":""},"enableDesktopHighlights":false,"enableVolumePricing":false,"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":false,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":"","_be_shelf_id":""},"enableFashionTopNav":false,"enableUnifiedSchema":false,"postProcessingVersion":1,"version":"v1","enableRelatedSearches":false,"enablePortableFacets":false,"enableFacetCount":true,"fetchMarquee":true,"fetchSkyline":true,"fetchGallery":false,"fetchSbaTop":true,"fetchDataV1":false,"fetchDataV2":false,"fungibilityEnabled":false,"enableAdsPromoData":false,"fetchDac":false,"tenant":"WM_GLASS","enableMultiSave":false,"enableInStoreShelfMessage":false,"enableSellerType":false,"enableItemRank":false,"enableOptimisticWeightUpdate":false,"enableAdditionalSearchDepartmentAnalytics":false,"enableFulfillmentTagsEnhacements":false,"enableRxDrugScheduleModal":false,"enablePromoData":false,"enableSignInToSeePrice":false,"enablePromotionMessages":false,"enableDebugAnalyticsTags":false,"enableItemLimits":false,"enableCanAddToList":false,"enableIsFreeWarranty":false,"enableShopSimilarBottomSheet":false,"adsParams":{"fungibilityEnabled":false},"pageType":"SearchPage"}',
# 'variables' : """{
#     "id": "",
#     "affinityOverride": "store_led",
#     "dealsId": "",
#     "query": "soda",
#     "nudgeContext": "",
#     "page": 2,
#     "prg": "desktop",
#     "catId": "",
#     "facet": "",
#     "sort": "best_match",
#     "rawFacet": "",
#     "seoPath": "",
#     "ps": 40,
#     "limit": 40,
#     "ptss": "",
#     "trsp": "",
#     "beShelfId": "",
#     "recall_set": "",
#     "module_search": "",
#     "min_price": "",
#     "max_price": "",
#     "storeSlotBooked": "",
#
#     "additionalQueryParams": {
#         "hidden_facet": None,
#         "translation": None,
#         "isMoreOptionsTileEnabled": True,
#         "isGenAiEnabled": False,
#         "rootDimension": "",
#         "altQuery": "",
#         "selectedFilter": "",
#         "neuralSearchSeeAll": False,
#         "isModuleArrayReq": False,
#         "isLMPBrowsePage": False
#     },
#
#     "searchArgs": {
#         "query": "soda",
#         "cat_id": "",
#         "prg": "desktop",
#         "facet": ""
#     },
#
#     "enableDesktopHighlights": False,
#     "enableVolumePricing": False,
#     "enableCopyBlock": True,
#     "enableVariantCount": False,
#     "enableSlaBadgeV2": False,
#     "enableUnifiedProductFragment": False,
#     "enableESSCarousel": False,
#
#     "fitmentFieldParams": {
#         "powerSportEnabled": True,
#         "dynamicFitmentEnabled": True,
#         "extendedAttributesEnabled": False,
#         "extendedAttributesV2Enabled": False,
#         "fuelTypeEnabled": False
#     },
#
#     "fitmentSearchParams": {
#         "id": "",
#         "affinityOverride": "store_led",
#         "dealsId": "",
#         "query": "soda",
#         "page": 2,
#         "ps": 40,
#         "limit": 40,
#         "sort": "best_match"
#     },
#
#     "searchParams": {
#         "id": "",
#         "affinityOverride": "store_led",
#         "dealsId": "",
#         "query": "soda",
#         "page": 2,
#         "ps": 40,
#         "limit": 40,
#         "sort": "best_match"
#     },
#
#     "enableFashionTopNav": False,
#     "enableUnifiedSchema": False,
#     "postProcessingVersion": 1,
#     "version": "v1",
#
#     "enableRelatedSearches": False,
#     "enablePortableFacets": False,
#     "enableFacetCount": True,
#
#     "fetchMarquee": True,
#     "fetchSkyline": True,
#     "fetchGallery": False,
#     "fetchSbaTop": True,
#
#     "fetchDataV1": False,
#     "fetchDataV2": False,
#
#     "fungibilityEnabled": False,
#     "enableAdsPromoData": False,
#     "fetchDac": False,
#
#     "tenant": "WM_GLASS",
#
#     "enableMultiSave": False,
#     "enableInStoreShelfMessage": False,
#     "enableSellerType": False,
#     "enableItemRank": False,
#     "enableOptimisticWeightUpdate": False,
#     "enableAdditionalSearchDepartmentAnalytics": False,
#     "enableFulfillmentTagsEnhacements": False,
#     "enableRxDrugScheduleModal": False,
#     "enablePromoData": False,
#     "enableSignInToSeePrice": False,
#     "enablePromotionMessages": False,
#     "enableDebugAnalyticsTags": False,
#     "enableItemLimits": False,
#     "enableCanAddToList": False,
#     "enableIsFreeWarranty": False,
#     "enableShopSimilarBottomSheet": False,
#
#     "adsParams": {
#         "fungibilityEnabled": False
#     },
#
#     "pageType": "SearchPage"
# }"""
# }

# response = requests.get(
#     'https://www.walmart.com/orchestra/snb/graphql/Search/7bf57a3d34085376704f3b81b0a118cedef00b02cc8b6fe0b512c7fc5d9e80fc/search',
#     params=params,
#     cookies=cookies,
#     headers=headers,
# )

print(response)
with open("data.json", "w", encoding='utf-8') as f:
    json.dump(response.json(), f, indent=4, ensure_ascii=False)