import requests
import json
import os
import time
import random
import gzip
import logging

import db_config as db
import headers_cookies as hc

from glom import glom


# =========================
# LOGGING SETUP
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)


# =========================
# CONSTANTS
# =========================

WALMART_GRAPHQL_URL = (
    "https://www.walmart.com/orchestra/snb/graphql/Search/"
    "***HIDDEN***/search"
)

WALMART_ZIPCODE_API = "https://www.walmart.com/store/electrode/api/switchUserStore"

MAX_RETRIES    = 3
RETRY_DELAY    = 5        # seconds between retries
MIN_SLEEP      = 2.0      # minimum delay between pages
MAX_SLEEP      = 6.0      # maximum delay between pages
PRODUCTS_LIMIT = 40       # items per page (Walmart max)


# =========================
# SAVE DATA TO DATABASE
# =========================

def save_data_db(items):
    """
    Insert extracted product records into the database.
    Follows the exact dynamic-column insert style from the existing script.
    Skips rows that fail and continues processing.
    """

    try:

        con = db.get_db_connection(db.db_name)
        cur = con.cursor()

        for item in items:

            # -------------------------
            # Replace empty/None values
            # -------------------------

            for k, v in item.items():
                if v is None or v == "":
                    item[k] = "N/A"

            cols   = ", ".join(item.keys()).strip(", ")
            values = tuple(item.values())

            try:

                insert_query = f"""
                INSERT IGNORE INTO walmart_products ({cols})
                VALUES {values}
                """

                cur.execute(insert_query)
                con.commit()

                log.info(f"Inserted -> {item.get('product_url', 'N/A')}")

            except Exception as insert_err:
                log.error(f"DB Insert Error: {insert_err}")

    except Exception as conn_err:
        log.error(f"DB Connection Error: {conn_err}")

    finally:
        try:
            cur.close()
            con.close()
        except Exception:
            pass


# =========================
# SET LOCATION / ZIPCODE
# =========================

def set_location(session, zipcode):
    """
    Set the delivery location on Walmart by hitting their store-switch API.
    This updates the session cookies so all subsequent requests return
    location-aware product data (pricing, availability, delivery estimates).

    Walmart uses the zip-code to resolve the nearest fulfillment store.
    The location is persisted server-side in the session cookie.

    Args:
        session  : requests.Session object (carries cookies across calls)
        zipcode  : string, e.g. "10001"

    Returns:
        True if location was set successfully, False otherwise.
    """

    log.info(f"Setting delivery location to zipcode: {zipcode}")

    # -------------------------
    # Build the location payload
    # Walmart expects a JSON body with the zip code
    # -------------------------

    location_payload = {
        "postalCode": str(zipcode),
        "storeId":    None,
        "isZipOnly":  True,
    }

    # -------------------------
    # Headers for the location API call
    # Must include content-type and origin to pass CORS check
    # -------------------------

    location_headers = {
        "accept":           "application/json",
        "accept-language":  "en-US,en;q=0.9",
        "content-type":     "application/json",
        "origin":           "https://www.walmart.com",
        "referer":          "https://www.walmart.com/",
        "user-agent":       hc.headers_pl.get("user-agent", "Mozilla/5.0"),
    }

    try:

        response = session.post(
            WALMART_ZIPCODE_API,
            json=location_payload,
            headers=location_headers,
            timeout=30,
        )

        log.info(f"Location API Status: {response.status_code}")

        if response.status_code == 200:
            log.info(f"Location set successfully -> zipcode: {zipcode}")
            return True

        else:
            log.warning(
                f"Location API returned non-200: {response.status_code} | "
                f"Body: {response.text[:300]}"
            )
            return False

    except Exception as e:
        log.error(f"Location Set Error: {e}")
        return False


# =========================
# BUILD PAYLOAD
# =========================

