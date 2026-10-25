import json
import os.path
import requests
from db_config import *
import db_config as db

def get_sub_category_links_bk(main_url,cat_id):
    cookies = {
        'adblocked': 'false',
        '_pxvid': '***HIDDEN***',
        'ACID': '28d24db6-fad4-4843-ae28-5cf5a395ed4f',
        '_m': '9',
        'hasACID': 'true',
        'abqme': 'true',
        '_pxhd': '***HIDDEN***',
        'vtc': 'aAML4Y7i5AJIS5Yp9qsqGk',
        'io_id': '005b2014-bf34-48ca-8e9e-78ecf4614c0c',
        'hasLocData': '1',
        'assortmentStoreId': '757',
        'dimensionData': '633',
        'isoLoc': 'IN_GJ_t3',
        'pxcts': '***HIDDEN***',
        '_astc': '***HIDDEN***',
        'AID': 'wmlspartner=0:reflectorid=0000000000000000000000:lastupd=1778758254155',
        '_xrps': 'false',
        'salsify_session_id': '73cde374-fe19-40c9-8565-530bcd1c1b28',
        'bstc': 'YKwMJnYTzgSCL3SBxFJ8qo',
        '_intlbu': 'false',
        '_shcc': 'US',
        'locDataV3': '***HIDDEN***',
        'userAppVersion': '***HIDDEN***',
        'xpth': 'x-o-mart%2BB2C~x-o-mverified%2Bfalse',
        'xpa': '1K-QU|1yTUd|30Fw1|3dj2O|5lkg6|6MG6f|8HCxo|CA1jM|GJLYr|Gr8kp|J0bU2|Jfzc9|LmatO|W30km|e4VGo|ekWg9|fdm-7|hb_OD|iXa3Y|jAjGm|jIKKp|jM1ax|jVixg|khRmE|lRAEa|qr1Kx|t04it|xUczm|zKxms',
        'exp-ck': '1K-QU130Fw126MG6f1CA1jM2GJLYr1Gr8kp3J0bU21W30km1ekWg91fdm-71hb_OD3iXa3Y2jIKKp1jVixg1lRAEa1qr1Kx1t04it1xUczm1zKxms1',
        'xptwj': '***HIDDEN***',
        'ak_bmsc': '***HIDDEN***',
        'xpm': '1%2B1778838391%2BaAML4Y7i5AJIS5Yp9qsqGk~%2B0',
        'locGuestData': '***HIDDEN***',
        '_px3': '***HIDDEN***',
        'akavpau_p2': '***HIDDEN***',
        'if_id': '***HIDDEN***',
        'TS016ef4c8': '***HIDDEN***',
        'TS01f89308': '***HIDDEN***',
        'TS8cb5a80e027': '***HIDDEN***',
        '_pxde': '***HIDDEN***',
        'xptc': '_m%2B9~assortmentStoreId%2B757',
        'com.wm.reflector': '"reflectorid:0000000000000000000000@lastupd:1778838431000@firstcreate:1778216693513"',
        'xptwg': '517411970:494D3F0939B488:B0FC49:31F40347:CC7B7760:11E74100:',
        'TS012768cf': '***HIDDEN***',
        'TS01a90220': '***HIDDEN***',
        'TS2a5e0c5c027': '***HIDDEN***',
        'bm_sv': '***HIDDEN***',
    }

    headers = {
        'accept': 'application/json',
        'accept-language': 'en-US',
        'baggage': '***HIDDEN***',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'device-memory': '8',
        'downlink': '10',
        'dpr': '1',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://www.walmart.com/browse/food/everyday-baking-essentials/976759_976780_5837233?affinityOverride=default&facet=brand%3AGreat+Value&seo=food&seo=everyday-baking-essentials&seo=976759_976780_5837233&page=2',
        'sec-ch-device-memory': '8',
        'sec-ch-dpr': '1',
        'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'tenant-id': 'elh9ie',
        'traceparent': '***HIDDEN***',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        'wm-client-traceid': '***HIDDEN***',
        'wm_mp': 'true',
        'wm_page_url': 'https://www.walmart.com/browse/food/everyday-baking-essentials/976759_976780_5837233?affinityOverride=default&facet=brand%3AGreat+Value&seo=food&seo=everyday-baking-essentials&seo=976759_976780_5837233&page=2',
        'wm_qos.correlation_id': '8wymLXvVrwGPGkjXQn8MhMTbz2Gj-GBt1FIM',
        'x-apollo-operation-name': 'Browse',
        'x-enable-server-timing': '1',
        'x-latency-trace': '1',
        'x-o-bu': 'WALMART-US',
        'x-o-ccm': 'server',
        'x-o-correlation-id': '8wymLXvVrwGPGkjXQn8MhMTbz2Gj-GBt1FIM',
        'x-o-gql-query': 'query Browse',
        'x-o-mart': 'B2C',
        'x-o-platform': 'rweb',
        'x-o-platform-version': '***HIDDEN***',
        'x-o-segment': 'oaoh',
        # 'cookie': '***HIDDEN***',
    }


    page = 1
    brand_lst = []
    while True:

        # params = {
        #     'variables': f'{{"id":"","affinityOverride":"default","pap":"{{\\"polaris\\":{{\\"ms_triggered\\":false}}}}","dealsId":"","query":"","nudgeContext":"","page":{page},"prg":"desktop","catId":{cat_id},"facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isLMPBrowsePage":false}},"searchArgs":{{"query":"","cat_id":{cat_id},"prg":"desktop","facet":""}},"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":true,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"fitmentFieldParams":{{"powerSportEnabled":true,"dynamicFitmentEnabled":true,"extendedAttributesEnabled":true,"extendedAttributesV2Enabled":false,"fuelTypeEnabled":true}},"fitmentSearchParams":{{"id":"","affinityOverride":"default","pap":"{{\\"polaris\\":{{\\"ms_triggered\\":false}}}}","dealsId":"","query":"","nudgeContext":"","page":{page},"prg":"desktop","catId":{cat_id},"facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isLMPBrowsePage":false}},"searchArgs":{{"query":"","cat_id":{cat_id},"prg":"desktop","facet":""}},"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":true,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":{cat_id},"_be_shelf_id":""}},"searchParams":{{"id":"","affinityOverride":"default","pap":"{{\\"polaris\\":{{\\"ms_triggered\\":false}}}}","dealsId":"","query":"","nudgeContext":"","page":{page},"prg":"desktop","catId":{cat_id},"facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isLMPBrowsePage":false}},"searchArgs":{{"query":"","cat_id":{cat_id},"prg":"desktop","facet":""}},"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":true,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":{cat_id},"_be_shelf_id":""}},"enableFashionTopNav":false,"fetchMarquee":true,"fetchSkyline":true,"fetchSbaTop":true,"fetchDataV1":true,"fetchDataV2":false,"fungibilityEnabled":false,"fetchGallery":false,"fetchDac":true,"enablePortableFacets":true,"tenant":"WM_GLASS","pageType":"BrowsePage","enableFacetCount":true,"enableMultiSave":false,"enableInStoreShelfMessage":false,"fSeo":true,"enableSellerType":false,"enableItemRank":false,"enableOptimisticWeightUpdate":false,"enableFulfillmentTagsEnhacements":false,"enableRxDrugScheduleModal":false,"enablePromoData":true,"enableAdsPromoData":false,"enableSeoLangUrl":false,"enableImageBannerCarousel":false,"enableHero4":false,"enableSeoBrowseMetaDataShortDesc":false,"enableCanAddToList":false,"enablePromotionMessages":false,"enableDebugAnalyticsTags":false,"enableSignInToSeePrice":false,"enableSimpleEmailSignUp":false,"enableModuleReposition":false,"enableUnifiedSchema":false,"version":"v1","postProcessingVersion":1}}'
        # }
        variables = {
            "id": "",
            "affinityOverride": "default",
            "pap": "{\"polaris\":{\"ms_triggered\":false}}",
            "dealsId": "",
            "query": "",
            "nudgeContext": "",
            "page": page,
            "prg": "desktop",
            "catId": cat_id,
            "facet": "",
            "sort": "best_match",
            "rawFacet": "",
            "seoPath": "",
            "ps": 40,
            "limit": 40,
            "ptss": "",
            "trsp": "",
            "beShelfId": "",
            "recall_set": "",
            "module_search": "",
            "min_price": "",
            "max_price": "",
            "storeSlotBooked": "",

            "additionalQueryParams": {
                "hidden_facet": None,
                "translation": None,
                "isMoreOptionsTileEnabled": True,
                "rootDimension": "",
                "altQuery": "",
                "selectedFilter": "",
                "neuralSearchSeeAll": False,
                "isLMPBrowsePage": False
            },

            "searchArgs": {
                "query": "",
                "cat_id": cat_id,
                "prg": "desktop",
                "facet": ""
            },

            "enableCopyBlock": True,
            "enableVariantCount": False,
            "enableSlaBadgeV2": True,
            "enableUnifiedProductFragment": False,
            "enableESSCarousel": False,

            "fitmentFieldParams": {
                "powerSportEnabled": True,
                "dynamicFitmentEnabled": True,
                "extendedAttributesEnabled": True,
                "extendedAttributesV2Enabled": False,
                "fuelTypeEnabled": True
            },

            "fitmentSearchParams": {
                "id": "",
                "affinityOverride": "default",
                "pap": "{\"polaris\":{\"ms_triggered\":false}}",
                "dealsId": "",
                "query": "",
                "nudgeContext": "",
                "page": page,
                "prg": "desktop",
                "catId": cat_id,
                "facet": "",
                "sort": "best_match",
                "rawFacet": "",
                "seoPath": "",
                "ps": 40,
                "limit": 40,
                "ptss": "",
                "trsp": "",
                "beShelfId": "",
                "recall_set": "",
                "module_search": "",
                "min_price": "",
                "max_price": "",
                "storeSlotBooked": "",

                "additionalQueryParams": {
                    "hidden_facet": None,
                    "translation": None,
                    "isMoreOptionsTileEnabled": True,
                    "rootDimension": "",
                    "altQuery": "",
                    "selectedFilter": "",
                    "neuralSearchSeeAll": False,
                    "isLMPBrowsePage": False
                },

                "searchArgs": {
                    "query": "",
                    "cat_id": cat_id,
                    "prg": "desktop",
                    "facet": ""
                },

                "enableCopyBlock": True,
                "enableVariantCount": False,
                "enableSlaBadgeV2": True,
                "enableUnifiedProductFragment": False,
                "enableESSCarousel": False,
                "cat_id": cat_id,
                "_be_shelf_id": ""
            },

            "searchParams": {
                "id": "",
                "affinityOverride": "default",
                "pap": "{\"polaris\":{\"ms_triggered\":false}}",
                "dealsId": "",
                "query": "",
                "nudgeContext": "",
                "page": page,
                "prg": "desktop",
                "catId": cat_id,
                "facet": "",
                "sort": "best_match",
                "rawFacet": "",
                "seoPath": "",
                "ps": 40,
                "limit": 40,
                "ptss": "",
                "trsp": "",
                "beShelfId": "",
                "recall_set": "",
                "module_search": "",
                "min_price": "",
                "max_price": "",
                "storeSlotBooked": "",

                "additionalQueryParams": {
                    "hidden_facet": None,
                    "translation": None,
                    "isMoreOptionsTileEnabled": True,
                    "rootDimension": "",
                    "altQuery": "",
                    "selectedFilter": "",
                    "neuralSearchSeeAll": False,
                    "isLMPBrowsePage": False
                },

                "searchArgs": {
                    "query": "",
                    "cat_id": cat_id,
                    "prg": "desktop",
                    "facet": ""
                },

                "enableCopyBlock": True,
                "enableVariantCount": False,
                "enableSlaBadgeV2": True,
                "enableUnifiedProductFragment": False,
                "enableESSCarousel": False,
                "cat_id": cat_id,
                "_be_shelf_id": ""
            },

            "enableFashionTopNav": False,
            "fetchMarquee": True,
            "fetchSkyline": True,
            "fetchSbaTop": True,
            "fetchDataV1": True,
            "fetchDataV2": False,
            "fungibilityEnabled": False,
            "fetchGallery": False,
            "fetchDac": True,
            "enablePortableFacets": True,
            "tenant": "WM_GLASS",
            "pageType": "BrowsePage",
            "enableFacetCount": True,
            "enableMultiSave": False,
            "enableInStoreShelfMessage": False,
            "fSeo": True,
            "enableSellerType": False,
            "enableItemRank": False,
            "enableOptimisticWeightUpdate": False,
            "enableFulfillmentTagsEnhacements": False,
            "enableRxDrugScheduleModal": False,
            "enablePromoData": True,
            "enableAdsPromoData": False,
            "enableSeoLangUrl": False,
            "enableImageBannerCarousel": False,
            "enableHero4": False,
            "enableSeoBrowseMetaDataShortDesc": False,
            "enableCanAddToList": False,
            "enablePromotionMessages": False,
            "enableDebugAnalyticsTags": False,
            "enableSignInToSeePrice": False,
            "enableSimpleEmailSignUp": False,
            "enableModuleReposition": False,
            "enableUnifiedSchema": False,
            "version": "v1",
            "postProcessingVersion": 1
        }

        params = {
            "variables": json.dumps(variables, separators=(",", ":"))
        }
        response = requests.get(
            'https://www.walmart.com/orchestra/snb/graphql/Browse/5612fc04f0ced99ad21af9a34a07a79ec6378ac66879d5ea051d1ef5d737ff3e/browse',
            params=params,
            cookies=cookies,
            headers=headers,
        )

        print(f"Page {page} Status: {response.status_code}")

        if response.status_code != 200:
            break

        data = response.json()

        # Save page JSON
        with open(f"page_{page}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        try:
            search_result = data["data"]["search"]["searchResult"]

            total_pages = search_result["paginationV2"]["maxPage"]
            # total_pages = 1
            print(f"Total Pages: {total_pages}")

            itemsv2 = search_result["itemStacks"][0]["itemsV2"]

            for item in itemsv2:
                canonical_url = item.get("canonicalUrl")

                if canonical_url:
                    pdp_url = f"https://www.walmart.com{canonical_url}"
                    print("URL:::::", pdp_url)

        except Exception as e:
            print("Parsing Error:", e)
            break

        if page == 1:
            modules = data["data"]["contentLayout"]["modules"]
            for module in modules:
                if module["type"] == "PillsModule":
                    pillsv2 = module["configs"]["pillsV2"]
                    for pillv2 in pillsv2:
                        cat_url = pillv2["url"]
                        title = pillv2["title"]

                        print("url::::",title , cat_url)

        # Stop after last page
        if page >= total_pages:
            print("All pages completed")
            break


    # if page == 1:
    #     modules = data["data"]["contentLayout"]["modules"]
    #     for module in modules:
    #         if module["type"] == "SearchSortFilterModule":
    #             all_filters = module["configs"]["allSortAndFilterFacets"]
    #             for all_filter in all_filters:
    #                 if all_filter["title"] == "Brand":
    #                     all_brands = all_filter["values"]
    #                     for brand in all_brands:
    #                         brand_id = brand["id"]
    #                         print("brand:::", brand_id)
    #                         brand_lst.append(brand_id)





    page += 1


def get_sub_category_links(main_url,cat_id):
    cookies = {
          'AID': 'wmlspartner=0:reflectorid=0000000000000000000000:lastupd=1778845670611',
          'ACID': '95ba3c37-135f-4fad-bcfc-f8010ddea74d',
          '_m': '9',
          'hasACID': 'true',
          'hasLocData': '1',
          'locDataV3': '***HIDDEN***',
          'locGuestData': '***HIDDEN***',
          'userAppVersion': '***HIDDEN***',
          'abqme': 'true',
          'vtc': 'e9sIRi2Le_kHFERQL2t84Y',
          '_pxhd': '***HIDDEN***',
          'adblocked': 'false',
          '_pxvid': '***HIDDEN***',
          'io_id': 'dd94c1e9-908b-4e4e-8fc9-51e48a9865df',
          'dimensionData': '641',
          'bstc': 'SM4v7m_DoCAv3E-0t8cCNI',
          'xpa': '1K-QU|1keyc|1yTUd|30Fw1|5-CaB|5lkg6|CA1jM|Dibla|Gr8kp|J0bU2|J0eUl|KQLX-|NOHmU|REv1S|Swr3R|UrkGc|_yYS_|_zFl1|fdm-7|jIKKp|jM1ax|jVixg|louGn|ncMv9|qQ9d7|r2_te|ruRu0|t04it|xUczm|xy5c4|yAlwq|zKxms',
          'exp-ck': '1K-QU11keyc130Fw12CA1jM2Gr8kp3J0bU21J0eUl1KQLX-1NOHmU1Swr3R1UrkGc1_zFl11fdm-71jIKKp1jVixg1ncMv93r2_te1ruRu01t04it1xUczm1xy5c42yAlwq1zKxms1',
          'isoLoc': 'IN_GJ_t3',
          'ak_bmsc': '***HIDDEN***',
          '_intlbu': 'false',
          '_shcc': 'US',
          'xpth': 'x-o-mart%2BB2C~x-o-mverified%2Bfalse',
          'bm_mi': '***HIDDEN***',
          'pxcts': '***HIDDEN***',
          '_astc': '***HIDDEN***',
          'assortmentStoreId': '757',
          'xptwj': '***HIDDEN***',
          'akavpau_p1': '***HIDDEN***',
          'akavpau_p2': '***HIDDEN***',
          'xpm': '1%2B1779080537%2Be9sIRi2Le_kHFERQL2t84Y~%2B0',
          'if_id': '***HIDDEN***',
          'TS016ef4c8': '***HIDDEN***',
          'TS01f89308': '***HIDDEN***',
          'TS8cb5a80e027': '***HIDDEN***',
          'com.wm.reflector': '"reflectorid:0000000000000000000000@lastupd:1779080844000@firstcreate:1778845670611"',
          'xptc': 'assortmentStoreId%2B757~_m%2B9',
          'xptwg': '2410138118:271FB07E55B51C0:5E735F6:50D84E0B:4C2A15C7:73952627:',
          'TS012768cf': '***HIDDEN***',
          'TS01a90220': '***HIDDEN***',
          'TS2a5e0c5c027': '***HIDDEN***',
          'bm_sv': '***HIDDEN***',
      }
    headers = {
        'accept': 'application/json',
        'accept-language': 'en-US',
        'baggage': '***HIDDEN***',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'device-memory': '32',
        'downlink': '10',
        'dpr': '1',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://www.walmart.com/browse/food/shop-all-rice/976759_976794_4879140_8850682_3061688?seo=food&seo=shop-all-rice&seo=976759_976794_4879140_8850682_3061688&page=2&affinityOverride=default',
        'sec-ch-device-memory': '32',
        'sec-ch-dpr': '1',
        'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'tenant-id': 'elh9ie',
        'traceparent': '***HIDDEN***',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        'wm-client-traceid': '***HIDDEN***',
        'wm_mp': 'true',
        'wm_page_url': 'https://www.walmart.com/browse/food/shop-all-rice/976759_976794_4879140_8850682_3061688?seo=food&seo=shop-all-rice&seo=976759_976794_4879140_8850682_3061688&page=2&affinityOverride=default',
        'wm_qos.correlation_id': 'q4y_HBSOYFSjV6IAP2FpAehrE2B_tUiHG_vu',
        'x-apollo-operation-name': 'Browse',
        'x-enable-server-timing': '1',
        'x-latency-trace': '1',
        'x-o-bu': 'WALMART-US',
        'x-o-ccm': 'server',
        'x-o-correlation-id': 'q4y_HBSOYFSjV6IAP2FpAehrE2B_tUiHG_vu',
        'x-o-gql-query': 'query Browse',
        'x-o-mart': 'B2C',
        'x-o-platform': 'rweb',
        'x-o-platform-version': '***HIDDEN***',
        'x-o-segment': 'oaoh',
        # 'cookie': '***HIDDEN***',
    }
    page = 1
    variables = {
        "id": "",
        "affinityOverride": "default",
        "pap": "{\"polaris\":{\"ms_triggered\":false}}",
        "dealsId": "",
        "query": "",
        "nudgeContext": "",
        "page": page,
        "prg": "desktop",
        "catId": cat_id,
        "facet": "",
        "sort": "best_match",
        "rawFacet": "",
        "seoPath": "",
        "ps": 40,
        "limit": 40,
        "ptss": "",
        "trsp": "",
        "beShelfId": "",
        "recall_set": "",
        "module_search": "",
        "min_price": "",
        "max_price": "",
        "storeSlotBooked": "",

        "additionalQueryParams": {
            "hidden_facet": None,
            "translation": None,
            "isMoreOptionsTileEnabled": True,
            "rootDimension": "",
            "altQuery": "",
            "selectedFilter": "",
            "neuralSearchSeeAll": False,
            "isLMPBrowsePage": False
        },

        "searchArgs": {
            "query": "",
            "cat_id": cat_id,
            "prg": "desktop",
            "facet": ""
        },

        "enableCopyBlock": True,
        "enableVariantCount": False,
        "enableSlaBadgeV2": True,
        "enableUnifiedProductFragment": False,
        "enableESSCarousel": False,

        "fitmentFieldParams": {
            "powerSportEnabled": True,
            "dynamicFitmentEnabled": True,
            "extendedAttributesEnabled": True,
            "extendedAttributesV2Enabled": False,
            "fuelTypeEnabled": True
        },

        "fitmentSearchParams": {
            "id": "",
            "affinityOverride": "default",
            "pap": "{\"polaris\":{\"ms_triggered\":false}}",
            "dealsId": "",
            "query": "",
            "nudgeContext": "",
            "page": page,
            "prg": "desktop",
            "catId": cat_id,
            "facet": "",
            "sort": "best_match",
            "rawFacet": "",
            "seoPath": "",
            "ps": 40,
            "limit": 40,
            "ptss": "",
            "trsp": "",
            "beShelfId": "",
            "recall_set": "",
            "module_search": "",
            "min_price": "",
            "max_price": "",
            "storeSlotBooked": "",

            "additionalQueryParams": {
                "hidden_facet": None,
                "translation": None,
                "isMoreOptionsTileEnabled": True,
                "rootDimension": "",
                "altQuery": "",
                "selectedFilter": "",
                "neuralSearchSeeAll": False,
                "isLMPBrowsePage": False
            },

            "searchArgs": {
                "query": "",
                "cat_id": cat_id,
                "prg": "desktop",
                "facet": ""
            },

            "enableCopyBlock": True,
            "enableVariantCount": False,
            "enableSlaBadgeV2": True,
            "enableUnifiedProductFragment": False,
            "enableESSCarousel": False,
            "cat_id": cat_id,
            "_be_shelf_id": ""
        },

        "searchParams": {
            "id": "",
            "affinityOverride": "default",
            "pap": "{\"polaris\":{\"ms_triggered\":false}}",
            "dealsId": "",
            "query": "",
            "nudgeContext": "",
            "page": page,
            "prg": "desktop",
            "catId": cat_id,
            "facet": "",
            "sort": "best_match",
            "rawFacet": "",
            "seoPath": "",
            "ps": 40,
            "limit": 40,
            "ptss": "",
            "trsp": "",
            "beShelfId": "",
            "recall_set": "",
            "module_search": "",
            "min_price": "",
            "max_price": "",
            "storeSlotBooked": "",

            "additionalQueryParams": {
                "hidden_facet": None,
                "translation": None,
                "isMoreOptionsTileEnabled": True,
                "rootDimension": "",
                "altQuery": "",
                "selectedFilter": "",
                "neuralSearchSeeAll": False,
                "isLMPBrowsePage": False
            },

            "searchArgs": {
                "query": "",
                "cat_id": cat_id,
                "prg": "desktop",
                "facet": ""
            },

            "enableCopyBlock": True,
            "enableVariantCount": False,
            "enableSlaBadgeV2": True,
            "enableUnifiedProductFragment": False,
            "enableESSCarousel": False,
            "cat_id": cat_id,
            "_be_shelf_id": ""
        },

        "enableFashionTopNav": False,
        "fetchMarquee": True,
        "fetchSkyline": True,
        "fetchSbaTop": True,
        "fetchDataV1": True,
        "fetchDataV2": False,
        "fungibilityEnabled": False,
        "fetchGallery": False,
        "fetchDac": True,
        "enablePortableFacets": True,
        "tenant": "WM_GLASS",
        "pageType": "BrowsePage",
        "enableFacetCount": True,
        "enableMultiSave": False,
        "enableInStoreShelfMessage": False,
        "fSeo": True,
        "enableSellerType": False,
        "enableItemRank": False,
        "enableOptimisticWeightUpdate": False,
        "enableFulfillmentTagsEnhacements": False,
        "enableRxDrugScheduleModal": False,
        "enablePromoData": True,
        "enableAdsPromoData": False,
        "enableSeoLangUrl": False,
        "enableImageBannerCarousel": False,
        "enableHero4": False,
        "enableSeoBrowseMetaDataShortDesc": False,
        "enableCanAddToList": False,
        "enablePromotionMessages": False,
        "enableDebugAnalyticsTags": False,
        "enableSignInToSeePrice": False,
        "enableSimpleEmailSignUp": False,
        "enableModuleReposition": False,
        "enableUnifiedSchema": False,
        "version": "v1",
        "postProcessingVersion": 1
    }
    file_path = os.path.join(CAT_PAGESAVE, f"{cat_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        params = {
            "variables": json.dumps(variables, separators=(",", ":"))
        }
        # 'variables': '{"id":"","affinityOverride":"default","pap":"{\\"polaris\\":{\\"ms_triggered\\":false}}","dealsId":"","query":"","nudgeContext":"","page":2,"prg":"desktop","catId":"976759_976780_5837233","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isLMPBrowsePage":false},"searchArgs":{"query":"","cat_id":"976759_976780_5837233","prg":"desktop","facet":""},"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":true,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"fitmentFieldParams":{"powerSportEnabled":true,"dynamicFitmentEnabled":true,"extendedAttributesEnabled":true,"extendedAttributesV2Enabled":false,"fuelTypeEnabled":true},"fitmentSearchParams":{"id":"","affinityOverride":"default","pap":"{\\"polaris\\":{\\"ms_triggered\\":false}}","dealsId":"","query":"","nudgeContext":"","page":2,"prg":"desktop","catId":"976759_976780_5837233","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isLMPBrowsePage":false},"searchArgs":{"query":"","cat_id":"976759_976780_5837233","prg":"desktop","facet":""},"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":true,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":"976759_976780_5837233","_be_shelf_id":""},"searchParams":{"id":"","affinityOverride":"default","pap":"{\\"polaris\\":{\\"ms_triggered\\":false}}","dealsId":"","query":"","nudgeContext":"","page":2,"prg":"desktop","catId":"976759_976780_5837233","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isLMPBrowsePage":false},"searchArgs":{"query":"","cat_id":"976759_976780_5837233","prg":"desktop","facet":""},"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":true,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":"976759_976780_5837233","_be_shelf_id":""},"enableFashionTopNav":false,"fetchMarquee":true,"fetchSkyline":true,"fetchSbaTop":true,"fetchDataV1":true,"fetchDataV2":false,"fungibilityEnabled":false,"fetchGallery":false,"fetchDac":true,"enablePortableFacets":true,"tenant":"WM_GLASS","pageType":"BrowsePage","enableFacetCount":true,"enableMultiSave":false,"enableInStoreShelfMessage":false,"fSeo":true,"enableSellerType":false,"enableItemRank":false,"enableOptimisticWeightUpdate":false,"enableFulfillmentTagsEnhacements":false,"enableRxDrugScheduleModal":false,"enablePromoData":true,"enableAdsPromoData":false,"enableSeoLangUrl":false,"enableImageBannerCarousel":false,"enableHero4":false,"enableSeoBrowseMetaDataShortDesc":false,"enableCanAddToList":false,"enablePromotionMessages":false,"enableDebugAnalyticsTags":false,"enableSignInToSeePrice":false,"enableSimpleEmailSignUp":false,"enableModuleReposition":false,"enableUnifiedSchema":false,"version":"v1","postProcessingVersion":1}',
        response = requests.get(
            'https://www.walmart.com/orchestra/snb/graphql/Browse/5612fc04f0ced99ad21af9a34a07a79ec6378ac66879d5ea051d1ef5d737ff3e/browse',
            params=params,
            cookies=cookies,
            headers=headers,
        )
        print(f"Page {page} Status: {response.status_code}")
        if response.status_code != 200:
            return response.status_code
        data = response.json()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    modules = data["data"]["contentLayout"]["modules"]
    # main_category = data["data"]["search"]["searchResult"]["shelfData"]["shelfName"]
    search_result = data["data"]["search"]["searchResult"]
    main_category = (
            search_result.get("shelfData", {}).get("shelfName")
            or ":".join(
        crumb.get("name", "")
        for crumb in search_result.get("breadCrumb", [])
        if crumb.get("name")
    )
    )
    total_count =search_result.get("aggregatedCount", None)
    for module in modules:
        if module["type"] == "PillsModule":
            pillsv2 = module["configs"]["pillsV2"]
            print(pillsv2)
            for pillv2 in pillsv2:
                cat_url = pillv2["url"]
                title = pillv2["title"]
                if cat_url.startswith("sort="):
                    cat_url = f"{main_url}?{cat_url}"
                print("url::::", title, cat_url)
                insert_category_data(main_url=main_url,main_category=main_category,subcategory_url=cat_url, category_id=cat_id, title=title, type="sub category", total_count=total_count, status='pending')



if __name__ == '__main__':
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # Fetch pending rows
        query = f"""
            SELECT id, pl_url
            FROM {db.input_table}
            WHERE status = 'pending'
              AND pl_url IS NOT NULL
              AND pl_url != 'N/A'
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("No pending category found.")
            exit()
        for row in rows:
            row_id = row["id"]
            main_url = row["pl_url"]
            try:
                # cat_id = main_url.rstrip("/").split("/")[-1]
                cat_id = main_url.rstrip("/").split("/")[-1].split("?")[0]
                print("=" * 80)
                print(f"Processing ID: {row_id}")
                print(f"URL: {main_url}")
                print(f"CAT ID: {cat_id}")
                # Run scraper
                result = get_sub_category_links(main_url, str(cat_id))
                # If successful update status
                if result != 500:
                    update_query = f"""
                        UPDATE {db.input_table}
                        SET status = 'completed',
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    cursor.execute(update_query, (row_id,))
                    conn.commit()
                    print(f"ID {row_id} completed.")
                else:
                    fail_query = f"""
                        UPDATE {db.input_table}
                        SET status = 'failed',
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    cursor.execute(fail_query, (row_id,))
                    conn.commit()
                    print(f"ID {row_id} failed.")
            except Exception as e:
                print(f"Error processing ID {row_id}: {e}")
                fail_query = f"""
                    UPDATE {db.input_table}
                    SET status = 'failed',
                        updated_at = NOW()
                    WHERE id = %s
                """
                cursor.execute(fail_query, (row_id,))
                conn.commit()
    finally:
        cursor.close()
        conn.close()

    # conn = db.get_db_connection(db.db_name)
    # cursor = conn.cursor(pymysql.cursors.DictCursor)
    # query = f""" SELECT * FROM {db.input_table} WHERE status = 'pending' """
    # cursor.execute(query)
    # rows = cursor.fetchall()
    # cursor.close()
    # conn.close()
    # if not rows:
    #     print("No pending product found.")
    # # urls = [
    # #     "https://www.walmart.com/browse/food/shop-all-rice/976759_976794_4879140_8850682_3061688",
    # #     "https://www.walmart.com/browse/food/pasta/976759_976794_3246797",
    # #     "https://www.walmart.com/browse/food/oatmeal-grits/976759_976783_7830606",
    # #     "https://www.walmart.com/browse/food/canned-goods/976759_976794_7433209",
    # #     "https://www.walmart.com/browse/food/condiments/976759_976794_7981173",
    # #     "https://www.walmart.com/browse/food/everyday-baking-essentials/976759_976780_5837233",
    # #     "https://www.walmart.com/browse/food/baking-chips/976759_976780_9959366_2710937",
    # #     "https://www.walmart.com/browse/food/cereal/976759_976783_8102529_4007132",
    # #     "https://www.walmart.com/browse/food/evoo/976759_976780_9959366_8252266_1842511",
    # #     "https://www.walmart.com/browse/food/avocado-oils/976759_976780_9959366_8252266_7081953",
    # #     "https://www.walmart.com/browse/food/canola-oils/976759_976780_9959366_8252266_8835608",
    # #     "https://www.walmart.com/browse/food/vegetable-oils/976759_976780_9959366_8252266_5676849",
    # #     "https://www.walmart.com/browse/food/peanut-oil/976759_976780_9959366_8252266_5667871",
    # #     "https://www.walmart.com/browse/food/cooking-oils/976759_976794_4649724_8048373",
    # #     "https://www.walmart.com/browse/food/snack-cakes/976759_976787_1001398",
    # #     "https://www.walmart.com/browse/food/fruit-snacks/976759_976787_1001395",
    # #     "https://www.walmart.com/browse/food/feel-good-snacks/976759_5004481_9769485",
    # #     "https://www.walmart.com/browse/food/frozen-meals/976759_976791_6259087",
    # #     "https://www.walmart.com/browse/food/ice-cream-novelties/976759_976791_1518625",
    # #     "https://www.walmart.com/browse/frozen-foods/frozen-desserts/976759_976791_9551235",
    # #     "https://www.walmart.com/browse/laundry/1115193_1071967",
    # #     "https://www.walmart.com/browse/food/bakery-bread/976759_976779",
    # #     "https://www.walmart.com/browse/food/coffee-and-tea/976759_1086446_5588831",
    # #     "https://www.walmart.com/browse/food/sports-drinks/976759_976782_1001682",
    # #     "https://www.walmart.com/browse/food/organic-produce/976759_976793_1913529",
    # #     "https://www.walmart.com/browse/food/international-foods/976759_976794_3854465",
    # #     "https://www.walmart.com/browse/food/herbs-spices-seasoning-mixes/976759_976794_3029941",
    # #     "https://www.walmart.com/browse/food/bbq-sauces-seasonings-marinades/976759_976794_5437393",
    # #     "https://www.walmart.com/browse/health/keto/976760_7501265_1974068",
    # #     "https://www.walmart.com/browse/food/gluten-free/976759_5004481_5546296"
    # # ]
    # for main_url in urls:
    #     cat_id = main_url.split("/")[-1]
    #     print(cat_id)
    #     get_sub_category_links(main_url,str(cat_id))



