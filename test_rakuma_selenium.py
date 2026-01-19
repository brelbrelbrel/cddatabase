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

# Rakuma (fril.jp) sold items
d.get('https://fril.jp/s?query=King+Crimson+CD&transaction=soldout')
time.sleep(3)
html = d.page_source
print(f"HTML size: {len(html)}")

# Find price classes
classes = set(re.findall(r'class="([^"]*price[^"]*)"', html, re.I))
print("Price classes:", list(classes)[:10])

# Find yen prices
yen = re.findall(r'[¥￥][\s]*([\d,]+)', html)
print(f"Yen prices: {yen[:15]}")

# Find 円
en = re.findall(r'([\d,]+)\s*円', html)
print(f"円 prices: {en[:15]}")

d.quit()