def build_payload(keyword, page_no, limit=40, brand="", category_id="", zipcode=""):
    """
    Build the Walmart GraphQL search payload as a clean Python dict.
    This avoids hardcoded JSON strings and supports dynamic page numbers.

    IMPORTANT NOTES:
    - fitmentSearchParams and searchParams must mirror the root payload
      with their own nested fitmentSearchParams/searchParams as empty dicts.
      This is what Walmart's API expects for pagination > page 1.
    - affinityOverride must be consistent across root and nested params.
    - page number must be synced across ALL three levels (root, fitment, search).
    - wm_page_url in headers must also reflect the correct page number.

    Args:
        keyword     : search keyword string
        page_no     : current page number (1-indexed)
        limit       : number of products per page (max 40)
        brand       : optional brand filter string
        category_id : optional Walmart category ID string
        zipcode     : delivery zipcode (informational, location set via session)

    Returns:
        dict payload ready for json.dumps()
    """

    # -------------------------
    # Build the facet string if brand is provided
    # Walmart uses facet=brand%3ABrandName format in URL
    # -------------------------

    facet_str = ""
    if brand:
        facet_str = f"brand:{brand}"

    # -------------------------
    # Core payload fields
    # These are shared across root, fitmentSearchParams, and searchParams
    # -------------------------

    core_fields = {
        "id":               "",
        "affinityOverride": "store_led",
        "dealsId":          "",
        "query":            keyword,
        "nudgeContext":     "",
        "page":             page_no,
        "prg":              "desktop",
        "catId":            category_id if category_id else "",
        "facet":            facet_str,
        "sort":             "best_match",
        "rawFacet":         "",
        "seoPath":          "",
        "ps":               limit,
        "limit":            limit,
        "ptss":             "",
        "trsp":             "",
        "beShelfId":        "",
        "recall_set":       "",
        "module_search":    "",
        "min_price":        "",
        "max_price":        "",
        "storeSlotBooked":  "",
    }

    # -------------------------
    # Nested additionalQueryParams block
    # Same across all three payload levels
    # -------------------------

    additional_query_params = {
        "hidden_facet":            None,
        "translation":             None,
        "isMoreOptionsTileEnabled": True,
        "isGenAiEnabled":          True,
        "rootDimension":           "",
        "altQuery":                "",
        "selectedFilter":          "",
        "neuralSearchSeeAll":      False,
        "isModuleArrayReq":        False,
        "isLMPBrowsePage":         False,
    }

    # -------------------------
    # searchArgs block
    # Same across all three payload levels
    # -------------------------

    search_args = {
        "query":  keyword,
        "cat_id": category_id if category_id else "",
        "prg":    "desktop",
        "facet":  facet_str,
    }

    # -------------------------
    # fitmentFieldParams block
    # Controls fitment/vehicle-related search features
    # -------------------------

    fitment_field_params = {
        "powerSportEnabled":          True,
        "dynamicFitmentEnabled":      True,
        "extendedAttributesEnabled":  True,
        "extendedAttributesV2Enabled": False,
        "fuelTypeEnabled":            True,
    }

    # -------------------------
    # Feature flag fields
    # Shared across all three payload levels
    # -------------------------

    feature_flags = {
        "ffAwareSearchOptOut":                    False,
        "enableDesktopHighlights":                False,
        "enableVolumePricing":                    False,
        "enableCopyBlock":                        True,
        "enableVariantCount":                     False,
        "enableSlaBadgeV2":                       True,
        "enableUnifiedProductFragment":           False,
        "enableESSCarousel":                      False,
        "enableFashionTopNav":                    False,
        "enableUnifiedSchema":                    True,
        "postProcessingVersion":                  2,
        "version":                                "v2",
        "enableRelatedSearches":                  True,
        "enablePortableFacets":                   True,
        "enableFacetCount":                       True,
        "fetchMarquee":                           True,
        "fetchSkyline":                           True,
        "fetchGallery":                           False,
        "fetchSbaTop":                            True,
        "fetchDataV1":                            True,
        "fetchDataV2":                            False,
        "fungibilityEnabled":                     False,
        "enableAdsPromoData":                     False,
        "fetchDac":                               True,
        "tenant":                                 "WM_GLASS",
        "enableMultiSave":                        False,
        "enableInStoreShelfMessage":              False,
        "enableSellerType":                       False,
        "enableItemRank":                         False,
        "enableOptimisticWeightUpdate":           False,
        "enableAdditionalSearchDepartmentAnalytics": True,
        "enableFulfillmentTagsEnhacements":       False,
        "enableRxDrugScheduleModal":              False,
        "enablePromoData":                        True,
        "enableSignInToSeePrice":                 False,
        "enablePromotionMessages":                False,
        "enableDebugAnalyticsTags":               False,
        "enableItemLimits":                       False,
        "enableCanAddToList":                     False,
        "enableIsFreeWarranty":                   False,
        "enableShopSimilarBottomSheet":           False,
        "adsParams": {
            "fungibilityEnabled": False,
        },
        "pageType": "SearchPage",
    }

    # -------------------------
    # Build nested fitmentSearchParams
    # This is a mirror of root payload MINUS its own nested params
    # Walmart requires cat_id and _be_shelf_id in these nested blocks
    # -------------------------

    fitment_search_params = {
        **core_fields,
        "additionalQueryParams": additional_query_params,
        "searchArgs":            search_args,
        "fitmentFieldParams":    fitment_field_params,
        **feature_flags,
        "cat_id":       category_id if category_id else "",
        "_be_shelf_id": "",
    }

    # -------------------------
    # Build nested searchParams
    # Also mirrors root payload with cat_id and _be_shelf_id appended
    # -------------------------

    search_params = {
        **core_fields,
        "additionalQueryParams": additional_query_params,
        "searchArgs":            search_args,
        "fitmentFieldParams":    fitment_field_params,
        **feature_flags,
        "cat_id":       category_id if category_id else "",
        "_be_shelf_id": "",
    }

    # -------------------------
    # Assemble root payload
    # Root payload references fitmentSearchParams and searchParams
    # that we built above — this is the CORRECT structure Walmart expects
    # -------------------------

    payload = {
        **core_fields,
        "additionalQueryParams":  additional_query_params,
        "searchArgs":             search_args,
        "fitmentFieldParams":     fitment_field_params,
        "fitmentSearchParams":    fitment_search_params,
        "searchParams":           search_params,
        **feature_flags,
    }

    return payload


