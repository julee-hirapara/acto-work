from appium import webdriver
from appium.options.android import UiAutomator2Options
import time

options = UiAutomator2Options()

options.platform_name = "Android"
options.device_name = "emulator-5554"
options.app_package = "in.co.metro.customerappmetro"
options.app_activity = "com.jio.bapp.jcp.metro.FyndWebViewActivity"
options.automation_name = "UiAutomator2"

# 🔥 IMPORTANT ADD THIS
options.set_capability("chromedriverAutodownload", True)

driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

time.sleep(10)

print(driver.contexts)

driver.quit()