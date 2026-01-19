# -*- coding: utf-8 -*-
"""
eBay Sold Items Price Scraper v2 (Selenium版)
"""
import sqlite3
import urllib.parse
import re
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"

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
        if 'Pardon' in driver.title or 'Interruption' in driver.title:
            print("  (blocked)")
            time.sleep(10)
            driver.get(url)
            time.sleep(3)
        html = driver.page_source
    except Exception as e:
        print(f"  Error: {e}")
        return []

    prices = []

    # Pattern 1: s-item__price class (most reliable)
    pattern1 = r's-item__price[^>]*>\s*\$?([\d,]+\.?\d*)'

    # Pattern 2: POSITIVE class (sold indicator)
    pattern2 = r'POSITIVE[^>]*>\s*\$?([\d,]+\.?\d*)'

    # Pattern 3: data-view with price
    pattern3 = r'"price":\s*"?\$?([\d,]+\.?\d*)"?'

    for pattern in [pattern1, pattern2, pattern3]:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for m in matches[:15]:
            try:
                val = float(m.replace(',', ''))
                if 1 < val < 5000:  # Valid CD price range
                    prices.append(val)
            except:
                pass
        if len(prices) >= 5:
            break

    # Remove duplicates
    seen = set()
    unique = []
    for p in prices:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique[:10]

def extract_search_query(title):
    if not title:
        return None
    title = re.sub(r'\s*\([^)]*remaster[^)]*\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\[[^\]]*\]', '', title)
    title = re.sub(r'[*=]', '', title)
    if ' - ' in title:
        parts = title.split(' - ', 1)
        artist = parts[0].strip()[:25]
        album = parts[1].strip()[:25]
        return f"{artist} {album} CD"
    return title[:50].strip() + ' CD'

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for col, coltype in [('ebay_sold_price', 'REAL'), ('ebay_avg_price', 'REAL'), ('ebay_sold_count', 'INTEGER')]:
        try:
            c.execute(f'ALTER TABLE releases ADD COLUMN {col} {coltype}')
            conn.commit()
        except:
            pass

    c.execute('''SELECT id, title, discogs_id FROM releases
                 WHERE title IS NOT NULL AND title != ""
                 AND (ebay_sold_price IS NULL OR ebay_sold_price = 0)
                 GROUP BY discogs_id
                 ORDER BY median_price DESC NULLS LAST
                 LIMIT 300''')
    releases = c.fetchall()

    print(f"Searching eBay for {len(releases)} releases...")
    print("=" * 60)

    driver = setup_driver()
    found = 0

    try:
        for i, (id_, title, discogs_id) in enumerate(releases, 1):
            query = extract_search_query(title)
            if not query:
                continue

            print(f"[{i}/{len(releases)}] {query[:40]}...")
            prices = search_ebay_sold(driver, query)
            time.sleep(1.5)

            if prices:
                avg_price = sum(prices) / len(prices)
                latest_price = prices[0]
                c.execute('''UPDATE releases SET ebay_sold_price=?, ebay_avg_price=?, ebay_sold_count=? WHERE discogs_id=?''',
                          (latest_price, round(avg_price, 2), len(prices), discogs_id))
                found += 1
                print(f"    ${latest_price:.2f} (avg ${avg_price:.2f}, {len(prices)} items)")
            else:
                print(f"    No sales")

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
