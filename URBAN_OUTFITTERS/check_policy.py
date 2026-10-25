import json

import requests

cookies = {
    'SSLB': '1',
    'urbn_uuid': '2b255836-e584-40b8-8fb9-75692ba80197',
    'urbn_geo_region': 'AS-SG',
    'urbn_data_center_id': 'US-NV',
    'urbn_tracer': 'VDWGNAAA7P',
    'urbn_dy_id': '-6395111219976395031',
    'utag_main_v_id': '***HIDDEN***',
    '_fbp': 'fb.1.1781606125671.828508829702287667.Bg',
    '_scid': '8frCjSq8zQC7vrRDgbShsemPjgO4npijTKy-Tg',
    'BVBRANDID': '1bb6d5d5-23c2-422b-bda8-9e2146523a73',
    'smartDash': '525bc576-3e59-4fe9-8ea9-4357ff396d8c',
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
    'QSI_SI_9AEkoeXmCVAdTMN_intercept': 'true',
    '_dyid_server': '6480680127563940034',
    'urbn_privacy_restriction_region': '%5B%22NJ%22%5D',
    'urbn_channel': 'web',
    'urbn_is_active_dy_session': 'true',
    '_dyid': '6480680127563940034',
    'urbn_currency': 'USD',
    'urbn_language': 'en-US',
    'siteId': 'uo-us',
    'urbn_edgescape_site_id': 'uo-us',
    'urbn_site_id': 'uo-us',
    'rbuid': 'rbos-497f8f09-964c-4025-a9f8-54d3e376dadd',
    '__obref': '2a0b9efd-6b58-439d-ba69-9e494726ca83',
    'bluecoreNV': 'false',
    'cebs': '1',
    '_li_dcdm_c': '.urbanoutfitters.com',
    '_lc2_fpi_js': '18c6eee2a756--01kv8004yaj6z6hen9ztvk5m5n',
    'urbn_page_visits_count': '%7B%22uo-us%22%3A5%7D',
    '_ga_BBMWPLK0E5': 'deleted',
    'ss-enable-multi-label-returns': 'true',
    'ss-enable-401-reauth-modal': '1',
    'SSSC': '***HIDDEN***',
    'urbn_auth_payload': '***HIDDEN***',
    'urbn_country': 'IN',
    'urbn_inventory_pool': 'INTL_DIRECT',
    'SSID': '***HIDDEN***',
    'utag_main__sn': '42',
    'utag_main_ses_id': '1785917025888%3Bexp-session',
    '_dyjsession': 'vy1d4c0h7tjoilm5q71rqv86ekbporf8',
    'utag_main_isLoggedIn': 'false%3Bexp-session',
    'utag_main_tag_session_256': '1%3Bexp-session',
    'utag_main_dc_visit': '42',
    'mt.v': '2.2053451854.1785917026737',
    'styliticsWidgetSession': '4a9a333f-d690-4d17-a994-4241390b1a4e',
    '_rdt_uuid': '1781606126415.a814df14-d6ac-4e1e-9ed6-83344dc1159c',
    '_uetsid': '***HIDDEN***',
    '_uetvid': '***HIDDEN***',
    '_scid_r': '8vrCjSq8zQC7vrRDgbShsemPjgO4npijTKy-uA',
    'bc_invalidateUrlCache_targeting': '1785917027586',
    'utag_main_dc_region': 'ap-east-1%3Bexp-session',
    '_ce.clock_data': '***HIDDEN***',
    'BVBRANDSID': '2fb3cef0-a8a3-427c-9626-b549211c5a20',
    '__ar_v4': 'TLGS2MDMOFEALNQLHLTLBW%3A20260722%3A100%7CQWC5THA5TZFOLOWWLOOPBD%3A20260722%3A100',
    '_tq_id.TV-7209544572-1.e625': 'aaec9c85032f6909.1780291504.0.1785917028..',
    '_clck': '1cbbq6o%5E2%5Eg8c%5E1%5E2353',
    '_sctr': '1%7C1785868200000',
    '__attentive_session_id': '***HIDDEN***',
    '__attentive_dv': '1',
    '__attentive_ss_referrer': 'ORGANIC',
    'utag_main_ttd_uuid': '0ab22fe8-bfa7-41f7-8b97-8d607fadc075%3Bexp-session',
    'utag_main_cms_256': '1%3Bexp-session',
    'utag_main__ss': '0%3Bexp-session',
    '_gcl_au': '1.1.388504494.1780291503.1049741007.1785917027.1785917040.1911699860.1785917027.1785917040',
    'ttcsid': '1785917027793::9H3nZbyA6UsfItazb8JR.34.1785917103791.0::1.-5993.0::75992.6.836.2258::70247.39.1819',
    'ttcsid_CC2K5NJC77U26CFATFP0': '1785917027792::YBbNgcePa6yJsESKv0VL.42.1785917103791.1',
    'SSRT': '***HIDDEN***',
    'utag_main__pn': '2%3Bexp-session',
    'utag_main__se': '8%3Bexp-session',
    'utag_main__st': '1785918906382%3Bexp-session',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Aug+05+2026+13%3A35%3A07+GMT%2B0530+(India+Standard+Time)&version=202606.1.0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&consentId=2b255836-e584-40b8-8fb9-75692ba80197&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0002%3A1%2CC0001%3A1%2CC0003%3A1%2CC0004%3A1&iType=1&geolocation=GB%3BENG&AwaitingReconsent=false&isDntEnabled=0&prevHadToken=0',
    'utag_main_dc_event': '2%3Bexp-session',
    'mp_urbn_urbanoutfitters_na_mixpanel': '%7B%22distinct_id%22%3A%20%2219ed000128082e-0c6414a4bff057-26061151-e1000-19ed0001281133d%22%2C%22bc_persist_updated%22%3A%201781606126210%7D',
    '_ga_BBMWPLK0E5': 'GS2.1.s1785917027$o24$g1$t1785917107$j51$l0$h0',
    '_ce.s': '***HIDDEN***',
    'cebsp_': '105',
    '__attentive_pv': '2',
    '_clsk': '1pd3nvf%5E1785917107979%5E3%5E1%5Et.clarity.ms%2Fcollect',
    'datadome': '***HIDDEN***',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Referer': 'https://www.urbanoutfitters.com/shop/bdg-alex-breezy-cotton-oversized-button-down-shirt?color=048&type=REGULAR&quantity=1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
    'sec-ch-device-memory': '32',
    'sec-ch-ua': '"Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-full-version-list': '"Not;A=Brand";v="8.0.0.0", "Chromium";v="150.0.7871.127", "Google Chrome";v="150.0.7871.127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    # 'Cookie': '***HIDDEN***',
}

