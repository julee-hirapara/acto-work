# import os
# import db_config_1 as db
#
#
# # =========================
# # GET DB DATA
# # =========================
# def fetch_db_records():
#     conn = db.get_db_connection(db.db_name)
#     cursor = conn.cursor()
#
#     query = f"""
#         SELECT hash_id, size
#         FROM {db.data_table}
#         WHERE hash_id IS NOT NULL
#     """
#
#     cursor.execute(query)
#     data = cursor.fetchall()
#
#     cursor.close()
#     conn.close()
#
#     return data
#
#
# # =========================
# # CHECK FILE EXISTS
# # =========================
# def file_exists(folder_path, hash_id):
#     file_path = os.path.join(folder_path, f"{hash_id}_size_chart.json")
#     return os.path.exists(file_path)
#
#
# # =========================
# # MAIN LOGIC
# # =========================
# def find_missing_sizecharts(folder_path):
#     db_data = fetch_db_records()
#
#     missing_set = set()   # ✅ prevents duplicates
#
#     for row in db_data:
#
#         hash_id = row.get("hash_id")
#         size = row.get("size")
#
#         if not hash_id:
#             continue
#
#         # skip ONE SIZE
#         if size and size.strip().upper() == "ONE SIZE":
#             continue
#
#         # file missing condition
#         if not file_exists(folder_path, hash_id):
#             missing_set.add(hash_id)   # ✅ only store hash_id
#
#     return list(missing_set)
#
#
# # =========================
# # RUN
# # =========================
# if __name__ == "__main__":
#
#     folder_path = db.SIZE_PAGESAVE
#
#     result = find_missing_sizecharts(folder_path)
#
#     print("\n==================== MISSING ====================")
#     print(f"Total Missing: {len(result)}\n")
#
#     for hash_id in result:
#         print(hash_id)


import requests

