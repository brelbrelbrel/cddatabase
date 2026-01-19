# -*- coding: utf-8 -*-
"""Mercari Sold Items Price Scraper - Selenium版"""
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
JPY_TO_USD = 155

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=ja')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def search_mercari_sold(driver, query):
    url = f"https://jp.mercari.com/search?keyword={urllib.parse.quote(query)}&status=sold_out"
    
    try:
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
    except Exception as e:
        print(f"  Error: {e}")
        return []

    prices = []
    
    # Pattern 1: 円 prices (most common)
    for m in re.finditer(r'([\d,]+)\s*円', html):
        try:
            val = int(m.group(1).replace(',', ''))
            if 100 < val < 500000:  # Valid range
                prices.append(val)
        except:
            pass
    
    # Pattern 2: merPrice class content
    for m in re.finditer(r'merPrice[^>]*>([^<]+)', html):
        content = m.group(1).strip()
        num = re.search(r'([\d,]+)', content)
        if num:
            try:
                val = int(num.group(1).replace(',', ''))
                if 100 < val < 500000:
                    prices.append(val)
            except:
                pass

    # Remove duplicates, convert to USD
    seen = set()
    unique = []
    for p in prices:
        if p not in seen:
            seen.add(p)
            unique.append(round(p / JPY_TO_USD, 2))
    
    return unique[:15]

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

    for col, t in [('mercari_sold_price', 'REAL'), ('mercari_avg_price', 'REAL'), ('mercari_sold_count', 'INTEGER')]:
        try:
            c.execute(f'ALTER TABLE releases ADD COLUMN {col} {t}')
        except:
            pass

    c.execute('''SELECT id, title, discogs_id FROM releases
                 WHERE title IS NOT NULL AND title != ""
                 AND (mercari_sold_price IS NULL OR mercari_sold_price = 0)
                 GROUP BY discogs_id ORDER BY median_price DESC NULLS LAST LIMIT 300''')
    releases = c.fetchall()

    print(f"Searching Mercari for {len(releases)} releases...")
    driver = setup_driver()
    found = 0

    try:
        for i, (id_, title, discogs_id) in enumerate(releases, 1):
            query = extract_query(title)
            if not query:
                continue

            print(f"[{i}/{len(releases)}] {query[:40]}...")
            prices = search_mercari_sold(driver, query)
            time.sleep(1)

            if prices:
                avg = sum(prices) / len(prices)
                c.execute('UPDATE releases SET mercari_sold_price=?, mercari_avg_price=?, mercari_sold_count=? WHERE discogs_id=?',
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
