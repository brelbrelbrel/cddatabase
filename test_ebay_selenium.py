# -*- coding: utf-8 -*-
"""Test eBay scraping with Selenium"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# Setup Chrome options
options = Options()
options.add_argument('--headless')  # Run without GUI
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

print("Starting Chrome...")
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    url = 'https://www.ebay.com/sch/i.html?_nkw=King+Crimson+CD&LH_Sold=1&_sacat=176985'
    print(f"Loading: {url}")
    driver.get(url)

    time.sleep(3)  # Wait for page to load

    # Get page title
    print(f"Title: {driver.title}")

    # Check for block
    if 'Pardon' in driver.title or 'Interruption' in driver.title:
        print("BLOCKED by eBay")
    else:
        # Find prices
        html = driver.page_source
        prices = re.findall(r'price">([^<]+)<', html)
        print(f"Prices found: {len(prices)}")
        for p in prices[:5]:
            print(f"  {p}")

    driver.quit()
    print("Done!")

except Exception as e:
    print(f"Error: {e}")
