import pymysql
import requests
import json
import os
import db_config as db
import headers_cookies as hc
from glom import glom


def save_data_db(items):
    try:
        con = db.get_db_connection(db.db_name)
        cur = con.cursor()

        for item in items:
            for k, v in item.items():
                if v in [None, "", [], {}]:
                    item[k] = "N/A"
            cols = ", ".join(item.keys()).strip(', ')
            values = tuple(item.values())
            try:
                insert_active = f"""INSERT IGNORE INTO {db.link_table} ({cols}) VALUES {values}"""
                cur.execute(insert_active)
                con.commit()
                print('inserted', item['product_url'])
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)
    finally:
        cur.close()
        con.close()


def fetch_response(page_no, pl_url, cat_id, category_name):
    file_loc = f"{db.PAGESAVE_PATH}\\CATEGORY\\{category_name}\\"
    os.makedirs(file_loc, exist_ok=True)
    file_name = fr"{file_loc}\\{cat_id}_{page_no}.json.gz"
    if os.path.exists(file_name):
        return json.loads(db.read_page(file_name))
    h = hc.headers_pl.copy()
    # DYNAMIC PAGE URL
    if page_no > 1:
        h['wm_page_url'] = f"{pl_url}?page={page_no}"
    else:
        h['wm_page_url'] = pl_url

    # SAME PAYLOAD STRUCTURE ONLY PAGE CHANGED DYNAMICALLY
    json_data = {
        "id": "",
        "affinityOverride": "default",
        "pap": "{\"polaris\":{\"ms_triggered\":false}}",
        "dealsId": "",
        "query": "",
        "nudgeContext": "",
        "page": page_no,
        "prg": "desktop",
        "catId": str(cat_id),
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
            "cat_id": str(cat_id),
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
            "page": page_no,
            "prg": "desktop",
            "catId": str(cat_id),
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
                "cat_id": str(cat_id),
                "prg": "desktop",
                "facet": ""
            },
            "enableCopyBlock": True,
            "enableVariantCount": False,
            "enableSlaBadgeV2": True,
            "enableUnifiedProductFragment": False,
            "enableESSCarousel": False,
            "cat_id": str(cat_id),
            "_be_shelf_id": ""
        },
        "searchParams": {
            "id": "",
            "affinityOverride": "default",
            "pap": "{\"polaris\":{\"ms_triggered\":false}}",
            "dealsId": "",
            "query": "",
            "nudgeContext": "",
            "page": page_no,
            "prg": "desktop",
            "catId": str(cat_id),
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
                "cat_id": str(cat_id),
                "prg": "desktop",
                "facet": ""
            },
            "enableCopyBlock": True,
            "enableVariantCount": False,
            "enableSlaBadgeV2": True,
            "enableUnifiedProductFragment": False,
            "enableESSCarousel": False,
            "cat_id": str(cat_id),
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
        'variables': json.dumps(json_data),
    }
    response = requests.get(
        'https://www.walmart.com/orchestra/snb/graphql/Browse/64a32778264c32a40ea5a46213a2236c8fe7616017b056af5a43af648260ff7e/browse',
        params=params,
        cookies=hc.cookies_pl,
        headers=h,
    )
    if response.status_code == 200:
        db.save_page(file_name=file_name, response=response.text)
        return response.json()
    else:
        print(f"Failed response form page[{page_no}]:", response.status_code)
        return None


def extract_data(json_data, page_no, pl_url, cat_id, category_name):
    scraped_data = []
    if not json_data:
        return scraped_data
    try:
        item_stacks = glom(
            json_data,
            "data.search.searchResult.itemStacks",
            default=[]
        )
        for products in item_stacks:
            for product in products.get('itemsV2', []):
                if "Product" not in product.get('__typename', ''):
                    continue
                try:
                    item = {}
                    price = glom(product, "priceInfo.currentPrice.price", default="N/A")
                    mrp = glom(product, "priceInfo.listPrice.price", default="N/A")
                    if mrp == "N/A":
                        mrp = price
                    price_discount = "N/A"
                    if isinstance(price, (int, float)) and isinstance(mrp, (int, float)):
                        if mrp > price:
                            price_discount = round(mrp - price, 2)
                    item['main_image'] = glom(
                        product,
                        "imageInfo.thumbnailUrl",
                        default="N/A"
                    )
                    if "jpeg?" in str(item['main_image']):
                        item['main_image'] = (
                                item['main_image'].split("jpeg?")[0] + "jpeg"
                        )
                    item['product_name'] = product.get('name', "N/A")
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
                        "Yes" if product.get("sponsoredProduct") else "No"
                    )
                    item['product_url'] = (
                        f"https://www.walmart.com{product['canonicalUrl']}"
                    )
                    item['product_id'] = (
                        product['canonicalUrl']
                        .split("?")[0]
                        .split("/")[-1]
                        .strip()
                    )
                    item['product_mrp'] = mrp
                    item['category_name'] = category_name
                    item['pl_url'] = pl_url
                    item['cat_id'] = cat_id
                    scraped_data.append(item)
                except Exception as e:
                    print(e)
    except Exception as e:
        print(e)
    return scraped_data


def main():
    conn = db.get_db_connection(db.db_name)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # Fetch pending rows
        query = f"""
            SELECT id, pl_url, category_name
            FROM {db.input_table}
            WHERE status = 'failed'
              AND pl_url IS NOT NULL
              AND pl_url != 'N/A'
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            print("No pending sub category found.")
            return
        for row in rows:
            row_id = row["id"]
            pl_url = row["pl_url"]
            category_name = row["category_name"]
            try:
                # REMOVE ? PARAMETERS IF EXISTS
                cat_id = pl_url.rstrip("/").split("/")[-1].split("?")[0]
                print("=" * 80)
                print(f"Processing ID: {row_id}")
                print(f"URL: {pl_url}")
                print(f"CAT ID: {cat_id}")
                page_no = 1
                success = True
                # while True:
                while page_no <= 27:
                    print(f"Sending request page: {page_no}")
                    json_data = fetch_response(
                        page_no=page_no,
                        pl_url=pl_url,
                        cat_id=cat_id,
                        category_name=category_name
                    )
                    # REQUEST FAILED
                    if not json_data:
                        success = False
                        break
                    items = extract_data(
                        json_data=json_data,
                        page_no=page_no,
                        pl_url=pl_url,
                        cat_id=cat_id,
                        category_name=category_name
                    )
                    # NO MORE PRODUCTS
                    if not items:
                        print("No more products found")
                        break
                    save_data_db(items)
                    print(f"Saved page: {page_no} | items: {len(items)}")
                    page_no += 1
                # =========================
                # UPDATE STATUS
                # =========================
                if success:
                    update_query = f"""
                        UPDATE {db.input_table}
                        SET status = 'completed',
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    cursor.execute(update_query, (row_id,))
                    conn.commit()
                    print(f"ID {row_id} completed")
                else:
                    fail_query = f"""
                        UPDATE {db.input_table}
                        SET status = 'failed',
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    cursor.execute(fail_query, (row_id,))
                    conn.commit()
                    print(f"ID {row_id} failed")
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


if __name__ == "__main__":
    main()