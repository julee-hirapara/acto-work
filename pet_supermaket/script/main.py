# # extract cat links
# # import requests
# from curl_cffi import requests
# from parsel import Selector
#
# headers = {
#     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#     'accept-language': 'en-US,en;q=0.9',
#     'cache-control': 'max-age=0',
#     'priority': 'u=0, i',
#     'referer': 'https://www.petsupermarket.com/',
#     'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'document',
#     'sec-fetch-mode': 'navigate',
#     'sec-fetch-site': 'same-origin',
#     'sec-fetch-user': '?1',
#     'upgrade-insecure-requests': '1',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
# }
#
# response = requests.get('https://www.petsupermarket.com/',
#                         impersonate="chrome110"
#                         # headers=headers
#                         )
# print(response)
# with open("data.html", "w", encoding='UTf-8') as f:
#     f.write(response.text)
#
# with open("data.html", "r", encoding='utf-8') as f:
#     html = f.read()
# sel = Selector(text=html)
# data = {}
#
# # loop each main category block
# categories = sel.xpath('//li[contains(@class,"menu-name-container")]')
#
# for cat in categories:
#     cat_name = cat.xpath('.//span[@class="menu-title"]/text()').get()
#
#     # skip unwanted ones
#     if cat_name in ["Deals", "Services", "Featured", "Brands"]:
#         continue
#
#     # get all subcategories UNTIL next category
#     subcats = cat.xpath(
#         'following-sibling::li//a[contains(@class,"sub-category")]'
#     )
#
#     sub_list = []
#
#     for sub in subcats:
#         name = sub.xpath('.//text()').get()
#         link = sub.xpath('./@href').get()
#
#         if link and link.startswith('/'):
#             link = "https://www.petsupermarket.com" + link
#
#         sub_list.append({
#             "name": name,
#             "link": link
#         })
#
#     data[cat_name] = sub_list
#
# # print result
# import pprint
#
# pprint.pprint(data)
#
# # category = sel.xpath('//li[contains(@class,"menu-name-container")]//span[@class="menu-title"]/text()').getall()
# #
# # print("category name ::::::::;", category)
# # category_links = sel.xpath('//li[contains(@class,"menu-name-container")]//a[@class="menu-see-all"]/@href').getall()
# #
# # print("category_links ::::::::::", category_links)
# # subcats = sel.xpath('//a[contains(@class,"sub-category")]')
# #
# # for sub in subcats:
# #     name = sub.xpath('.//text()').get()
# #     link = sub.xpath('./@href').get()
# #     print(f"sub category ::: {name} | link ::: {link}")
# #     # print(name, link)
# # # links = sel.xpath('//li[@role="menuitem"]//a[contains(@class,"sub-category")]/@href').getall()
# # # for i in links:
# # #     print(i)
#
#
# # ------------------------------------------------------------------------------------------------
# # category request
#
# import requests
#
# cookies = {
#     'cqcid': 'ab1mmUIyXSzA3t90XW1I2c1zgB',
#     'cquid': '||',
#     'LastClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'FirstClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'dwanonymous_4053305edc20ff64eb8871bb843fe7be': '***HIDDEN***',
#     '__cq_dnt': '0',
#     'dw_dnt': '0',
#     '_pxhd': '***HIDDEN***',
#     'osano_consentmanager_uuid': '095acbac-9dbd-4c21-a536-0a678c02fa9c',
#     'osano_consentmanager': 'Va8EONnA8cHXhKUqr5ZWIYrKD0seGkP4yWBWBeNKTFXD_hmuPQBXuuOs4i-nYl75FSmE41qsL1gc1JaBRQ2nEZjZI7vBxvHMzn7mOcHEjiQO5JgHDu-kxKi6w0v06Ik8yC8DU6bDXuAtBaeukrS0vFYhYOmOVw68WlzbERw0kHd8xdkeFJRhkDycoAmJN741T-IHsxlGBAixJZlgWuJ-1ASdVQQV0VRdF81kBa4-XhbhlKS1wiYvpnr0RTMYwYnVF4DCcMlUELFcRee70iClaicckLUQV8sZMliO-QnEBYUuUr51n_v05corQC52AumtZTUAkEO23e8=',
#     'og_session_id': '***HIDDEN***',
#     '_pxvid': '***HIDDEN***',
#     'pxcts': '***HIDDEN***',
#     '_gcl_au': '1.1.765787073.1774618640',
#     '__pxvid': '14312175-29e2-11f1-815e-f212657ca150',
#     '_fbp': 'fb.1.1774618642824.146818474712257692',
#     '_tt_enable_cookie': '1',
#     '_ttp': '01KMQR72K7KJQNCK502R1FR156_.tt.1',
#     '__cq_uuid': 'abuW4IQNJDy9gkn91dvrk3wizs',
#     'QuantumMetricUserID': '***HIDDEN***',
#     'dwac_aebb837897655f6bf10f0cf8c8': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I%3D|dw-only|||USD|false|America%2FNew%5FYork|true',
#     'sid': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I',
#     'dwsid': 'sJD4WI_v8Nu-K2COObe-wytVU9U1N2mEm8C5XPV4OdIZWz-s55EIPNKxnKhuQkBPXFWwEszAlqet7Rd2QpxMWg==',
#     '_gid': 'GA1.2.616842992.1774788504',
#     'geo_permission_denied': 'true',
#     'QuantumMetricSessionID': '***HIDDEN***',
#     '__cq_bc': '%7B%22bgtk-PetSupermarket%22%3A%5B%7B%22id%22%3A%22PSI09136%22%2C%22sku%22%3A%222845112329%22%7D%5D%7D',
#     '__pr.gllwvf': 'iw1cF-wIVH',
#     '_gat_UA-20243033-5': '1',
#     '__cq_seg': '0~-0.58!1~-0.29!2~0.04!3~-0.00!4~-0.43!5~0.08!6~0.13!7~0.41!8~-0.42!9~0.14',
#     '_ga_VL84Y20Z19': 'GS2.1.s1774790336$o3$g1$t1774792505$j23$l0$h473992302',
#     '_px2': '***HIDDEN***',
#     '_ga': 'GA1.2.1951877540.1774618641',
#     '_ga_1LLY653XNS': 'GS2.2.s1774790341$o3$g1$t1774792505$j25$l0$h0',
#     '_uetsid': '***HIDDEN***',
#     '_uetvid': '***HIDDEN***',
#     'ttcsid': '1774788509783::tHJ0offpwSIHMShdoEVJ.2.1774792507487.0',
#     'ttcsid_CH8KFEJC77U3VDB5OC4G': '1774788509778::tlw6nWRQmVflANoRN_Ug.2.1774792507488.1',
# }
#
# headers = {
#     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#     'accept-language': 'en-US,en;q=0.9',
#     'cache-control': 'max-age=0',
#     'priority': 'u=0, i',
#     'referer': 'https://www.petsupermarket.com/',
#     'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'document',
#     'sec-fetch-mode': 'navigate',
#     'sec-fetch-site': 'same-origin',
#     'sec-fetch-user': '?1',
#     'upgrade-insecure-requests': '1',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
#     # 'cookie': '***HIDDEN***',
# }
#
# response = requests.get('https://www.petsupermarket.com/dog/food/dry-food/', cookies=cookies, headers=headers)
#
# # ---------------------------------------------------------------------------------------------------
# import requests
#
#
# cookies = {
#     'cqcid': 'ab1mmUIyXSzA3t90XW1I2c1zgB',
#     'cquid': '||',
#     'LastClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'FirstClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'dwanonymous_4053305edc20ff64eb8871bb843fe7be': '***HIDDEN***',
#     '__cq_dnt': '0',
#     'dw_dnt': '0',
#     '_pxhd': '***HIDDEN***',
#     'osano_consentmanager_uuid': '095acbac-9dbd-4c21-a536-0a678c02fa9c',
#     'osano_consentmanager': 'Va8EONnA8cHXhKUqr5ZWIYrKD0seGkP4yWBWBeNKTFXD_hmuPQBXuuOs4i-nYl75FSmE41qsL1gc1JaBRQ2nEZjZI7vBxvHMzn7mOcHEjiQO5JgHDu-kxKi6w0v06Ik8yC8DU6bDXuAtBaeukrS0vFYhYOmOVw68WlzbERw0kHd8xdkeFJRhkDycoAmJN741T-IHsxlGBAixJZlgWuJ-1ASdVQQV0VRdF81kBa4-XhbhlKS1wiYvpnr0RTMYwYnVF4DCcMlUELFcRee70iClaicckLUQV8sZMliO-QnEBYUuUr51n_v05corQC52AumtZTUAkEO23e8=',
#     'og_session_id': '***HIDDEN***',
#     '_pxvid': '***HIDDEN***',
#     'pxcts': '***HIDDEN***',
#     '_gcl_au': '1.1.765787073.1774618640',
#     '__pxvid': '14312175-29e2-11f1-815e-f212657ca150',
#     '_fbp': 'fb.1.1774618642824.146818474712257692',
#     '_tt_enable_cookie': '1',
#     '_ttp': '01KMQR72K7KJQNCK502R1FR156_.tt.1',
#     '__cq_uuid': 'abuW4IQNJDy9gkn91dvrk3wizs',
#     'QuantumMetricUserID': '***HIDDEN***',
#     'dwac_aebb837897655f6bf10f0cf8c8': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I%3D|dw-only|||USD|false|America%2FNew%5FYork|true',
#     'sid': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I',
#     'dwsid': 'sJD4WI_v8Nu-K2COObe-wytVU9U1N2mEm8C5XPV4OdIZWz-s55EIPNKxnKhuQkBPXFWwEszAlqet7Rd2QpxMWg==',
#     '_gid': 'GA1.2.616842992.1774788504',
#     'geo_permission_denied': 'true',
#     'QuantumMetricSessionID': '***HIDDEN***',
#     '__cq_bc': '%7B%22bgtk-PetSupermarket%22%3A%5B%7B%22id%22%3A%22PSI09136%22%2C%22sku%22%3A%222845112329%22%7D%5D%7D',
#     '__pr.gllwvf': 'iw1cF-wIVH',
#     '__cq_seg': '0~-0.58!1~-0.29!2~0.04!3~-0.00!4~-0.43!5~0.08!6~0.13!7~0.41!8~-0.42!9~0.14',
#     '_ga_VL84Y20Z19': 'GS2.1.s1774790336$o3$g1$t1774792513$j15$l0$h473992302',
#     '_ga': 'GA1.2.1951877540.1774618641',
#     '_ga_1LLY653XNS': 'GS2.2.s1774790341$o3$g1$t1774792513$j17$l0$h0',
#     '_px2': '***HIDDEN***',
#     '_uetsid': '***HIDDEN***',
#     '_uetvid': '***HIDDEN***',
#     'ttcsid': '1774788509783::tHJ0offpwSIHMShdoEVJ.2.1774792530033.0',
#     'ttcsid_CH8KFEJC77U3VDB5OC4G': '1774788509778::tlw6nWRQmVflANoRN_Ug.2.1774792530035.1',
# }
#
# headers = {
#     'accept': '*/*',
#     'accept-language': 'en-US,en;q=0.9',
#     'priority': 'u=1, i',
#     'referer': 'https://www.petsupermarket.com/dog/food/dry-food/',
#     'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'empty',
#     'sec-fetch-mode': 'cors',
#     'sec-fetch-site': 'same-origin',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
#     'x-requested-with': 'XMLHttpRequest',
#     # 'cookie': '***HIDDEN***',
# }
#
# params = {
#     'cgid': 'dog_food_dryfood',
#     'start': '29',
#     'sz': '30',
#     'selectedUrl': 'https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Search-UpdateGrid?cgid=dog_food_dryfood&start=29&sz=30',
# }
#
# response = requests.get(
#     'https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Search-UpdateGrid',
#     params=params,
#     cookies=cookies,
#     headers=headers,
# )
#
# # -----------------------------------------------------------------------------------------------
# # 2 page
# import requests
#
# cookies = {
#     'cqcid': 'ab1mmUIyXSzA3t90XW1I2c1zgB',
#     'cquid': '||',
#     'LastClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'FirstClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'dwanonymous_4053305edc20ff64eb8871bb843fe7be': '***HIDDEN***',
#     '__cq_dnt': '0',
#     'dw_dnt': '0',
#     '_pxhd': '***HIDDEN***',
#     'osano_consentmanager_uuid': '095acbac-9dbd-4c21-a536-0a678c02fa9c',
#     'osano_consentmanager': 'Va8EONnA8cHXhKUqr5ZWIYrKD0seGkP4yWBWBeNKTFXD_hmuPQBXuuOs4i-nYl75FSmE41qsL1gc1JaBRQ2nEZjZI7vBxvHMzn7mOcHEjiQO5JgHDu-kxKi6w0v06Ik8yC8DU6bDXuAtBaeukrS0vFYhYOmOVw68WlzbERw0kHd8xdkeFJRhkDycoAmJN741T-IHsxlGBAixJZlgWuJ-1ASdVQQV0VRdF81kBa4-XhbhlKS1wiYvpnr0RTMYwYnVF4DCcMlUELFcRee70iClaicckLUQV8sZMliO-QnEBYUuUr51n_v05corQC52AumtZTUAkEO23e8=',
#     'og_session_id': '***HIDDEN***',
#     '_pxvid': '***HIDDEN***',
#     'pxcts': '***HIDDEN***',
#     '_gcl_au': '1.1.765787073.1774618640',
#     '__pxvid': '14312175-29e2-11f1-815e-f212657ca150',
#     '_fbp': 'fb.1.1774618642824.146818474712257692',
#     '_tt_enable_cookie': '1',
#     '_ttp': '01KMQR72K7KJQNCK502R1FR156_.tt.1',
#     '__cq_uuid': 'abuW4IQNJDy9gkn91dvrk3wizs',
#     'QuantumMetricUserID': '***HIDDEN***',
#     'dwac_aebb837897655f6bf10f0cf8c8': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I%3D|dw-only|||USD|false|America%2FNew%5FYork|true',
#     'sid': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I',
#     'dwsid': 'sJD4WI_v8Nu-K2COObe-wytVU9U1N2mEm8C5XPV4OdIZWz-s55EIPNKxnKhuQkBPXFWwEszAlqet7Rd2QpxMWg==',
#     '_gid': 'GA1.2.616842992.1774788504',
#     'geo_permission_denied': 'true',
#     'QuantumMetricSessionID': '***HIDDEN***',
#     '__cq_bc': '%7B%22bgtk-PetSupermarket%22%3A%5B%7B%22id%22%3A%22PSI09136%22%2C%22sku%22%3A%222845112329%22%7D%5D%7D',
#     '__pr.gllwvf': 'iw1cF-wIVH',
#     '__cq_seg': '0~-0.58!1~-0.29!2~0.04!3~-0.00!4~-0.43!5~0.08!6~0.13!7~0.41!8~-0.42!9~0.14',
#     '_ga_VL84Y20Z19': 'GS2.1.s1774790336$o3$g1$t1774792513$j15$l0$h473992302',
#     '_ga': 'GA1.2.1951877540.1774618641',
#     '_ga_1LLY653XNS': 'GS2.2.s1774790341$o3$g1$t1774792513$j17$l0$h0',
#     '_px2': '***HIDDEN***',
#     '_uetsid': '***HIDDEN***',
#     '_uetvid': '***HIDDEN***',
#     'ttcsid': '1774788509783::tHJ0offpwSIHMShdoEVJ.2.1774792750362.0',
#     'ttcsid_CH8KFEJC77U3VDB5OC4G': '1774788509778::tlw6nWRQmVflANoRN_Ug.2.1774792750366.1',
# }
#
# headers = {
#     'accept': '*/*',
#     'accept-language': 'en-US,en;q=0.9',
#     'priority': 'u=1, i',
#     'referer': 'https://www.petsupermarket.com/dog/food/dry-food/',
#     'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'empty',
#     'sec-fetch-mode': 'cors',
#     'sec-fetch-site': 'same-origin',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
#     'x-requested-with': 'XMLHttpRequest',
#     # 'cookie': '***HIDDEN***',
# }
#
# params = {
#     'cgid': 'dog_food_dryfood',
#     'start': '59',
#     'sz': '30',
#     'selectedUrl': 'https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Search-UpdateGrid?cgid=dog_food_dryfood&start=59&sz=30',
# }
#
# response = requests.get(
#     'https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Search-UpdateGrid',
#     params=params,
#     cookies=cookies,
#     headers=headers,
# )
#
# # ---------------------------------------------------------------------------------------------------------
# # with filter
#
# import requests
#
# cookies = {
#     'cqcid': 'ab1mmUIyXSzA3t90XW1I2c1zgB',
#     'cquid': '||',
#     'LastClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'FirstClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'dwanonymous_4053305edc20ff64eb8871bb843fe7be': '***HIDDEN***',
#     '__cq_dnt': '0',
#     'dw_dnt': '0',
#     '_pxhd': '***HIDDEN***',
#     'osano_consentmanager_uuid': '095acbac-9dbd-4c21-a536-0a678c02fa9c',
#     'osano_consentmanager': 'Va8EONnA8cHXhKUqr5ZWIYrKD0seGkP4yWBWBeNKTFXD_hmuPQBXuuOs4i-nYl75FSmE41qsL1gc1JaBRQ2nEZjZI7vBxvHMzn7mOcHEjiQO5JgHDu-kxKi6w0v06Ik8yC8DU6bDXuAtBaeukrS0vFYhYOmOVw68WlzbERw0kHd8xdkeFJRhkDycoAmJN741T-IHsxlGBAixJZlgWuJ-1ASdVQQV0VRdF81kBa4-XhbhlKS1wiYvpnr0RTMYwYnVF4DCcMlUELFcRee70iClaicckLUQV8sZMliO-QnEBYUuUr51n_v05corQC52AumtZTUAkEO23e8=',
#     'og_session_id': '***HIDDEN***',
#     '_pxvid': '***HIDDEN***',
#     'pxcts': '***HIDDEN***',
#     '_gcl_au': '1.1.765787073.1774618640',
#     '__pxvid': '14312175-29e2-11f1-815e-f212657ca150',
#     '_fbp': 'fb.1.1774618642824.146818474712257692',
#     '_tt_enable_cookie': '1',
#     '_ttp': '01KMQR72K7KJQNCK502R1FR156_.tt.1',
#     '__cq_uuid': 'abuW4IQNJDy9gkn91dvrk3wizs',
#     'QuantumMetricUserID': '***HIDDEN***',
#     'dwac_aebb837897655f6bf10f0cf8c8': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I%3D|dw-only|||USD|false|America%2FNew%5FYork|true',
#     'sid': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I',
#     'dwsid': 'sJD4WI_v8Nu-K2COObe-wytVU9U1N2mEm8C5XPV4OdIZWz-s55EIPNKxnKhuQkBPXFWwEszAlqet7Rd2QpxMWg==',
#     '_gid': 'GA1.2.616842992.1774788504',
#     'geo_permission_denied': 'true',
#     'QuantumMetricSessionID': '***HIDDEN***',
#     '__cq_bc': '%7B%22bgtk-PetSupermarket%22%3A%5B%7B%22id%22%3A%22PSI09136%22%2C%22sku%22%3A%222845112329%22%7D%5D%7D',
#     '__pr.gllwvf': 'iw1cF-wIVH',
#     '__cq_seg': '0~-0.58!1~-0.29!2~0.04!3~-0.00!4~-0.43!5~0.08!6~0.13!7~0.41!8~-0.42!9~0.14',
#     '_ga_VL84Y20Z19': 'GS2.1.s1774790336$o3$g1$t1774792862$j59$l0$h473992302',
#     '_ga': 'GA1.2.1951877540.1774618641',
#     '_gat_UA-20243033-5': '1',
#     '_ga_1LLY653XNS': 'GS2.2.s1774790341$o3$g1$t1774792862$j60$l0$h0',
#     '_px2': '***HIDDEN***',
#     '_uetsid': '***HIDDEN***',
#     '_uetvid': '***HIDDEN***',
#     'ttcsid': '1774788509783::tHJ0offpwSIHMShdoEVJ.2.1774792888773.0',
#     'ttcsid_CH8KFEJC77U3VDB5OC4G': '1774788509778::tlw6nWRQmVflANoRN_Ug.2.1774792888775.1',
# }
#
# headers = {
#     'accept': '*/*',
#     'accept-language': 'en-US,en;q=0.9',
#     'priority': 'u=1, i',
#     'referer': 'https://www.petsupermarket.com/dog/food/dry-food/?prefn1=petProductType&prefv1=ALLERGY+%26+IMMUNITY',
#     'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'empty',
#     'sec-fetch-mode': 'cors',
#     'sec-fetch-site': 'same-origin',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
#     'x-requested-with': 'XMLHttpRequest',
#     # 'cookie': '***HIDDEN***',
# }
#
# params = {
#     'cgid': 'dog_food_dryfood',
#     'prefn1': 'petProductType',
#     'prefv1': 'ALLERGY & IMMUNITY',
#     'page': '0',
#     'selectedUrl': 'https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Search-ShowAjax?cgid=dog_food_dryfood&prefn1=petProductType&prefv1=ALLERGY%20%26%20IMMUNITY',
#     'resetReq': 'false',
# }
#
# response = requests.get(
#     'https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Search-ShowAjax',
#     params=params,
#     cookies=cookies,
#     headers=headers,
# )
#
#
# # --------------------------------------------------------------------------------------------------------
# # with many filter
# import requests
#
# cookies = {
#     'cqcid': 'ab1mmUIyXSzA3t90XW1I2c1zgB',
#     'cquid': '||',
#     'LastClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'FirstClick': '"{\\"datetime\\":\\"2026-03-27T13:37:17.431Z\\",\\"utm_source\\":\\"Direct\\",\\"utm_content\\":\\"Direct\\",\\"utm_campaign\\":\\"Direct\\",\\"utm_medium\\":\\"Direct\\"}"',
#     'dwanonymous_4053305edc20ff64eb8871bb843fe7be': '***HIDDEN***',
#     '__cq_dnt': '0',
#     'dw_dnt': '0',
#     '_pxhd': '***HIDDEN***',
#     'osano_consentmanager_uuid': '095acbac-9dbd-4c21-a536-0a678c02fa9c',
#     'osano_consentmanager': 'Va8EONnA8cHXhKUqr5ZWIYrKD0seGkP4yWBWBeNKTFXD_hmuPQBXuuOs4i-nYl75FSmE41qsL1gc1JaBRQ2nEZjZI7vBxvHMzn7mOcHEjiQO5JgHDu-kxKi6w0v06Ik8yC8DU6bDXuAtBaeukrS0vFYhYOmOVw68WlzbERw0kHd8xdkeFJRhkDycoAmJN741T-IHsxlGBAixJZlgWuJ-1ASdVQQV0VRdF81kBa4-XhbhlKS1wiYvpnr0RTMYwYnVF4DCcMlUELFcRee70iClaicckLUQV8sZMliO-QnEBYUuUr51n_v05corQC52AumtZTUAkEO23e8=',
#     'og_session_id': '***HIDDEN***',
#     '_pxvid': '***HIDDEN***',
#     'pxcts': '***HIDDEN***',
#     '_gcl_au': '1.1.765787073.1774618640',
#     '__pxvid': '14312175-29e2-11f1-815e-f212657ca150',
#     '_fbp': 'fb.1.1774618642824.146818474712257692',
#     '_tt_enable_cookie': '1',
#     '_ttp': '01KMQR72K7KJQNCK502R1FR156_.tt.1',
#     '__cq_uuid': 'abuW4IQNJDy9gkn91dvrk3wizs',
#     'QuantumMetricUserID': '***HIDDEN***',
#     'dwac_aebb837897655f6bf10f0cf8c8': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I%3D|dw-only|||USD|false|America%2FNew%5FYork|true',
#     'sid': 'B6keP-WkulVuufzXW-px5pxstbJffCMKS1I',
#     'dwsid': 'sJD4WI_v8Nu-K2COObe-wytVU9U1N2mEm8C5XPV4OdIZWz-s55EIPNKxnKhuQkBPXFWwEszAlqet7Rd2QpxMWg==',
#     '_gid': 'GA1.2.616842992.1774788504',
#     'geo_permission_denied': 'true',
#     'QuantumMetricSessionID': '***HIDDEN***',
#     '__cq_bc': '%7B%22bgtk-PetSupermarket%22%3A%5B%7B%22id%22%3A%22PSI09136%22%2C%22sku%22%3A%222845112329%22%7D%5D%7D',
#     '__pr.gllwvf': 'iw1cF-wIVH',
#     '__cq_seg': '0~-0.58!1~-0.29!2~0.04!3~-0.00!4~-0.43!5~0.08!6~0.13!7~0.41!8~-0.42!9~0.14',
#     '_ga_VL84Y20Z19': 'GS2.1.s1774790336$o3$g1$t1774792862$j59$l0$h473992302',
#     '_ga': 'GA1.2.1951877540.1774618641',
#     '_ga_1LLY653XNS': 'GS2.2.s1774790341$o3$g1$t1774792862$j60$l0$h0',
#     '_px2': '***HIDDEN***',
#     '_uetsid': '***HIDDEN***',
#     '_uetvid': '***HIDDEN***',
#     'ttcsid': '1774788509783::tHJ0offpwSIHMShdoEVJ.2.1774792981183.0',
#     'ttcsid_CH8KFEJC77U3VDB5OC4G': '1774788509778::tlw6nWRQmVflANoRN_Ug.2.1774792981184.1',
# }
#
# headers = {
#     'accept': '*/*',
#     'accept-language': 'en-US,en;q=0.9',
#     'priority': 'u=1, i',
#     'referer': 'https://www.petsupermarket.com/dog/food/dry-food/?prefn1=brand&prefv1=Victor&prefn2=petCategoryType&prefv2=FOOD&prefn3=petLifeStage&prefv3=ADULT&prefn4=petProductType&prefv4=ALLERGY+%26+IMMUNITY',
#     'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'sec-fetch-dest': 'empty',
#     'sec-fetch-mode': 'cors',
#     'sec-fetch-site': 'same-origin',
#     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
#     'x-requested-with': 'XMLHttpRequest',
#     # 'cookie': '***HIDDEN***',
# }
#
# params = {
#     'cgid': 'dog_food_dryfood',
#     'prefn1': 'brand',
#     'prefv1': 'Victor',
#     'prefn2': 'petCategoryType',
#     'prefv2': 'FOOD',
#     'prefn3': 'petLifeStage',
#     'prefv3': 'ADULT',
#     'prefn4': 'petProductType',
#     'prefv4': 'ALLERGY & IMMUNITY',
#     'page': '0',
#     'selectedUrl': 'https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Search-ShowAjax?cgid=dog_food_dryfood&prefn1=brand&prefv1=Victor&prefn2=petCategoryType&prefv2=FOOD&prefn3=petLifeStage&prefv3=ADULT&prefn4=petProductType&prefv4=ALLERGY%20%26%20IMMUNITY',
#     'resetReq': 'false',
# }
#
# response = requests.get(
#     'https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Search-ShowAjax',
#     params=params,
#     cookies=cookies,
#     headers=headers,
# )
import hashlib
import html as html_lib
from curl_cffi import requests

