#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time, os

opts = Options()
# Use headless new mode if supported
opts.add_argument('--headless=new')
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-gpu')
opts.add_argument('--window-size=1600,1200')

# Use system chromium binary
chrome_path = '/usr/bin/chromium-browser'
if not os.path.exists(chrome_path):
    chrome_path = '/usr/bin/chromium'

# chromedriver path
chromedriver_path = '/usr/bin/chromedriver'
if not os.path.exists(chromedriver_path):
    chromedriver_path = '/usr/bin/chromium-chromedriver'

opts.binary_location = chrome_path
service = Service(executable_path=chromedriver_path)

# instantiate
print('Starting webdriver with', chrome_path, chromedriver_path)
driver = webdriver.Chrome(service=service, options=opts)

urls = [
    ('services_list', 'http://127.0.0.1:8001/services/'),
    ('booking_new', 'http://127.0.0.1:8001/bookings/new/'),
]

os.makedirs('screenshots', exist_ok=True)
for name, url in urls:
    try:
        print('Loading', url)
        driver.get(url)
        time.sleep(1.5)
        fname = os.path.join('screenshots', f'{name}.png')
        driver.save_screenshot(fname)
        print('saved', fname)
    except Exception as e:
        print('error', url, e)

driver.quit()
print('Done')
