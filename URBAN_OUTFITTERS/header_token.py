# # # # from playwright.sync_api import sync_playwright
# # # # import time
# # # #
# # # #
# # # # def get_urban_outfitters_token(timeout=12):
# # # #     """Launches Playwright, loads UO site, and returns Authorization Bearer token."""
# # # #
# # # #     with sync_playwright() as p:
# # # #         browser = p.chromium.launch(headless=False)
# # # #         context = browser.new_context()
# # # #         page = context.new_page()
# # # # "Press & Hold to confirm you are
# # # # a human (and not a bot).
# # # # "
# # # #         state = {"token": None}
# # # #
# # # #         def extract_token(headers):
# # # #             for k, v in headers.items():
# # # #                 if k.lower() == "authorization" and v.startswith("Bearer "):
# # # #                     return v
# # # #             return None
# # # #
# # # #         def log_request(request):
# # # #             if state["token"]:
# # # #                 return
# # # #             auth = extract_token(request.headers)
# # # #             if auth:
# # # #                 print("\nFOUND TOKEN:")
# # # #                 print(auth)
# # # #                 state["token"] = auth
# # # #
# # # #         context.on("request", log_request)
# # # #
# # # #         print("Opening page...")
# # # #         page.goto("https://www.urbanoutfitters.com/", wait_until="domcontentloaded")
# # # #
# # # #         # wait until timeout or until token is found
# # # #         start = time.time()
# # # #         while time.time() - start < timeout and not state["token"]:
# # # #             page.wait_for_timeout(500)
# # # #
# # # #         browser.close()
# # # #         return state["token"]
# # # #
# # # #
# # # # # -------------------------
# # # # # Example usage:
# # # # # -------------------------
# # # # if __name__ == '__main__':
# # # #     token = get_urban_outfitters_token()
# # # #     print("\nReturned Token:", token)
# # #
# # #
# # #
# # # from playwright.sync_api import sync_playwright, TimeoutError
# # # import time
# # #
# # #
# # # BOT_TEXT = "Press & Hold"
# # # TARGET_URL = "https://www.urbanoutfitters.com/"
# # #
# # #
# # # def get_urban_outfitters_token(
# # #     timeout=12,
# # #     max_attempts=3,
# # #     retry_delay=10
# # # ):
# # #     """
# # #     Tries to fetch Urban Outfitters Bearer token.
# # #     If bot challenge appears, closes browser and retries.
# # #     """
# # #
# # #     for attempt in range(1, max_attempts + 1):
# # #         print(f"\n🚀 Attempt {attempt}/{max_attempts}")
# # #
# # #         with sync_playwright() as p:
# # #             browser = p.chromium.launch(
# # #                 headless=False,
# # #                 args=[
# # #                     "--disable-blink-features=AutomationControlled",
# # #                 ],
# # #             )
# # #
# # #             context = browser.new_context()
# # #             page = context.new_page()
# # #             # time.sleep(10)
# # #             state = {"token": None}
# # #
# # #             def extract_token(headers):
# # #                 for k, v in headers.items():
# # #                     if k.lower() == "authorization" and v.startswith("Bearer "):
# # #                         return v
# # #                 return None
# # #
# # #             def log_request(request):
# # #                 if state["token"]:
# # #                     return
# # #                 auth = extract_token(request.headers)
# # #                 if auth:
# # #                     print("\n✅ FOUND TOKEN:")
# # #                     print(auth)
# # #                     state["token"] = auth
# # #
# # #             context.on("request", log_request)
# # #
# # #             print("Opening page...")
# # #             try:
# # #                 page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=20000)
# # #             except TimeoutError:
# # #                 print("⚠️ Page load timeout")
# # #                 browser.close()
# # #                 continue
# # #
# # #             # --- Check for bot challenge ---
# # #             try:
# # #                 if page.locator(f"text={BOT_TEXT}").is_visible(timeout=3000):
# # #                     print("🤖 Bot challenge detected (Press & Hold)")
# # #                     browser.close()
# # #                     time.sleep(retry_delay)
# # #                     continue
# # #             except TimeoutError:
# # #                 pass  # text not found → good sign
# # #
# # #             # --- Wait for token ---
# # #             start = time.time()
# # #             while time.time() - start < timeout:
# # #                 if state["token"]:
# # #                     cookies = context.cookies()
# # #                     browser.close()
# # #                     return state["token"], cookies
# # #                 # if state["token"]:
# # #                 #     browser.close()
# # #                 #     return state["token"]
# # #                 page.wait_for_timeout(500)
# # #
# # #             print("⏱ Token not found in this attempt")
# # #             browser.close()
# # #             time.sleep(retry_delay)
# # #
# # #     print("❌ Failed to get token after all attempts")
# # #     return None, None
# #
# #
# #
# # # from playwright.sync_api import sync_playwright
# # # import time
# # #
# # #
# # # def get_urban_outfitters_token(timeout=12):
# # #     """Launches Playwright, loads UO site, and returns Authorization Bearer token."""
# # #
# # #     with sync_playwright() as p:
# # #         browser = p.chromium.launch(headless=False)
# # #         context = browser.new_context()
# # #         page = context.new_page()
# # # "Press & Hold to confirm you are
# # # a human (and not a bot).
# # # "
# # #         state = {"token": None}
# # #
# # #         def extract_token(headers):
# # #             for k, v in headers.items():
# # #                 if k.lower() == "authorization" and v.startswith("Bearer "):
# # #                     return v
# # #             return None
# # #
# # #         def log_request(request):
# # #             if state["token"]:
# # #                 return
# # #             auth = extract_token(request.headers)
# # #             if auth:
# # #                 print("\nFOUND TOKEN:")
# # #                 print(auth)
# # #                 state["token"] = auth
# # #
# # #         context.on("request", log_request)
# # #
# # #         print("Opening page...")
# # #         page.goto("https://www.urbanoutfitters.com/", wait_until="domcontentloaded")
# # #
# # #         # wait until timeout or until token is found
# # #         start = time.time()
# # #         while time.time() - start < timeout and not state["token"]:
# # #             page.wait_for_timeout(500)
# # #
# # #         browser.close()
# # #         return state["token"]
# # #
# # #
# # # # -------------------------
# # # # Example usage:
# # # # -------------------------
# # # if __name__ == '__main__':
# # #     token = get_urban_outfitters_token()
# #     print("\nReturned Token:", token)
#
#
#
# from playwright.sync_api import sync_playwright, TimeoutError
# import time
#
#
# BOT_TEXT = "Press & Hold"
# TARGET_URL = "https://www.urbanoutfitters.com/"
#
#
# def get_urban_outfitters_token(
#     timeout=12,
#     max_attempts=3,
#     retry_delay=10
# ):
#     """
#     Tries to fetch Urban Outfitters Bearer token.
#     If bot challenge appears, closes browser and retries.
#     """
#
#     for attempt in range(1, max_attempts + 1):
#         print(f"\n🚀 Attempt {attempt}/{max_attempts}")
#
#         with sync_playwright() as p:
#             browser = p.chromium.launch(
#                 headless=False,
#                 args=[
#                     "--disable-blink-features=AutomationControlled",
#                 ],
#             )
#
#             context = browser.new_context()
#             page = context.new_page()
#
#             state = {"token": None}
#
#             def extract_headers(headers):
#                 auth = None
#                 datadome = None
#                 data_center = None
#
#                 for k, v in headers.items():
#                     k = k.lower()
#
#                     if k == "authorization" and v.startswith("Bearer "):
#                         auth = v
#
#                     # elif k == "x-datadome-clientid":
#                     #     datadome = v
#                     #
#                     # elif k == "x-urbn-primary-data-center-id":
#                     #     data_center = v
#
#                 return auth
#
#             def extract_token(headers):
#                 print(headers)
#                 for k, v in headers.items():
#
#                     if k.lower() == "authorization" and v.startswith("Bearer "):
#                         return v
#
#                 return None
#
#             def log_request(request):
#                 if state["token"]:
#                     return
#                 auth = extract_token(request.headers)
#                 if auth:
#                     state["token"] = auth
#             # def log_request(request):
#             #     if all(state.values()):
#             #         return
#             #
#             #     auth, datadome, data_center = extract_headers(request.headers)
#             #
#             #     if auth:
#             #         state["authorization"] = auth
#             #
#             #     if datadome:
#             #         state["datadome"] = datadome
#             #
#             #     if data_center:
#             #         state["data_center"] = data_center
#             #
#             #     if all(state.values()):
#             #         print("\n✅ ALL HEADERS FOUND:")
#             #         print(state)
#
#             context.on("request", log_request)
#             try:
#                 page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=20000)
#             except TimeoutError:
#                 print("⚠️ Page load timeout")
#                 browser.close()
#                 continue
#
#             # --- Check for bot challenge ---
#             try:
#                 if page.locator(f"text={BOT_TEXT}").is_visible(timeout=3000):
#                     print("🤖 Bot challenge detected (Press & Hold)")
#                     browser.close()
#                     time.sleep(retry_delay)
#                     continue
#             except TimeoutError:
#                 pass  # text not found → good sign
#
#             # --- Wait for token ---
#             start = time.time()
#             while time.time() - start < timeout:
#                 if all(state.values()):
#                     browser.close()
#                     return state
#                 page.wait_for_timeout(500)
#
#             print("⏱ Token not found in this attempt")
#             browser.close()
#             time.sleep(retry_delay)
#     print("❌ Failed to get token after all attempts")
#     return None