session = requests.Session()
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
}

response = session.get(
    'https://www.petsupermarket.com/dog/supplies/health-wellness/hip-joint-care/grizzly-functions-hip-joint-aid-liquid-dog-supplement/SCM01518.html',
    # cookies=cookies,
    headers=headers,
    impersonate="chrome110"
)

if response.status_code == 200:
    with open("data.html", "w", encoding='utf-8') as f:
        f.write(response.text)
from parsel import Selector
import json
html = response.text
# sel = Selector(text=html)

sel = Selector(text=response.text)
buttons = sel.xpath('//button[contains(@class,"size-attribute")]')
variation_urls = []
for btn in buttons:
    raw_url = btn.xpath('./@data-url').get()
    if raw_url:
        url = html_lib.unescape(raw_url)
        # url = html.unescape(raw_url)  # decode &amp;
        variation_urls.append(url)
print(variation_urls)
for v_url in variation_urls:
    h = hashlib.sha256(v_url.encode()).hexdigest()
    num = int(h, 16)
    short_id = str(num)[0:16]

    print("Calling:", v_url)

    res = session.get(
        v_url,
        headers=headers,
        impersonate="chrome110"
    )

    print("Status:", res.status_code)

    if res.status_code == 200:
        with open(f"{short_id}.json", "w", encoding='utf-8') as f:
            json.dump(res.json(), f, ensure_ascii=False, indent=4)
        print(short_id, res.status_code)
        print(res.text[:300])  # preview




