import requests
import json
import os
import time
import random

import db_config as db
import headers_cookies as hc

from glom import glom


# =========================
# SAVE DATA
# =========================

def save_data_db(items):
    try:
        con = db.get_db_connection(db.db_name)
        cur = con.cursor()

        for item in items:

            for k, v in item.items():
                if not v:
                    item[k] = "N/A"

            cols = ", ".join(item.keys()).strip(', ')
            values = tuple(item.values())

            try:
                insert_active = f"""
                INSERT INTO {db.link_table} ({cols})
                VALUES {values}
                """

                cur.execute(insert_active)
                con.commit()

                print('inserted ->', item['product_url'])

            except Exception as e:
                print("DB Insert Error:", e)

    except Exception as e:
        print("DB Connection Error:", e)

    finally:
        try:
            cur.close()
            con.close()
        except:
            pass


# =========================
# BUILD PAYLOAD
# =========================

def build_payload(keyword, page_no, limit=40):

    payload = {
        "id": "",
        "affinityOverride": "store_led",
        "dealsId": "",
        "query": keyword,
        "nudgeContext": "",
        "page": page_no,
        "prg": "desktop",
        "catId": "",
        "facet": "",
        "sort": "best_match",
        "rawFacet": "",
        "seoPath": "",
        "ps": limit,
        "limit": limit,
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
            "isGenAiEnabled": True,
            "rootDimension": "",
            "altQuery": "",
            "selectedFilter": "",
            "neuralSearchSeeAll": False,
            "isModuleArrayReq": False,
            "isLMPBrowsePage": False
        },

        "searchArgs": {
            "query": keyword,
            "cat_id": "",
            "prg": "desktop",
            "facet": ""
        },

        "ffAwareSearchOptOut": False,

        "enableDesktopHighlights": False,
        "enableVolumePricing": False,
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

        "fitmentSearchParams": {},

        "searchParams": {},

        "enableFashionTopNav": False,
        "enableUnifiedSchema": True,

        "postProcessingVersion": 2,
        "version": "v2",

        "enableRelatedSearches": True,
        "enablePortableFacets": True,
        "enableFacetCount": True,

        "fetchMarquee": True,
        "fetchSkyline": True,
        "fetchGallery": False,
        "fetchSbaTop": True,

        "fetchDataV1": True,
        "fetchDataV2": False,

        "fungibilityEnabled": False,

        "enableAdsPromoData": False,
        "fetchDac": True,

        "tenant": "WM_GLASS",

        "enableMultiSave": False,
        "enableInStoreShelfMessage": False,
        "enableSellerType": False,
        "enableItemRank": False,
        "enableOptimisticWeightUpdate": False,
        "enableAdditionalSearchDepartmentAnalytics": True,
        "enableFulfillmentTagsEnhacements": False,
        "enableRxDrugScheduleModal": False,
        "enablePromoData": True,
        "enableSignInToSeePrice": False,
        "enablePromotionMessages": False,
        "enableDebugAnalyticsTags": False,
        "enableItemLimits": False,
        "enableCanAddToList": False,
        "enableIsFreeWarranty": False,
        "enableShopSimilarBottomSheet": False,

        "adsParams": {
            "fungibilityEnabled": False
        },

        "pageType": "SearchPage"
    }

    # IMPORTANT:
    # Walmart expects these nested payloads too

    payload["fitmentSearchParams"] = {
        **payload,
        "fitmentSearchParams": {},
        "searchParams": {}
    }

    payload["searchParams"] = {
        **payload,
        "fitmentSearchParams": {},
        "searchParams": {}
    }

    return payload


# =========================
# FETCH RESPONSE
# =========================

