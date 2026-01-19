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
d.get('https://www.ebay.com/sch/i.html?_nkw=King+Crimson+CD&LH_Complete=1&LH_Sold=1&_sacat=176985')
time.sleep(3)
html = d.page_source

# Find s-card__price with surrounding context
for m in re.finditer(r's-card__price[^>]*>([^<]{1,50})<', html):
    print(f"Price content: {repr(m.group(1))}")
    if len([x for x in re.finditer(r's-card__price', html[:m.start()])]) > 10:
        break

d.quit()