response = requests.get('https://www.urbanoutfitters.com/help/return-policy',
                        # cookies=cookies,
                        headers=headers
                        )

print(response)
with open("policy.html", "w", encoding='utf-8') as f:
    f.write(response.text)
html = response.text
from parsel import Selector

selector = Selector(text=html)
return_policy = selector.xpath(
    '//h2[contains(normalize-space(), "Return Policy")]'
    '/ancestor::div[contains(@class, "c-pwa-content-module")][1]'
    '//div[contains(@class, "c-pwa-text-component__body-copy")]//text()'
).getall()
return_policy = " ".join(x.strip() for x in return_policy if x.strip())
# return_policy = selector.xpath(
#     '//h2[contains(normalize-space(), "Return Policy")]'
#     '/ancestor::div[contains(@class, "c-pwa-content-module")][1]'
#     '//div[contains(@class, "c-pwa-text-component__body-copy")]//text()[normalize-space() and not(contains(., "Our Online Return Policy"))]'
# ).getall()
#
# return_policy = " ".join(x.strip() for x in return_policy if x.strip())

print(return_policy)


# ==================================================================================================
import requests

cookies = {
    'ttcsid_CC2K5NJC77U26CFATFP0': '1778732226999::ZW7Y3aivq6OBlL_0FIdV.58.1778733326116.1',
    'SSLB': '1',
    'urbn_uuid': 'af184042-6c60-4e50-895b-010cd13ebefc',
    '_pxvid': '***HIDDEN***',
    'utag_main_v_id': '***HIDDEN***',
    '_fbp': 'fb.1.1778733389743.590532045229385853.Bg',
    '_ga': 'GA1.1.620004048.1778733390',
    'rbuid': 'rbos-800b632a-4a83-4f88-8161-9e73192f606c',
    '_tt_enable_cookie': '1',
    '_ttp': '01KRJCB6YRSAXR7B1A67E3JM8M_.tt.1',
    '_lc2_fpi': '18c6eee2a756--01krjcb709wcjhn0k7qs13pbtx',
    '__adroll_fpc': '***HIDDEN***',
    '__attentive_cco': '1778733390999',
    '_pin_unauth': 'dWlkPU9XUXlNMll5WlRndE9XUTVNeTAwTmpKaUxXSm1NR010WkRaa1kyVTRNR0k0TUdWaQ',
    '_svsid': '***HIDDEN***',
    '_scid': 'cvrISxuIyTxYW3kY5L8NNVSPhM6am6j7r6caWw',
    'BVBRANDID': '574940e3-5f25-405f-8aff-19bb12a7dec6',
    'ttcsid': '1778732074499::ue00j8KXzTSV6yb1zj4x.59.1778733326116.0::1.1229461.1249253::923057.2.785.572::1782746.82.86',
    'urbn_dy_id': '5728578981195810175',
    '__attentive_id': '***HIDDEN***',
    '_attn_': '***HIDDEN***',
    'utag_main_dc_visit': 'NaN',
    'bluecoreNV': 'false',
    '_pxhd': '***HIDDEN***',
    'mp_urbn_urbanoutfitters_eu_mixpanel': '%7B%22distinct_id%22%3A%20%2219e24c597d0295-0c0cd5888fa6c48-26061151-e1000-19e24c597d1ef2%22%2C%22bc_persist_updated%22%3A%201782300248606%7D',
    'ttcsid_CC34JGRC77UFTO4NILP0': '1782363534986::uSvopjF6CX4mQi4RTj_x.2.1782364208663.0',
    'urbn_data_center_id': 'US-PA',
    'urbn_tracer': 'ZES6YAUNZI',
    'urbn_geo_region': 'US-PA',
    '_dyid_server': '1945555281327381773',
    '_dyid': '1945555281327381773',
    '__obref': '2b427ded-eba3-4f31-b0ef-a5505fe20e78',
    'smartDash': '65df30c0-4774-4879-a3b5-75b1adb9ba3f',
    'mt.v': '2.255158994.1786011871820',
    'styliticsWidgetSession': '09237f28-6f2e-460e-b047-918c033d7048',
    'urbn_is_active_dy_session': 'true',
    'urbn_channel': 'web',
    'urbn_currency': 'USD',
    'urbn_country': 'IN',
    'urbn_inventory_pool': 'INTL_DIRECT',
    'urbn_language': 'en-US',
    'siteId': 'uo-us',
    'urbn_edgescape_site_id': 'uo-us',
    'urbn_site_id': 'uo-us',
    '_li_dcdm_c': '.urbanoutfitters.com',
    '_lc2_fpi_js': '18c6eee2a756--01krjcb709wcjhn0k7qs13pbtx',
    'cebs': '1',
    '_CEFT': 'Q%3D%3D%3D',
    '_sctr': '1%7C1786991400000',
    'QSI_SI_9AEkoeXmCVAdTMN_intercept': 'true',
    '_clck': '9wi3m2%5E2%5Eg8q%5E1%5E2378',
    '_dyjsession': 'uqe7mhxcm7zo46lsv6wsnudteqqkbmg9',
    'urbn_page_visits_count': '%7B%22uo-us%22%3A2%7D',
    '_scid_r': 'a_rISxuIyTxYW3kY5L8NNVSPhM6am6j7r6cbzA',
    '__ar_v4': 'TLGS2MDMOFEALNQLHLTLBW%3A20260805%3A8%7CQWC5THA5TZFOLOWWLOOPBD%3A20260805%3A8',
    '_rdt_uuid': '1778733390735.4fc56b0e-4221-4362-b9dd-16207c77267a',
    '_tq_id.TV-7209544572-1.e625': 'cd8f4adb041e1934.1767158160.0.1787137149..',
    '_uetsid': '***HIDDEN***',
    '_uetvid': '***HIDDEN***',
    '_ce.clock_data': '***HIDDEN***',
    '__attentive_dv': '1',
    'ttcsid_CC2K5NJC77U26CFATFP0': '1787137101911::FXwecQ8qokIj76k7DU4W.97.1787137220494.1',
    'ss-enable-401-reauth-modal': '1',
    'SS_ENABLE_STYLITICS': '1',
    'ss-enable-multi-label-returns': 'true',
    'SSID': '***HIDDEN***',
    'SSSC': '***HIDDEN***',
    'SSRT': '***HIDDEN***',
    'urbn_auth_payload': '***HIDDEN***',
    'utag_main__sn': '86',
    'utag_main__se': '1%3Bexp-session',
    'utag_main__ss': '1%3Bexp-session',
    'utag_main__st': '1787141377377%3Bexp-session',
    'utag_main_ses_id': '1787139577377%3Bexp-session',
    'utag_main__pn': '1%3Bexp-session',
    'utag_main_isLoggedIn': 'false%3Bexp-session',
    'utag_main_tag_session_256': '1%3Bexp-session',
    'utag_main_dc_event': '1%3Bexp-session',
    'mp_urbn_urbanoutfitters_na_mixpanel': '%7B%22distinct_id%22%3A%20%2219e24c597d0295-0c0cd5888fa6c48-26061151-e1000-19e24c597d1ef2%22%2C%22bc_persist_updated%22%3A%201782378501912%7D',
    'utag_main_dc_region': 'ap-east-1%3Bexp-session',
    'bc_invalidateUrlCache_targeting': '1787139578144',
    'cebsp_': '7',
    '_clsk': 'ckihil%5E1787139579119%5E17%5E0%5El.clarity.ms%2Fcollect',
    '__attentive_session_id': '***HIDDEN***',
    '__attentive_pv': '1',
    '__attentive_ss_referrer': 'ORGANIC',
    'utag_main_ttd_uuid': '7dfd94e8-427e-4856-bea5-007797578a0a%3Bexp-session',
    'utag_main_cms_256': '1%3Bexp-session',
    'datadome': '***HIDDEN***',
    '_ce.s': '***HIDDEN***',
    'ttcsid': '1787139533400::t77sBGwn2hEpaAJUrm7Q.103.1787139533400.0::1.42077.46813::1764458.25.875.1727::198640.304.1400',
    '_ga_BBMWPLK0E5': 'GS2.1.s1787139578$o52$g1$t1787139733$j60$l0$h0',
    '_gcl_au': '1.1.1355511563.1783321330.71873036.1787139734.1787139733.877716464.1787137101.1787139733',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Aug+19+2026+17%3A12%3A13+GMT%2B0530+(India+Standard+Time)&version=202606.1.0&browserGpcFlag=0&isDntEnabled=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&consentId=af184042-6c60-4e50-895b-010cd13ebefc&interactionCount=1&isAnonUser=1&prevHadToken=0&landingPath=https%3A%2F%2Fwww.urbanoutfitters.com%2Fhelp%2Finternational-shipping&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&crTime=1787139733951',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Referer': 'https://www.urbanoutfitters.com/jackets-coats-for-women',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36',
    'sec-ch-device-memory': '16',
    'sec-ch-ua': '"Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-full-version-list': '"Not=A?Brand";v="99.0.0.0", "Google Chrome";v="151.0.7922.138", "Chromium";v="151.0.7922.138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    # 'Cookie': '***HIDDEN***',
}

