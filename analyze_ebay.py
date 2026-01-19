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
d.get('https://www.ebay.com/sch/i.html?_nkw=Pink+Floyd+CD&LH_Complete=1&LH_Sold=1&_sacat=176985')
time.sleep(3)
html = d.page_source

# Save for inspection
open('ebay_debug.html', 'w', encoding='utf-8').write(html)

# Find all class names with price
classes = set(re.findall(r'class="([^"]*price[^"]*)"', html, re.I))
print("Price-related classes:")
for c in list(classes)[:15]:
    print(f"  {c}")

# Try to find item blocks
items = re.findall(r'<li[^>]*class="[^"]*s-item[^"]*"[^>]*>(.*?)</li>', html, re.DOTALL)
print(f"\nFound {len(items)} items")
if items:
    # Check first item
    first = items[0][:2000]
    prices_in_item = re.findall(r'\$[\d,.]+', first)
    print(f"Prices in first item: {prices_in_item}")

d.quit()