# # Extract JSON-LD script content
# json_text = sel.xpath('//script[@type="application/ld+json"]/text()').get()
# data = json.loads(json_text)
# # Navigate to offers
# offers = data['offers']['offers']
# for offer in offers:
#     pid = offer['sku']
#     url = offer['url']
#     print("PID:", pid)
#     print("URL:", url)
#     print("-" * 40)
#
# for offer in offers:
#     pid = offer['sku']
#     referer = offer['url']
#
#     # 🔥 Step 1: visit variant page (VERY IMPORTANT)
#     session.get(
#         referer,
#         headers=headers,
#         impersonate="chrome110"
#     )
#
#     headers['referer'] = referer
#
#     data = {
#         'pid': pid,
#         # 'options': '[{"optionId":"AutoShipOptions","selectedValueId":"4_2"}]',
#         # 'isAutoShipSelected': 'true',
#         # 'shipment': 'DTC',
#     }
#
#     res = session.post(
#         'https://www.petsupermarket.com/on/demandware.store/Sites-PetSupermarket-Site/default/Product-updateSubscription',
#         headers=headers,
#         data=data,
#         impersonate="chrome110"
#     )
#     if res.status_code == 200:
#         with open(f"{pid}.json", "w", encoding='utf-8') as f:
#             json.dump(res.json(), f, ensure_ascii=False, indent=4)
#     print(pid, res.status_code)
