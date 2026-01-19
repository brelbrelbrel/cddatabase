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

d.get('https://fril.jp/s?query=King+Crimson+CD&transaction=soldout')
time.sleep(3)
html = d.page_source

# Check item-box__item-price content
for m in re.finditer(r'item-box__item-price[^>]*>([^<]+)', html):
    print(f"item-price: {repr(m.group(1))}")
    
# Check price-status__price content  
for m in re.finditer(r'price-status__price[^>]*>([^<]+)', html):
    print(f"status-price: {repr(m.group(1))}")

d.quit()