# =========================
# SAVE PAGE TO CACHE
# =========================

def save_page_cache(file_name, response_text):
    """
    Save raw response text to gzip cache file.
    Avoids redundant HTTP requests on re-runs.

    Args:
        file_name     : full path including .json.gz extension
        response_text : raw response string from requests
    """

    try:
        with gzip.open(file_name, "wt", encoding="utf-8") as f:
            f.write(response_text)
        log.info(f"Cached -> {file_name}")

    except Exception as e:
        log.error(f"Cache Save Error: {e}")


# =========================
# LOAD PAGE FROM CACHE
# =========================

def load_page_cache(file_name):
    """
    Load and decompress a gzip-cached JSON page.

    Args:
        file_name : full path to .json.gz file

    Returns:
        Parsed JSON dict, or None on failure
    """

    try:
        with gzip.open(file_name, "rt", encoding="utf-8") as f:
            content = f.read()
        return json.loads(content)

    except Exception as e:
        log.error(f"Cache Load Error: {e}")
        return None


# =========================
# BUILD REQUEST HEADERS
# =========================

def build_request_headers(keyword, page_no, brand, category_id):
    """
    Build the per-request headers.
    wm_page_url MUST match the actual search URL including page number.
    This is one of the key reasons page > 1 fails — if wm_page_url stays
    at page 1, Walmart's backend may return stale/incorrect data.

    Args:
        keyword     : search keyword
        page_no     : current page number
        brand       : brand filter string
        category_id : category ID string

    Returns:
        dict of headers for this request
    """

    # -------------------------
    # Copy base headers from hc module
    # Do NOT mutate the original — always copy first
    # -------------------------

    h = hc.headers_pl.copy()

    # -------------------------
    # Build the search URL that matches this specific page
    # This is used as wm_page_url so Walmart knows which page we're on
    # -------------------------

    sku = keyword.replace(" ", "+")

    if brand and category_id:
        page_url = (
            f"https://www.walmart.com/search?q={sku}"
            f"&facet=brand%3A{brand}%7C%7Ccategory%3A{category_id}"
            f"&page={page_no}"
        )

    elif brand:
        page_url = (
            f"https://www.walmart.com/search?q={sku}"
            f"&facet=brand%3A{brand}"
            f"&page={page_no}"
        )

    elif category_id:
        page_url = (
            f"https://www.walmart.com/search?q={sku}"
            f"&catId={category_id}"
            f"&page={page_no}"
        )

    else:
        page_url = (
            f"https://www.walmart.com/search?q={sku}"
            f"&page={page_no}"
        )

    # -------------------------
    # Set wm_page_url — this is CRITICAL for pagination
    # Walmart uses this header to validate request context
    # Mismatching this with the payload page causes empty results on page > 1
    # -------------------------

    h["wm_page_url"] = page_url

    return h