def fetch_response(page_no, sku, keyword, brand):

    file_loc = f"{db.page_save_path}\\PL\\"

    os.makedirs(file_loc, exist_ok=True)

    file_name = fr"{file_loc}\\{keyword}_{brand}_{page_no}.json.gz"

    # =========================
    # CACHE
    # =========================

    if os.path.exists(file_name):

        print("Loaded from cache")

        return json.loads(db.read_page(file_name))

    # =========================
    # HEADERS
    # =========================

    h = hc.headers_pl.copy()

    if brand:
        url = f"https://www.walmart.com/search?q={sku}&facet=brand%3A{brand}&page={page_no}"
    else:
        url = f"https://www.walmart.com/search?q={sku}&page={page_no}"

    h['wm_page_url'] = url

    # =========================
    # PAYLOAD
    # =========================

    payload = build_payload(
        keyword=keyword,
        page_no=page_no,
        limit=40
    )

    params = {
        "variables": json.dumps(
            payload,
            separators=(",", ":")
        )
    }

    # =========================
    # REQUEST
    # =========================

    try:

        response = requests.get(
            "https://www.walmart.com/orchestra/snb/graphql/Search/7bf57a3d34085376704f3b81b0a118cedef00b02cc8b6fe0b512c7fc5d9e80fc/search",
            params=params,
            cookies=hc.cookies_pl,
            headers=h,
            timeout=60
        )

        print("STATUS:", response.status_code)

        if response.status_code == 200:

            db.save_page(
                file_name=file_name,
                response=response.text
            )

            return response.json()

        else:

            print(f"Failed Page [{page_no}] -> {response.status_code}")

            print(response.text[:500])

            return None

    except Exception as e:

        print("Request Error:", e)

        return None


# =========================
# EXTRACT DATA
# =========================

def extract_data(json_data, page_no, brand):

    scraped_data = []

    if not json_data:
        return scraped_data

    try:

        item_stacks = glom(
            json_data,
            "data.search.searchResult.itemStacks",
            default=[]
        )

        for stack in item_stacks:

            for product in stack.get("itemsV2", []):

                try:

                    if "Product" not in product.get("__typename", ""):
                        continue

                    item = {}

                    # =========================
                    # PRICE
                    # =========================

                    price = glom(
                        product,
                        "priceInfo.currentPrice.price",
                        default="N/A"
                    )

                    mrp = glom(
                        product,
                        "priceInfo.listPrice.price",
                        default="N/A"
                    )

                    if mrp == "N/A":
                        mrp = price

                    price_discount = "N/A"

                    if isinstance(price, (int, float)) and isinstance(mrp, (int, float)):
                        if mrp > price:
                            price_discount = round(mrp - price, 2)

                    # =========================
                    # IMAGE
                    # =========================

                    image_url = glom(
                        product,
                        "imageInfo.thumbnailUrl",
                        default="N/A"
                    )

                    if "jpeg?" in image_url:
                        image_url = image_url.split("jpeg?")[0] + "jpeg"

                    # =========================
                    # PRODUCT
                    # =========================

                    canonical_url = product.get("canonicalUrl", "")

                    product_url = (
                        f"https://www.walmart.com{canonical_url}"
                        if canonical_url else "N/A"
                    )

                    product_id = "N/A"

                    if canonical_url:
                        product_id = (
                            canonical_url
                            .split("?")[0]
                            .split("/")[-1]
                            .strip()
                        )

                    item['main_image'] = image_url
                    item['product_name'] = product.get("name", "N/A")
                    item['product_price'] = price
                    item['price_per_unit'] = glom(
                        product,
                        "priceInfo.unitPrice.priceString",
                        default="N/A"
                    )

                    item['price_discount'] = price_discount
                    item['avg_rating'] = product.get("averageRating", "N/A")
                    item['num_review'] = product.get("numberOfReviews", "N/A")

                    item['page_num'] = page_no

                    item['sponsored'] = (
                        "Yes"
                        if product.get("sponsoredProduct")
                        else "No"
                    )

                    item['product_url'] = product_url
                    item['product_id'] = product_id

                    item['product_mrp'] = mrp

                    item['brand'] = brand

                    scraped_data.append(item)

                except Exception as e:
                    print("Product Parse Error:", e)

    except Exception as e:

        print("Extract Error:", e)

    return scraped_data


# =========================
# MAIN
# =========================

def main(record):

    keyword = record['keyword']

    sku = keyword.replace(" ", "+")

    page_no = 1

    total_products = 0

    while True:

        print("\n")
        print("=" * 60)
        print(f"Sending Request Page -> {page_no}")
        print("=" * 60)

        json_data = fetch_response(
            page_no=page_no,
            sku=sku,
            keyword=keyword,
            brand=""
        )

        if not json_data:

            print("No JSON Response")
            break

        items = extract_data(
            json_data=json_data,
            page_no=page_no,
            brand=""
        )

        if not items:

            print("No More Products")
            break

        print(f"Extracted Products -> {len(items)}")

        total_products += len(items)

        # =========================
        # SAVE
        # =========================

        save_data_db(items)

        # =========================
        # NEXT PAGE
        # =========================

        page_no += 1

        # =========================
        # DELAY
        # =========================

        sleep_time = random.uniform(2, 5)

        print(f"Sleeping {round(sleep_time, 2)} sec")

        time.sleep(sleep_time)

    print("\n")
    print("=" * 60)
    print(f"TOTAL PRODUCTS -> {total_products}")
    print("=" * 60)