from playwright.sync_api import sync_playwright, TimeoutError
import time


BOT_TEXT = "Press & Hold"
TARGET_URL = "https://www.urbanoutfitters.com/"


def get_urban_outfitters_token(
    timeout=12,
    max_attempts=3,
    retry_delay=10
):
    """
    Tries to fetch Urban Outfitters Bearer token.
    If bot challenge appears, closes browser and retries.
    """

    for attempt in range(1, max_attempts + 1):
        print(f"\n🚀 Attempt {attempt}/{max_attempts}")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            context = browser.new_context()
            page = context.new_page()

            # state = {"token": None}
            state = {
                "token": None,
                "headers": None
            }
            def extract_token(headers):
                # print(headers)
                for k, v in headers.items():

                    if k.lower() == "authorization" and v.startswith("Bearer "):
                        return v
                return None

            # def log_request(request):
            #     if state["token"]:
            #         return
            #     auth = extract_token(request.headers)
            #     if auth:
            #         print("\n✅ FOUND TOKEN:")
            #         print(auth)
            #         state["token"] = auth
            def log_request(request):
                if state["headers"]:
                    return

                headers = request.headers

                has_auth = False
                has_datadome = False

                for k, v in headers.items():
                    k = k.lower()

                    if k == "authorization" and v.startswith("Bearer "):
                        has_auth = True
                        state["token"] = v

                    elif k == "x-datadome-clientid":
                        has_datadome = True

                # 🎯 Capture ONLY when both exist (this is key)
                if has_auth and has_datadome:
                    print("\n✅ PERFECT MATCH REQUEST:", request.url)

                    state["headers"] = headers

            context.on("request", log_request)

            print("Opening page...")
            try:
                page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=20000)
            except TimeoutError:
                print("⚠️ Page load timeout")
                browser.close()
                continue

            # --- Check for bot challenge ---
            try:
                if page.locator(f"text={BOT_TEXT}").is_visible(timeout=3000):
                    print("🤖 Bot challenge detected (Press & Hold)")
                    browser.close()
                    time.sleep(retry_delay)
                    continue
            except TimeoutError:
                pass  # text not found → good sign

            # --- Wait for token ---
            start = time.time()
            while time.time() - start < timeout:
                # if state["token"]:
                #     browser.close()
                #     return state["token"]
                if state["headers"]:
                    browser.close()
                    return state
                page.wait_for_timeout(500)

            print("⏱ Token not found in this attempt")
            browser.close()
            time.sleep(retry_delay)

    print("❌ Failed to get token after all attempts")
    return None