# =========================
# FETCH RESPONSE
# =========================

def fetch_response(session, page_no, keyword, brand, category_id, zipcode, cache_dir):
    """
    Fetch the Walmart search GraphQL API response for a given page.
    Supports:
        - Disk-based gzip cache (skip request if already fetched)
        - Retry logic with exponential backoff
        - Dynamic headers with correct wm_page_url per page
        - Dynamic payload via build_payload()

    Args:
        session     : requests.Session (carries location cookies)
        page_no     : current page number
        keyword     : search keyword string
        brand       : brand filter (empty string = no filter)
        category_id : Walmart category ID (empty string = no filter)
        zipcode     : delivery zip (informational for cache filename)
        cache_dir   : directory path for gzip cache files

    Returns:
        Parsed JSON dict, or None on failure
    """

    # -------------------------
    # Build cache file name
    # Include zipcode so cached data is location-specific
    # -------------------------

    safe_keyword = keyword.replace(" ", "_")
    safe_brand   = brand.replace(" ", "_") if brand else "no_brand"

    file_name = os.path.join(
        cache_dir,
        f"{safe_keyword}_{safe_brand}_{zipcode}_{page_no}.json.gz"
    )

    # -------------------------
    # CACHE: Return cached response if it exists
    # -------------------------

    if os.path.exists(file_name):
        log.info(f"Loaded from cache -> Page {page_no}")
        return load_page_cache(file_name)

    # -------------------------
    # Build request headers with correct wm_page_url for this page
    # -------------------------

    headers = build_request_headers(
        keyword=keyword,
        page_no=page_no,
        brand=brand,
        category_id=category_id,
    )

    # -------------------------
    # Build the payload for this page
    # Payload is a clean Python dict — no hardcoded JSON strings
    # -------------------------

    payload = build_payload(
        keyword=keyword,
        page_no=page_no,
        limit=PRODUCTS_LIMIT,
        brand=brand,
        category_id=category_id,
        zipcode=zipcode,
    )

    # -------------------------
    # Serialize payload to JSON string for the 'variables' query param
    # Use compact separators to match what the browser sends
    # -------------------------

    params = {
        "variables": json.dumps(payload, separators=(",", ":"))
    }

    # -------------------------
    # RETRY LOOP
    # Attempt up to MAX_RETRIES times before giving up on this page
    # -------------------------

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            log.info(
                f"Request -> Page {page_no} | Keyword: '{keyword}' | "
                f"Brand: '{brand}' | ZIP: {zipcode} | Attempt: {attempt}/{MAX_RETRIES}"
            )

            response = session.get(
                WALMART_GRAPHQL_URL,
                params=params,
                headers=headers,
                timeout=60,
            )

            log.info(f"Status: {response.status_code} | Page: {page_no}")

            # -------------------------
            # SUCCESS: Parse and cache the response
            # -------------------------

            if response.status_code == 200:

                try:
                    json_data = response.json()
                except json.JSONDecodeError as json_err:
                    log.error(f"JSON Parse Error on Page {page_no}: {json_err}")
                    log.error(f"Raw Response (500 chars): {response.text[:500]}")
                    return None

                # Save to cache so future runs skip this request
                save_page_cache(
                    file_name=file_name,
                    response_text=response.text
                )

                return json_data

            # -------------------------
            # RATE LIMITED / BLOCKED: Log and retry
            # -------------------------

            elif response.status_code in (429, 503, 403):

                log.warning(
                    f"Rate limited or blocked on Page {page_no}: "
                    f"{response.status_code} | Retrying in {RETRY_DELAY * attempt}s"
                )

                time.sleep(RETRY_DELAY * attempt)

            # -------------------------
            # OTHER FAILURE: Log and retry
            # -------------------------

            else:

                log.error(
                    f"Failed Page {page_no}: HTTP {response.status_code} | "
                    f"Body (500 chars): {response.text[:500]}"
                )

                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)

        except requests.exceptions.Timeout:
            log.error(f"Timeout on Page {page_no} | Attempt {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        except requests.exceptions.ConnectionError as conn_err:
            log.error(f"Connection Error on Page {page_no}: {conn_err} | Attempt {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

        except Exception as e:
            log.error(f"Unexpected Request Error on Page {page_no}: {e} | Attempt {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    log.error(f"All {MAX_RETRIES} attempts failed for Page {page_no}. Skipping.")
    return None


# =========================
# EXTRACT DATA
# =========================

def extract_data(json_data, page_no, brand, keyword, zipcode):
    """
    Extract product data from Walmart GraphQL search response.

    Handles:
        - Skipping non-product cards (ads, banners, etc.)
        - Safe glom-based field extraction with defaults
        - Image URL cleanup (strips query params)
        - Price discount calculation
        - Product URL construction from canonicalUrl

    Args:
        json_data : parsed JSON dict from Walmart API
        page_no   : current page number
        brand     : brand filter string (stored in extracted item)
        keyword   : search keyword (stored in extracted item)
        zipcode   : delivery zipcode (stored in extracted item)

    Returns:
        List of product dicts ready for DB insert
    """

    scraped_data = []

    if not json_data:
        log.warning("extract_data received empty json_data")
        return scraped_data

    # -------------------------
    # Navigate to itemStacks
    # This is the top-level container for search result groups
    # -------------------------

    try:

        item_stacks = glom(
            json_data,
            "data.search.searchResult.itemStacks",
            default=[]
        )

    except Exception as e:
        log.error(f"Error navigating to itemStacks: {e}")
        return scraped_data

    if not item_stacks:
        log.warning("itemStacks is empty — likely end of pagination or blocked response")
        return scraped_data

    # -------------------------
    # Iterate each item stack (Walmart groups results into stacks)
    # -------------------------

    for stack in item_stacks:

        stack_title = stack.get("title", "unknown")
        items_v2    = stack.get("itemsV2", [])

        log.info(f"Processing stack: '{stack_title}' | Items: {len(items_v2)}")

        for product in items_v2:

            # -------------------------
            # Skip non-Product cards
            # Walmart includes ad slots, banners, etc. in itemsV2
            # These have __typename like "AdModule", "Banner", etc.
            # -------------------------

            type_name = product.get("__typename", "")

            if "Product" not in type_name:
                log.debug(f"Skipping non-product card: __typename={type_name}")
                continue

            try:

                item = {}

                # -------------------------
                # PRICE: Current selling price
                # -------------------------

                price = glom(
                    product,
                    "priceInfo.currentPrice.price",
                    default=None
                )

                # -------------------------
                # MRP: Original / list price (before discount)
                # Fall back to current price if no list price available
                # -------------------------

                mrp = glom(
                    product,
                    "priceInfo.listPrice.price",
                    default=None
                )

                if mrp is None:
                    mrp = price

                # -------------------------
                # DISCOUNT: Calculate price difference if both values are numeric
                # -------------------------

                price_discount = "N/A"

                if isinstance(price, (int, float)) and isinstance(mrp, (int, float)):
                    if mrp > price:
                        price_discount = round(mrp - price, 2)

                # -------------------------
                # PRICE PER UNIT: e.g. "$0.08/fl oz"
                # -------------------------

                price_per_unit = glom(
                    product,
                    "priceInfo.unitPrice.priceString",
                    default="N/A"
                )

                # -------------------------
                # IMAGE URL: Clean thumbnail URL
                # Walmart often appends query params — strip them for clean URL
                # -------------------------

                image_url = glom(
                    product,
                    "imageInfo.thumbnailUrl",
                    default="N/A"
                )

                if image_url and "jpeg?" in image_url:
                    image_url = image_url.split("jpeg?")[0] + "jpeg"

                # -------------------------
                # PRODUCT URL + PRODUCT ID
                # canonicalUrl is a relative path: /ip/Product-Name/12345678
                # Product ID is the numeric segment at the end of the path
                # -------------------------

                canonical_url = product.get("canonicalUrl", "")

                if canonical_url:
                    product_url = f"https://www.walmart.com{canonical_url}"

                    # Extract product ID from URL path
                    # e.g. /ip/Coca-Cola-12-Pack/123456789?some=param -> 123456789
                    product_id = (
                        canonical_url
                        .split("?")[0]
                        .split("/")[-1]
                        .strip()
                    )

                else:
                    product_url = "N/A"
                    product_id  = "N/A"

                # -------------------------
                # SPONSORED STATUS
                # Walmart marks sponsored products via sponsoredProduct field
                # -------------------------

                is_sponsored = "Yes" if product.get("sponsoredProduct") else "No"

                # -------------------------
                # RATINGS + REVIEWS
                # -------------------------

                avg_rating  = product.get("averageRating",   "N/A")
                num_reviews = product.get("numberOfReviews", "N/A")

                # -------------------------
                # SELLER / FULFILLMENT INFO
                # -------------------------

                seller_name = glom(
                    product,
                    "sellerInfo.sellerDisplayName",
                    default="N/A"
                )

                fulfillment_type = glom(
                    product,
                    "fulfillmentBadge",
                    default="N/A"
                )

                # -------------------------
                # AVAILABILITY
                # -------------------------

                availability = glom(
                    product,
                    "availabilityStatusDisplayValue",
                    default="N/A"
                )

                # -------------------------
                # ASSEMBLE ITEM DICT
                # Column order must match the database schema
                # -------------------------

                item["product_id"]       = product_id
                item["product_name"]     = product.get("name", "N/A") or "N/A"
                item["product_url"]      = product_url
                item["main_image"]       = image_url
                item["product_price"]    = price    if price    is not None else "N/A"
                item["product_mrp"]      = mrp      if mrp      is not None else "N/A"
                item["price_discount"]   = price_discount
                item["price_per_unit"]   = price_per_unit
                item["avg_rating"]       = avg_rating
                item["num_review"]       = num_reviews
                item["sponsored"]        = is_sponsored
                item["seller_name"]      = seller_name
                item["fulfillment_type"] = fulfillment_type
                item["availability"]     = availability
                item["brand"]            = brand if brand else "N/A"
                item["keyword"]          = keyword
                item["zipcode"]          = zipcode
                item["page_num"]         = page_no

                scraped_data.append(item)

            except Exception as product_err:
                log.error(f"Product Parse Error: {product_err}")
                continue

    log.info(f"Extracted {len(scraped_data)} products from Page {page_no}")

    return scraped_data


# =========================
# DEDUPLICATE PRODUCTS
# =========================

def deduplicate(items, seen_ids):
    """
    Filter out products already seen in previous pages.
    Modifies seen_ids in-place to track across pagination.

    Args:
        items    : list of product dicts from extract_data()
        seen_ids : set of product_id strings already processed

    Returns:
        List of unique product dicts not previously seen
    """

    unique_items = []

    for item in items:
        pid = item.get("product_id", "N/A")

        if pid == "N/A" or pid not in seen_ids:
            seen_ids.add(pid)
            unique_items.append(item)

        else:
            log.debug(f"Duplicate skipped -> product_id: {pid}")

    return unique_items


# =========================
# GET TOTAL PRODUCTS COUNT
# =========================

def get_total_products(json_data):
    """
    Try to read the total product count from the API response.
    Walmart sometimes returns this in the response metadata.
    Used to calculate expected number of pages.

    Args:
        json_data : parsed JSON dict from Walmart API

    Returns:
        int total products count, or None if not available
    """

    try:

        total = glom(
            json_data,
            "data.search.searchResult.count",
            default=None
        )

        if total is not None:
            log.info(f"Total products reported by API: {total}")

        return total

    except Exception:
        return None


# =========================
# CREATE SESSION WITH LOCATION
# =========================

def create_session(zipcode):
    """
    Create a requests.Session object and configure it with:
        - Base cookies from hc module
        - Location set via Walmart's zip-code API

    Using a Session ensures location cookies are sent on every subsequent request.

    Args:
        zipcode : delivery zip code string

    Returns:
        Configured requests.Session object
    """

    session = requests.Session()

    # -------------------------
    # Load base cookies from hc module into the session
    # These are the browser cookies needed for authentication/session
    # -------------------------

    for cookie_name, cookie_value in hc.cookies_pl.items():
        session.cookies.set(cookie_name, cookie_value)

    # -------------------------
    # Set the delivery location via Walmart API
    # This updates session cookies to reflect the chosen zipcode
    # -------------------------

    if zipcode:
        location_set = set_location(session, zipcode)

        if not location_set:
            log.warning(
                f"Could not set location to zipcode {zipcode}. "
                f"Results may not be location-specific."
            )

    return session


# =========================
# MAIN SCRAPER LOOP
# =========================

def main(record):
    """
    Main entry point for the Walmart PL scraper.
    Orchestrates:
        - Session creation with location setup
        - Full pagination loop (page 1 through last page)
        - Extraction, deduplication, and DB insert per page
        - Safe exit conditions

    Args:
        record : dict with keys:
            - keyword     : search term (required)
            - zipcode     : delivery zip code (required for location-based results)
            - brand       : brand filter string (optional, default "")
            - category_id : Walmart category ID (optional, default "")
    """

    # -------------------------
    # Parse input record
    # -------------------------

    keyword     = record.get("keyword",     "")
    zipcode     = record.get("zipcode",     "")
    brand       = record.get("brand",       "")
    category_id = record.get("category_id", "")

    if not keyword:
        log.error("No keyword provided. Exiting.")
        return

    log.info("=" * 60)
    log.info(f"STARTING SCRAPER")
    log.info(f"Keyword     : {keyword}")
    log.info(f"Zipcode     : {zipcode}")
    log.info(f"Brand       : {brand}")
    log.info(f"Category ID : {category_id}")
    log.info("=" * 60)

    # -------------------------
    # Setup cache directory
    # Separate folder per scraper type (PL = product listing)
    # -------------------------

    cache_dir = os.path.join(db.page_save_path, "PL")
    os.makedirs(cache_dir, exist_ok=True)

    # -------------------------
    # Create session with location cookies set
    # -------------------------

    session = create_session(zipcode)

    # -------------------------
    # Tracking variables
    # -------------------------

    page_no        = 1
    total_products = 0
    seen_ids       = set()      # For deduplication across pages
    total_reported = None       # Total products count from API (if available)

    # -------------------------
    # PAGINATION LOOP
    # Continue until:
    #   (a) No JSON response returned
    #   (b) No products extracted from page
    #   (c) Total pages exhausted (if total_reported is available)
    # -------------------------

    while True:

        log.info("")
        log.info("=" * 60)
        log.info(f"Fetching Page -> {page_no}")
        log.info("=" * 60)

        # -------------------------
        # FETCH: Get API response for this page
        # -------------------------

        json_data = fetch_response(
            session=session,
            page_no=page_no,
            keyword=keyword,
            brand=brand,
            category_id=category_id,
            zipcode=zipcode,
            cache_dir=cache_dir,
        )

        if not json_data:
            log.warning(f"No JSON response on Page {page_no}. Stopping pagination.")
            break

        # -------------------------
        # Get total product count from API response on first page
        # This helps us know when to stop
        # -------------------------

        if page_no == 1:
            total_reported = get_total_products(json_data)

            if total_reported is not None:
                import math
                max_pages = math.ceil(total_reported / PRODUCTS_LIMIT)
                log.info(f"Expected max pages: {max_pages} (based on {total_reported} total products)")

        # -------------------------
        # EXTRACT: Parse products from API response
        # -------------------------

        items = extract_data(
            json_data=json_data,
            page_no=page_no,
            brand=brand,
            keyword=keyword,
            zipcode=zipcode,
        )

        if not items:
            log.info(f"No products found on Page {page_no}. End of pagination.")
            break

        # -------------------------
        # DEDUPLICATE: Remove products already seen on previous pages
        # -------------------------

        unique_items = deduplicate(items, seen_ids)

        log.info(
            f"Page {page_no}: {len(items)} extracted | "
            f"{len(unique_items)} unique | "
            f"{len(items) - len(unique_items)} duplicates skipped"
        )

        if not unique_items:
            log.info(f"All products on Page {page_no} were duplicates. Stopping.")
            break

        # -------------------------
        # SAVE: Insert unique products into DB
        # -------------------------

        save_data_db(unique_items)

        total_products += len(unique_items)

        log.info(f"Running total: {total_products} products saved")

        # -------------------------
        # CHECK: Stop if we've hit the reported total
        # -------------------------

        if total_reported is not None and total_products >= total_reported:
            log.info(
                f"Reached reported total of {total_reported} products. "
                f"Stopping pagination."
            )
            break

        # -------------------------
        # NEXT PAGE: Advance page counter
        # -------------------------

        page_no += 1

        # -------------------------
        # DELAY: Random sleep to avoid rate limiting
        # -------------------------

        sleep_time = random.uniform(MIN_SLEEP, MAX_SLEEP)

        log.info(f"Sleeping {round(sleep_time, 2)} seconds before next page...")

        time.sleep(sleep_time)

    # -------------------------
    # FINAL SUMMARY
    # -------------------------

    log.info("")
    log.info("=" * 60)
    log.info(f"SCRAPING COMPLETE")
    log.info(f"Total Pages Scraped : {page_no}")
    log.info(f"Total Products Saved: {total_products}")
    log.info(f"Keyword             : {keyword}")
    log.info(f"Zipcode             : {zipcode}")
    log.info(f"Brand               : {brand}")
    log.info("=" * 60)


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":

    main({
        "keyword":     "Soda",
        "zipcode":     "12206",     # New York, NY — change as needed
        "brand":       "",          # e.g. "Coca-Cola" or leave empty for all brands
        "category_id": "",          # e.g. "976759" or leave empty for all categories
    })