# =========================
# START
# =========================

if __name__ == "__main__":

    main({
        'keyword': "Soda"
    })


# import requests
# import json
# import os
# import db_config as db
# import headers_cookies as hc
# from glom import glom
#
#
# def save_data_db(items):
#     try:
#         con = db.get_db_connection(db.db_name)
#         cur = con.cursor()
#         for item in items:
#             for k, v in item.items():
#                 if not v:
#                     item[k] = "N/A"
#             cols = ", ".join(item.keys()).strip(', ')
#             values = tuple(item.values())
#             try:
#                 insert_active = f"""INSERT INTO {db.link_table} ({cols}) VALUES {values}"""
#                 cur.execute(insert_active)
#                 con.commit()
#                 print('inserted', item['product_url'])
#             except Exception as e:
#                 print(e)
#     except Exception as e:
#         print(e)
#     finally:
#         cur.close()
#         con.close()
#
#
# def build_payload(keyword, page_no, limit=40):
#     payload = {
#         "id": "",
#         "affinityOverride": "store_led",
#         "dealsId": "",
#         "query": keyword,
#         "nudgeContext": "",
#         "page": page_no,
#         "prg": "desktop",
#         "catId": "",
#         "facet": "",
#         "sort": "best_match",
#         "rawFacet": "",
#         "seoPath": "",
#         "ps": limit,
#         "limit": limit,
#         "ptss": "",
#         "trsp": "",
#         "beShelfId": "",
#         "recall_set": "",
#         "module_search": "",
#         "min_price": "",
#         "max_price": "",
#         "storeSlotBooked": "",
#
#         "additionalQueryParams": {
#             "hidden_facet": None,
#             "translation": None,
#             "isMoreOptionsTileEnabled": True,
#             "isGenAiEnabled": True,
#             "rootDimension": "",
#             "altQuery": "",
#             "selectedFilter": "",
#             "neuralSearchSeeAll": False,
#             "isModuleArrayReq": False,
#             "isLMPBrowsePage": False
#         },
#
#         "searchArgs": {
#             "query": keyword,
#             "cat_id": "",
#             "prg": "desktop",
#             "facet": ""
#         },
#
#         "enableDesktopHighlights": False,
#         "enableVolumePricing": False,
#         "enableCopyBlock": True,
#         "enableVariantCount": False,
#         "enableSlaBadgeV2": True,
#         "enableUnifiedProductFragment": False,
#         "enableESSCarousel": False,
#
#         "fitmentFieldParams": {
#             "powerSportEnabled": True,
#             "dynamicFitmentEnabled": True,
#             "extendedAttributesEnabled": True,
#             "extendedAttributesV2Enabled": False,
#             "fuelTypeEnabled": True
#         },
#
#         "fitmentSearchParams": {},
#
#         "searchParams": {},
#
#         "enableFashionTopNav": False,
#         "enableUnifiedSchema": True,
#         "postProcessingVersion": 2,
#         "version": "v2",
#
#         "enableRelatedSearches": True,
#         "enablePortableFacets": True,
#         "enableFacetCount": True,
#
#         "fetchMarquee": True,
#         "fetchSkyline": True,
#         "fetchGallery": False,
#         "fetchSbaTop": True,
#
#         "fetchDataV1": True,
#         "fetchDataV2": False,
#
#         "fungibilityEnabled": False,
#         "enableAdsPromoData": False,
#         "fetchDac": True,
#
#         "tenant": "WM_GLASS",
#
#         "enableMultiSave": False,
#         "enableInStoreShelfMessage": False,
#         "enableSellerType": False,
#         "enableItemRank": False,
#         "enableOptimisticWeightUpdate": False,
#         "enableAdditionalSearchDepartmentAnalytics": True,
#         "enableFulfillmentTagsEnhacements": False,
#         "enableRxDrugScheduleModal": False,
#         "enablePromoData": True,
#         "enableSignInToSeePrice": False,
#         "enablePromotionMessages": False,
#         "enableDebugAnalyticsTags": False,
#         "enableItemLimits": False,
#         "enableCanAddToList": False,
#         "enableIsFreeWarranty": False,
#         "enableShopSimilarBottomSheet": False,
#
#         "adsParams": {
#             "fungibilityEnabled": False
#         },
#
#         "pageType": "SearchPage"
#     }
#
#     # IMPORTANT
#     payload["fitmentSearchParams"] = payload.copy()
#     payload["searchParams"] = payload.copy()
#
#     return payload
#
#
# def fetch_response(page_no, sku, keyword, brand):
#     file_loc = f"{db.page_save_path}\\PL\\"
#     os.makedirs(file_loc, exist_ok=True)
#     file_name = fr"{file_loc}\\{keyword}_{brand}_{page_no}.json.gz"
#     if os.path.exists(file_name):
#         return json.loads(db.read_page(file_name))
#     else:
#         h = hc.headers_pl.copy()
#         if page_no > 1:
#             params = {
#                 'variables': '{"id":"","affinityOverride":"store_led","dealsId":"","query":"soda","nudgeContext":"","page":2,"prg":"desktop","catId":"","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"isGenAiEnabled":false,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isModuleArrayReq":false,"isLMPBrowsePage":false},"searchArgs":{"query":"soda","cat_id":"","prg":"desktop","facet":""},"enableDesktopHighlights":false,"enableVolumePricing":false,"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":false,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"fitmentFieldParams":{"powerSportEnabled":true,"dynamicFitmentEnabled":true,"extendedAttributesEnabled":false,"extendedAttributesV2Enabled":false,"fuelTypeEnabled":false},"fitmentSearchParams":{"id":"","affinityOverride":"store_led","dealsId":"","query":"soda","nudgeContext":"","page":2,"prg":"desktop","catId":"","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"isGenAiEnabled":false,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isModuleArrayReq":false,"isLMPBrowsePage":false},"searchArgs":{"query":"soda","cat_id":"","prg":"desktop","facet":""},"enableDesktopHighlights":false,"enableVolumePricing":false,"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":false,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":"","_be_shelf_id":""},"searchParams":{"id":"","affinityOverride":"store_led","dealsId":"","query":"soda","nudgeContext":"","page":2,"prg":"desktop","catId":"","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"isGenAiEnabled":false,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isModuleArrayReq":false,"isLMPBrowsePage":false},"searchArgs":{"query":"soda","cat_id":"","prg":"desktop","facet":""},"enableDesktopHighlights":false,"enableVolumePricing":false,"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":false,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":"","_be_shelf_id":""},"enableFashionTopNav":false,"enableUnifiedSchema":false,"postProcessingVersion":1,"version":"v1","enableRelatedSearches":false,"enablePortableFacets":false,"enableFacetCount":true,"fetchMarquee":true,"fetchSkyline":true,"fetchGallery":false,"fetchSbaTop":true,"fetchDataV1":false,"fetchDataV2":false,"fungibilityEnabled":false,"enableAdsPromoData":false,"fetchDac":false,"tenant":"WM_GLASS","enableMultiSave":false,"enableInStoreShelfMessage":false,"enableSellerType":false,"enableItemRank":false,"enableOptimisticWeightUpdate":false,"enableAdditionalSearchDepartmentAnalytics":false,"enableFulfillmentTagsEnhacements":false,"enableRxDrugScheduleModal":false,"enablePromoData":false,"enableSignInToSeePrice":false,"enablePromotionMessages":false,"enableDebugAnalyticsTags":false,"enableItemLimits":false,"enableCanAddToList":false,"enableIsFreeWarranty":false,"enableShopSimilarBottomSheet":false,"adsParams":{"fungibilityEnabled":false},"pageType":"SearchPage"}',
#             }
#             # params = {
#             #     'variables': '{"id":"","affinityOverride":"default","pap":"{\\"polaris\\":{\\"ms_triggered\\":true}}","dealsId":"","query":"Coffee Makers","nudgeContext":"","page":2,"prg":"desktop","catId":"","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"isGenAiEnabled":true,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isModuleArrayReq":false,"isLMPBrowsePage":false},"searchArgs":{"query":"Coffee Makers","cat_id":"","prg":"desktop","facet":""},"ffAwareSearchOptOut":false,"enableDesktopHighlights":false,"enableVolumePricing":false,"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":true,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"fitmentFieldParams":{"powerSportEnabled":true,"dynamicFitmentEnabled":true,"extendedAttributesEnabled":true,"extendedAttributesV2Enabled":false,"fuelTypeEnabled":true},"fitmentSearchParams":{"id":"","affinityOverride":"default","pap":"{\\"polaris\\":{\\"ms_triggered\\":true}}","dealsId":"","query":"Coffee Makers","nudgeContext":"","page":2,"prg":"desktop","catId":"","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"isGenAiEnabled":true,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isModuleArrayReq":false,"isLMPBrowsePage":false},"searchArgs":{"query":"Coffee Makers","cat_id":"","prg":"desktop","facet":""},"ffAwareSearchOptOut":false,"enableDesktopHighlights":false,"enableVolumePricing":false,"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":true,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":"","_be_shelf_id":""},"searchParams":{"id":"","affinityOverride":"default","pap":"{\\"polaris\\":{\\"ms_triggered\\":true}}","dealsId":"","query":"Coffee Makers","nudgeContext":"","page":2,"prg":"desktop","catId":"","facet":"","sort":"best_match","rawFacet":"","seoPath":"","ps":40,"limit":40,"ptss":"","trsp":"","beShelfId":"","recall_set":"","module_search":"","min_price":"","max_price":"","storeSlotBooked":"","additionalQueryParams":{"hidden_facet":null,"translation":null,"isMoreOptionsTileEnabled":true,"isGenAiEnabled":true,"rootDimension":"","altQuery":"","selectedFilter":"","neuralSearchSeeAll":false,"isModuleArrayReq":false,"isLMPBrowsePage":false},"searchArgs":{"query":"Coffee Makers","cat_id":"","prg":"desktop","facet":""},"ffAwareSearchOptOut":false,"enableDesktopHighlights":false,"enableVolumePricing":false,"enableCopyBlock":true,"enableVariantCount":false,"enableSlaBadgeV2":true,"enableUnifiedProductFragment":false,"enableESSCarousel":false,"cat_id":"","_be_shelf_id":""},"enableFashionTopNav":false,"enableUnifiedSchema":true,"postProcessingVersion":2,"version":"v2","enableRelatedSearches":true,"enablePortableFacets":true,"enableFacetCount":true,"fetchMarquee":true,"fetchSkyline":true,"fetchGallery":false,"fetchSbaTop":true,"fetchDataV1":true,"fetchDataV2":false,"fungibilityEnabled":false,"enableAdsPromoData":false,"fetchDac":true,"tenant":"WM_GLASS","enableMultiSave":false,"enableInStoreShelfMessage":false,"enableSellerType":false,"enableItemRank":false,"enableOptimisticWeightUpdate":false,"enableAdditionalSearchDepartmentAnalytics":true,"enableFulfillmentTagsEnhacements":false,"enableRxDrugScheduleModal":false,"enablePromoData":true,"enableSignInToSeePrice":false,"enablePromotionMessages":false,"enableDebugAnalyticsTags":false,"enableItemLimits":false,"enableCanAddToList":false,"enableIsFreeWarranty":false,"enableShopSimilarBottomSheet":false,"adsParams":{"fungibilityEnabled":false},"pageType":"SearchPage"}'.replace('"page":2,', f'"page":{page_no},'),
#             # }
#             url = f"https://www.walmart.com/search?q={sku}&facet=brand%3A{brand}&page={page_no}&affinityOverride=store_led"
#             h['wm_page_url'] = url
#         else:
#             json_data = {
#     "id": "",
#     "dealsId": "",
#     "query": keyword,
#     "nudgeContext": "",
#     "page": 1,
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
#     "additionalQueryParams": {
#         "hidden_facet": None,
#         "translation": None,
#         "isMoreOptionsTileEnabled": True,
#         "isGenAiEnabled": True,
#         "rootDimension": "",
#         "altQuery": "",
#         "selectedFilter": "",
#         "neuralSearchSeeAll": False,
#         "isModuleArrayReq": False,
#         "isLMPBrowsePage": False
#     },
#     "searchArgs": {
#         "query": keyword,
#         "cat_id": "",
#         "prg": "desktop",
#         "facet": ""
#     },
#     "ffAwareSearchOptOut": False,
#     "enableDesktopHighlights": False,
#     "enableVolumePricing": False,
#     "enableCopyBlock": True,
#     "enableVariantCount": False,
#     "enableSlaBadgeV2": True,
#     "enableUnifiedProductFragment": False,
#     "enableESSCarousel": False,
#     "fitmentFieldParams": {
#         "powerSportEnabled": True,
#         "dynamicFitmentEnabled": True,
#         "extendedAttributesEnabled": True,
#         "extendedAttributesV2Enabled": False,
#         "fuelTypeEnabled": True
#     },
#     "fitmentSearchParams": {
#         "id": "",
#         "dealsId": "",
#         "query": keyword,
#         "nudgeContext": "",
#         "page": 1,
#         "prg": "desktop",
#         "catId": "",
#         "facet": "",
#         "sort": "best_match",
#         "rawFacet": "",
#         "seoPath": "",
#         "ps": 40,
#         "limit": 40,
#         "ptss": "",
#         "trsp": "",
#         "beShelfId": "",
#         "recall_set": "",
#         "module_search": "",
#         "min_price": "",
#         "max_price": "",
#         "storeSlotBooked": "",
#         "additionalQueryParams": {
#             "hidden_facet": None,
#             "translation": None,
#             "isMoreOptionsTileEnabled": True,
#             "isGenAiEnabled": True,
#             "rootDimension": "",
#             "altQuery": "",
#             "selectedFilter": "",
#             "neuralSearchSeeAll": False,
#             "isModuleArrayReq": False,
#             "isLMPBrowsePage": False
#         },
#         "searchArgs": {
#             "query": keyword,
#             "cat_id": "",
#             "prg": "desktop",
#             "facet": ""
#         },
#         "ffAwareSearchOptOut": False,
#         "enableDesktopHighlights": False,
#         "enableVolumePricing": False,
#         "enableCopyBlock": True,
#         "enableVariantCount": False,
#         "enableSlaBadgeV2": True,
#         "enableUnifiedProductFragment": False,
#         "enableESSCarousel": False,
#         "cat_id": "",
#         "_be_shelf_id": ""
#     },
#     "searchParams": {
#         "id": "",
#         "dealsId": "",
#         "query": keyword,
#         "nudgeContext": "",
#         "page": 1,
#         "prg": "desktop",
#         "catId": "",
#         "facet": "",
#         "sort": "best_match",
#         "rawFacet": "",
#         "seoPath": "",
#         "ps": 40,
#         "limit": 40,
#         "ptss": "",
#         "trsp": "",
#         "beShelfId": "",
#         "recall_set": "",
#         "module_search": "",
#         "min_price": "",
#         "max_price": "",
#         "storeSlotBooked": "",
#         "additionalQueryParams": {
#             "hidden_facet": None,
#             "translation": None,
#             "isMoreOptionsTileEnabled": True,
#             "isGenAiEnabled": True,
#             "rootDimension": "",
#             "altQuery": "",
#             "selectedFilter": "",
#             "neuralSearchSeeAll": False,
#             "isModuleArrayReq": False,
#             "isLMPBrowsePage": False
#         },
#         "searchArgs": {
#             "query": keyword,
#             "cat_id": "",
#             "prg": "desktop",
#             "facet": ""
#         },
#         "ffAwareSearchOptOut": False,
#         "enableDesktopHighlights": False,
#         "enableVolumePricing": False,
#         "enableCopyBlock": True,
#         "enableVariantCount": False,
#         "enableSlaBadgeV2": True,
#         "enableUnifiedProductFragment": False,
#         "enableESSCarousel": False,
#         "cat_id": "",
#         "_be_shelf_id": ""
#     },
#     "enableFashionTopNav": False,
#     "enableUnifiedSchema": True,
#     "postProcessingVersion": 2,
#     "version": "v2",
#     "enableRelatedSearches": True,
#     "enablePortableFacets": True,
#     "enableFacetCount": True,
#     "fetchMarquee": True,
#     "fetchSkyline": True,
#     "fetchGallery": False,
#     "fetchSbaTop": True,
#     "fetchDataV1": True,
#     "fetchDataV2": False,
#     "fungibilityEnabled": False,
#     "enableAdsPromoData": False,
#     "fetchDac": True,
#     "tenant": "WM_GLASS",
#     "enableMultiSave": False,
#     "enableInStoreShelfMessage": False,
#     "enableSellerType": False,
#     "enableItemRank": False,
#     "enableOptimisticWeightUpdate": False,
#     "enableAdditionalSearchDepartmentAnalytics": True,
#     "enableFulfillmentTagsEnhacements": False,
#     "enableRxDrugScheduleModal": False,
#     "enablePromoData": True,
#     "enableSignInToSeePrice": False,
#     "enablePromotionMessages": False,
#     "enableDebugAnalyticsTags": False,
#     "enableItemLimits": False,
#     "enableCanAddToList": False,
#     "enableIsFreeWarranty": False,
#     "enableShopSimilarBottomSheet": False,
#     "adsParams": {
#         "fungibilityEnabled": False
#     },
#     "pageType": "SearchPage"
# }
#             url = f"https://www.walmart.com/search?q={sku}&facet=brand%3A{brand}"
#             h['wm_page_url'] = url
#             params = {
#                 'variables': json.dumps(json_data),
#             }
#         response = requests.get(
#             'https://www.walmart.com/orchestra/snb/graphql/Search/7bf57a3d34085376704f3b81b0a118cedef00b02cc8b6fe0b512c7fc5d9e80fc/search',
#             params=params,
#             cookies=hc.cookies_pl,
#             headers=h,
#         )
#         if response.status_code == 200:
#             db.save_page(file_name=file_name, response=response.text)
#             return response.json()
#         else:
#             print(f"Failed response form page[{page_no}]:", response.status_code)
#             return None
#
# def extract_data(json_data, page_no, brand) :
#     scraped_data = []
#     if json_data:
#         try:
#             for products in json_data['data']['search']['searchResult']['itemStacks']:
#                 for product in products['itemsV2']:
#                     if "Product" not in product['__typename']:
#                         continue
#                     try:
#                         item = {}
#                         price = glom(product, "priceInfo.currentPrice.price",default="N/A")
#                         mrp = glom(product,"priceInfo.listPrice.price",  default="N/A")
#                         if mrp == "N/A":
#                             mrp = price
#                         price_discount = "N/A"
#                         price = price if price != "N/A" else None
#                         mrp = mrp if mrp != "N/A" else None
#                         if mrp and price:
#                             if mrp > price:
#                                 price_discount = round(mrp - price, 2)
#                         item['main_image'] = glom(product,"imageInfo.thumbnailUrl",  default="N/A")
#                         if "jpeg?" in item['main_image']:
#                             item['main_image'] = item['main_image'].split("jpeg?")[0] + "jpeg"
#                         item['product_name'] = product['name']
#                         item['product_price'] = price if price else "N/A"
#                         item['price_per_unit'] = glom(product,"priceInfo.unitPrice.priceString",  default="N/A")
#                         item['price_discount'] = price_discount
#                         item['avg_rating'] = product.get("averageRating", "N/A")
#                         item['num_review'] = product.get("numberOfReviews", "N/A")
#                         item['page_num'] = page_no
#                         item['sponsored'] = "Yes" if product.get("sponsoredProduct", None) else "No"
#                         item['product_url'] = f"https://www.walmart.com{product['canonicalUrl']}"
#                         item['product_id'] = product['canonicalUrl'].split("?")[0].split("/")[-1].strip()
#                         item['product_mrp'] = mrp
#                         item['brand'] = brand
#                         scraped_data.append(item)
#                     except Exception as e:
#                         pass
#         except:
#             pass
#     return scraped_data
#
#
# def main(record):
#     keyword = record['keyword']
#     sku = keyword.replace(" ", "+")
#     page_no = 1
#     while True:
#         print(f"sending request [] on page: ", page_no)
#         json_data = fetch_response(page_no=page_no, sku=sku, keyword=keyword, brand="")
#         if not json_data:
#             break
#         items = extract_data(json_data, page_no=page_no, brand="")
#         if not items:
#             break
#         save_data_db(items)
#         page_no+=1
#         # break
#
# if __name__ == "__main__":
#     main({'keyword':"Soda"})