response = requests.get(
    # 'https://www.urbanoutfitters.com/shop/out-from-under-pretty-plush-fleece-quarter-zip-pullover?color=066&type=REGULAR&new_tab=1&a15_rid=95a9ddf393b3/yPulLEtq70-263365&quantity=1',
    # 'https://www.urbanoutfitters.com/shop/bdg-off-duty-ribbed-scoop-neck-short-sleeve-tee?color=040&recommendation=pdp-secondary-DYrectray-Recently%20Viewed',
    'https://www.urbanoutfitters.com/shop/standard-cloth-postgame-stripe-sweatpants?color=043&type=REGULAR&new_tab=1&a15_rid=2f5ab8a491bb%2Fcj2dKQzaZ4-289301',
    cookies=cookies,
    headers=headers,
)

print(response.status_code)
html = response.text
from parsel import Selector

selector = Selector(text=html)

rows = selector.xpath(
    '//h3[normalize-space()="Shipping"]'
    '/following-sibling::div[contains(@class, "s-pwa-cms")][1]'
    '//table//tbody/tr'
)

shipping_cost = {}
estimated_delivery_time = {}

for row in rows:

    method = row.xpath('./td[1]//text()').getall()
    delivery_time = row.xpath('./td[2]//text()').getall()
    cost = row.xpath('./td[3]//text()').getall()

    method = " ".join(x.strip() for x in method if x.strip())
    delivery_time = " ".join(x.strip() for x in delivery_time if x.strip())
    cost = " ".join(x.strip() for x in cost if x.strip())

    if method:
        estimated_delivery_time[method] = delivery_time
        shipping_cost[method] = cost

print(json.dumps([shipping_cost]))
print(json.dumps([estimated_delivery_time]))

tags = selector.xpath(
    '//p[@data-qa-pdp-secondary-callout="true"]//span/text()'
    ' | '
    '//p[@data-qa-badge]/@data-qa-badge'
).getall()

tags = " | ".join(
    x.strip()
    for x in selector.xpath(
        '//p[@data-qa-pdp-secondary-callout="true"]//span/text()'
        ' | '
        '//p[@data-qa-badge]/@data-qa-badge'
    ).getall()
    if x.strip()
)
print(tags)