cookies = {
    'SSLB': '1',
    'urbn_geo_region': 'AS-SG',
    'urbn_data_center_id': 'US-NV',
    'urbn_tracer': 'VDWGNAAA7P',
    'utag_main_v_id': '***HIDDEN***',
    '_fbp': 'fb.1.1781606125671.828508829702287667.Bg',
    '_scid': '8frCjSq8zQC7vrRDgbShsemPjgO4npijTKy-Tg',
    'BVBRANDID': '1bb6d5d5-23c2-422b-bda8-9e2146523a73',
    '_tt_enable_cookie': '1',
    '_ttp': '01KV8004XB5PHEB222WP5N2FJ6_.tt.1',
    '_lc2_fpi': '18c6eee2a756--01kv8004yaj6z6hen9ztvk5m5n',
    '__attentive_id': '***HIDDEN***',
    '_attn_': '***HIDDEN***',
    '__attentive_cco': '1781606126832',
    '_svsid': '***HIDDEN***',
    '__adroll_fpc': '***HIDDEN***',
    '_pin_unauth': 'dWlkPVpXWmlZVFl6T1RBdFlUZzJOQzAwWmpNMkxUbGhNalF0WWpJeFlqZzVNR1ExWVdVMA',
    '_ga': 'GA1.1.695608221.1781606128',
    'OptanonAlertBoxClosed': '2026-06-16T10:35:28.347Z',
    '__obref': '2a0b9efd-6b58-439d-ba69-9e494726ca83',
    'mt.v': '2.2053451854.1785917026737',
    'styliticsWidgetSession': '4a9a333f-d690-4d17-a994-4241390b1a4e',
    '_ce.s': '***HIDDEN***',
    '_dyid_server': '6480680127563940034',
    '_dyid': '6480680127563940034',
    'rbuid': 'rbos-497f8f09-964c-4025-a9f8-54d3e376dadd',
    'smartDash': 'bab10c25-d949-4b6f-9b7b-47677f3a295f',
    '_li_dcdm_c': '.urbanoutfitters.com',
    '_lc2_fpi_js': '18c6eee2a756--01kv8004yaj6z6hen9ztvk5m5n',
    '_sctr': '1%7C1791484200000',
    '_clck': '1cbbq6o%5E2%5Ega8%5E1%5E2353',
    'monetate_social_proof': '',
    'ss-enable-401-reauth-modal': '1',
    'ss-enable-multi-label-returns': 'true',
    'SSID': '***HIDDEN***',
    'SSSC': '***HIDDEN***',
    'SSRT': '***HIDDEN***',
    'urbn_auth_payload': '***HIDDEN***',
    'urbn_is_active_dy_session': 'true',
    '_dyjsession': 'y7fiw36dn1ql5krq7p7oaafwyt4bmaro',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Mon+Oct+12+2026+10%3A13%3A45+GMT%2B0530+(India+Standard+Time)&version=202606.1.0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&consentId=2b255836-e584-40b8-8fb9-75692ba80197&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0002%3A1%2CC0001%3A1%2CC0003%3A1%2CC0004%3A1&iType=1&geolocation=GB%3BENG&AwaitingReconsent=false&isDntEnabled=0&prevHadToken=0',
    'datadome': '***HIDDEN***',
    'utag_main__sn': '44',
    'utag_main_ses_id': '1791780227947%3Bexp-session',
    'utag_main__pn': '1%3Bexp-session',
    '_dy_soct': '1791780228!!',
    'utag_main_isLoggedIn': 'false%3Bexp-session',
    'utag_main_tag_session_256': '1%3Bexp-session',
    'utag_main_dc_visit': '44',
    'utag_main_dc_event': '1%3Bexp-session',
    'utag_main__se': '2%3Bexp-session',
    'utag_main__ss': '0%3Bexp-session',
    'utag_main__st': '1791782028504%3Bexp-session',
    'utag_main_dc_region': 'us-east-1%3Bexp-session',
    '_ga_BBMWPLK0E5': 'GS2.1.s1791780222$o26$g1$t1791780230$j52$l0$h0',
    'mp_urbn_urbanoutfitters_na_mixpanel': '%7B%22distinct_id%22%3A%20%2219ed000128082e-0c6414a4bff057-26061151-e1000-19ed0001281133d%22%2C%22bc_persist_updated%22%3A%201781606126210%7D',
    '_uetsid': '***HIDDEN***',
    '_uetvid': '***HIDDEN***',
    '__attentive_session_id': '***HIDDEN***',
    '_gcl_au': '1.1.898374089.1791551837.163911079.1791780232.1791780231.933950495.1791780232.1791780231',
    '_rdt_uuid': '1781606126415.a814df14-d6ac-4e1e-9ed6-83344dc1159c',
    '__attentive_pv': '1',
    '__attentive_ss_referrer': 'ORGANIC',
    '_scid_r': 'CPrCjSq8zQC7vrRDgbShsemPjgO4npijTKy-vg',
    '__attentive_dv': '1',
    '_clsk': '7elhe%5E1791780232877%5E3%5E0%5Ee.clarity.ms%2Fcollect',
    'utag_main_ttd_uuid': '0ab22fe8-bfa7-41f7-8b97-8d607fadc075%3Bexp-session',
    'utag_main_cms_256': '1%3Bexp-session',
    'ttcsid': '1791780217015::Ztk0U00bIRstUUr2l2gV.36.1791780235010.0::1.4073.14053::17971.1.1188.254::2077.22.0',
    'ttcsid_CC2K5NJC77U26CFATFP0': '1791780231067::gbtddezMO9Ml05Ka5f1W.44.1791780235010.0',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'Bearer ***HIDDEN***',
    'content-type': 'application/json',
    'origin': 'https://www.urbanoutfitters.com',
    'priority': 'u=1, i',
    'referer': 'https://www.urbanoutfitters.com/',
    'sec-ch-ua': '"Chromium";v="154", "Google Chrome";v="154", "Not A(Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36',
    'x-datadome-clientid': 'Ys9mfW_fL829Hgz9Z1rsq1V0XaPGdeuVX61DmogCbEqIBuVQnjVxbMw133Mfx2tcLcMtqPwbS3CnqcUkmUKnq5smsz9Co3qmpckSbMP7bV9ALa1JmldH9rL939hGj7AU',
    'x-urbn-channel': 'web',
    'x-urbn-country': 'US',
    'x-urbn-currency': 'USD',
    'x-urbn-experience': 'ss',
    'x-urbn-geo-region': 'AS-SG',
    'x-urbn-language': 'en-US',
    'x-urbn-primary-data-center-id': 'US-NV',
    'x-urbn-site-id': 'uo-us',
    # 'cookie': '***HIDDEN***',
}

json_data = {
    'pageSize': 10000,
    'skip': 0,
    'projectionSlug': 'categorytiles',
    'personalization': '0',
    'customerConsent': 'true',
    'featureProductIds': [],
}

response = requests.post(
    'https://api.urbanoutfitters.com/api/catalog-search-service/v0/uo-us/tiles/womens-clothing',
    cookies=cookies,
    headers=headers,
    json=json_data,
)

print(response)
print(response.json())
# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
#data = '{"pageSize":72,"skip":66,"projectionSlug":"categorytiles","personalization":"0","customerConsent":"true","featureProductIds":[]}'
#response = requests.post(
#    'https://api.urbanoutfitters.com/api/catalog-search-service/v0/uo-us/tiles/womens-clothing',
#    cookies=cookies,
#    headers=headers,
#    data=data,
#)