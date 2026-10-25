# using_playwright_getting_token.py

import asyncio
import json
import re
from playwright.async_api import async_playwright
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "datadome_token.txt")

# OUTPUT_FILE = "datadome_token.txt"
token_saved = None


async def handle_response(response):
    global token_saved
    if token_saved:
        return
    if "https://api-js.datadome.co/js/" not in response.url:
        return
    try:
        data = await response.json()
        cookie = data.get("cookie", "")
        match = re.search(r"datadome=([^;]+)", cookie)
        if match:
            token_saved = match.group(1)
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(token_saved)
            print("New DataDome Token:", token_saved)
    except Exception as e:
        print(e)

# async def handle_response(response):
#     global token_saved, response_count
#     if "https://api-js.datadome.co/js/" not in response.url:
#         return
#     response_count += 1
#     print(f"DataDome JS Response #{response_count}")
#     # Ignore the first response
#     if response_count == 1:
#         print("Ignoring first DataDome response")
#         return
#     try:
#         data = await response.json()
#         cookie = data.get("cookie", "")
#         match = re.search(r"datadome=([^;]+)", cookie)
#         if match:
#             token_saved = match.group(1)
#             with open(TOKEN_FILE, "w", encoding="utf-8") as f:
#                 f.write(token_saved)
#             print("Updated DataDome Token:", token_saved)
#     except Exception as e:
#         print(e)

async def auto_scroll(page):
    previous_height = 0
    while True:
        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        previous_height = current_height
        await page.wait_for_timeout(1500)
    await page.evaluate("window.scrollTo(0,0)")


async def generate_token():
    # global token_saved, response_count
    # token_saved = None
    # response_count = 0
    global token_saved
    token_saved = None
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        page.on(
            "response",
            lambda response: asyncio.create_task(handle_response(response))
        )
        await page.goto(
            "https://www.constructionweekonline.com/",
            wait_until="domcontentloaded",
            timeout=120000
        )
        await page.wait_for_timeout(5000)
        await auto_scroll(page)
        await page.mouse.move(300, 300)
        await page.mouse.move(700, 500)
        await page.mouse.move(500, 200)
        # wait until token arrives
        for _ in range(20):
            if token_saved:
                break
            await page.wait_for_timeout(1000)
        await browser.close()
    return token_saved


def get_new_token_from_browser():
    return asyncio.run(generate_token())

if __name__ == '__main__':
    token =get_new_token_from_browser()
    print(token)
    # import sys
    #
    # print(sys.executable)