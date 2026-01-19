# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, re

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
service = Service(ChromeDriverManager().install())
d = webdriver.Chrome(service=service, options=options)

url = 'https://www.ebay.com/sch/i.html?_nkw=Pink+Floyd+CD&LH_Complete=1&LH_Sold=1&_sacat=176985'
print(f"Fetching: {url}")
d.get(url)
time.sleep(3)
html = d.page_source
print(f"HTML size: {len(html)}")

# Look for USD prices with $ sign
usd_prices = re.findall(r'\$(\d+\.\d{2})', html)
print(f"USD prices: {usd_prices[:15]}")

# s-item__price
item_prices = re.findall(r's-item__price[^>]*>([^<]+)', html)
print(f"Item prices: {item_prices[:10]}")

d.quit()
