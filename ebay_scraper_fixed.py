# -*- coding: utf-8 -*-
"""eBay Sold Items Price Scraper - Fixed for JPY"""
import sqlite3
import urllib.parse
import re
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
JPY_TO_USD = 155  # Conversion rate

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def search_ebay_sold(driver, query, category=176985):
    params = {
        '_nkw': query,
        'LH_Complete': '1',
        'LH_Sold': '1', 
        '_sacat': str(category),
    }
    url = "https://www.ebay.com/sch/i.html?" + urllib.parse.urlencode(params)

    try:
        driver.get(url)
        time.sleep(2)
        if 'Pardon' in driver.title:
            time.sleep(10)
            driver.get(url)
            time.sleep(3)
        html = driver.page_source
    except Exception as e:
        print(f"  Error: {e}")
        return []

    prices = []
    
    # Find s-card__price content
    for m in re.finditer(r's-card__price[^>]*>([^<]+)<', html):
        content = m.group(1).strip()
        
        # Skip $20.00 shipping price
        if content == '$20.00':
            continue
            
        # Parse JPY (円)
        if '円' in content or '¥' in content:
            num = re.search(r'([\d,]+)', content)
            if num:
                try:
                    jpy = float(num.group(1).replace(',', ''))
                    if 100 < jpy < 500000:  # Valid range
                        usd = round(jpy / JPY_TO_USD, 2)
                        prices.append(usd)
                except:
                    pass
        # Parse USD ($)
        elif '$' in content:
            num = re.search(r'\$([\d,.]+)', content)
            if num:
                try:
                    usd = float(num.group(1).replace(',', ''))
                    if 0.5 < usd < 2000:
                        prices.append(usd)
                except:
                    pass

    # Remove duplicates
    seen = set()
    unique = []
    for p in prices:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    
    return unique[:10]

def extract_query(title):
    if not title:
        return None
    title = re.sub(r'\s*\([^)]*\)', '', title)
    title = re.sub(r'\s*\[[^\]]*\]', '', title)
    title = re.sub(r'[*=]', '', title)
    if ' - ' in title:
        parts = title.split(' - ', 1)
        return f"{parts[0][:25]} {parts[1][:25]} CD"
    return title[:50] + ' CD'

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for col, t in [('ebay_sold_price', 'REAL'), ('ebay_avg_price', 'REAL'), ('ebay_sold_count', 'INTEGER')]:
        try:
            c.execute(f'ALTER TABLE releases ADD COLUMN {col} {t}')
        except:
            pass

    c.execute('''SELECT id, title, discogs_id FROM releases
                 WHERE title IS NOT NULL AND title != ""
                 AND (ebay_sold_price IS NULL OR ebay_sold_price = 0)
                 GROUP BY discogs_id ORDER BY median_price DESC NULLS LAST LIMIT 300''')
    releases = c.fetchall()

    print(f"Searching eBay for {len(releases)} releases...")
    driver = setup_driver()
    found = 0

    try:
        for i, (id_, title, discogs_id) in enumerate(releases, 1):
            query = extract_query(title)
            if not query:
                continue

            print(f"[{i}/{len(releases)}] {query[:40]}...")
            prices = search_ebay_sold(driver, query)
            time.sleep(1.5)

            if prices:
                avg = sum(prices) / len(prices)
                c.execute('UPDATE releases SET ebay_sold_price=?, ebay_avg_price=?, ebay_sold_count=? WHERE discogs_id=?',
                          (prices[0], round(avg, 2), len(prices), discogs_id))
                found += 1
                print(f"    ${prices[0]:.2f} (avg ${avg:.2f}, {len(prices)} items)")
            else:
                print("    No sales")

            if i % 20 == 0:
                conn.commit()
                print(f"  === Saved {found} ===")
    finally:
        driver.quit()

    conn.commit()
    conn.close()
    print(f"\nDone! Found {found}/{len(releases)}")

if __name__ == "__main__":
    main()
