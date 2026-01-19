# -*- coding: utf-8 -*-
"""
eBay Sold Items Price Scraper (Selenium版)
※落札済み商品の価格をスクレイピング
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
    """Setup Chrome driver with anti-detection"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def search_ebay_sold(driver, query, category=176985):
    """
    Search eBay sold listings
    category 176985 = Music > CDs
    Returns list of prices in USD
    """
    params = {
        '_nkw': query,
        'LH_Complete': '1',
        'LH_Sold': '1',
        '_sacat': str(category),
    }
    url = "https://www.ebay.com/sch/i.html?" + urllib.parse.urlencode(params)

    try:
        driver.get(url)
        time.sleep(2)  # Wait for page load

        # Check for block
        if 'Pardon' in driver.title or 'Interruption' in driver.title:
            print("  (blocked, waiting...)")
            time.sleep(10)
            driver.get(url)
            time.sleep(3)

        html = driver.page_source
    except Exception as e:
        print(f"  Error: {e}")
        return []

    prices = []
    price_pattern = r'price">([^<]+)<'
    matches = re.findall(price_pattern, html)

    for match in matches[:20]:
        price = parse_ebay_price(match)
        if price and price > 0:
            prices.append(price)

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for p in prices:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique

def parse_ebay_price(price_str):
    """Parse eBay price string to USD float"""
    if not price_str:
        return None
    price_str = price_str.strip()
    if ' to ' in price_str.lower():
        price_str = price_str.split(' to ')[0].strip()
    match = re.search(r'[\d,.]+', price_str)
    if not match:
        return None
    num_str = match.group().replace(',', '')
    try:
        value = float(num_str)
    except:
        return None

    # Currency conversion (2025 rates)
    price_upper = price_str.upper()
    if 'JPY' in price_upper or '¥' in price_str or '円' in price_str:
        return round(value / 155, 2)
    elif 'EUR' in price_upper or '€' in price_str:
        return round(value * 1.05, 2)
    elif 'GBP' in price_upper or '£' in price_str:
        return round(value * 1.25, 2)
    elif '$' in price_str:
        return round(value, 2)
    return None

def extract_search_query(title):
    """Extract search query from Discogs title"""
    if not title:
        return None
    # Remove common suffixes
    title = re.sub(r'\s*\([^)]*remaster[^)]*\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\([^)]*edition[^)]*\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\([^)]*deluxe[^)]*\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\[[^\]]*\]', '', title)
    # Remove special characters that break search
    title = re.sub(r'[*=]', '', title)
    if len(title) > 60:
        title = title[:60]
    return title.strip() + ' CD'

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Add eBay columns if not exist
    for col, coltype in [
        ('ebay_sold_price', 'REAL'),
        ('ebay_avg_price', 'REAL'),
        ('ebay_sold_count', 'INTEGER'),
    ]:
        try:
            c.execute(f'ALTER TABLE releases ADD COLUMN {col} {coltype}')
            conn.commit()
        except:
            pass

    # Get releases to search - prioritize by Discogs median price
    c.execute('''SELECT id, title, discogs_id FROM releases
                 WHERE title IS NOT NULL AND title != ""
                 AND (ebay_sold_price IS NULL OR ebay_sold_price = 0)
                 GROUP BY discogs_id
                 ORDER BY median_price DESC NULLS LAST
                 LIMIT 300''')
    releases = c.fetchall()

    print(f"Searching eBay for {len(releases)} releases (Selenium)...")
    print("=" * 60)

    print("Starting Chrome driver...")
    driver = setup_driver()

    found = 0
    try:
        for i, (id_, title, discogs_id) in enumerate(releases, 1):
            query = extract_search_query(title)
            if not query:
                continue

            print(f"[{i}/{len(releases)}] {query[:45]}...")
            prices = search_ebay_sold(driver, query)
            time.sleep(1.5)  # Rate limit

            if prices:
                avg_price = sum(prices) / len(prices)
                latest_price = prices[0]
                c.execute('''UPDATE releases SET
                             ebay_sold_price=?, ebay_avg_price=?, ebay_sold_count=?
                             WHERE discogs_id=?''',
                          (latest_price, round(avg_price, 2), len(prices), discogs_id))
                found += 1
                print(f"    ${latest_price:.2f} (avg: ${avg_price:.2f}, {len(prices)} sales)")
            else:
                print(f"    No sales found")

            if i % 20 == 0:
                conn.commit()
                print(f"  === Saved {found} records ===")

    finally:
        driver.quit()
        print("Chrome driver closed")

    conn.commit()
    conn.close()
    print()
    print("=" * 60)
    print(f"Done! Found eBay prices for {found}/{len(releases)} releases")

if __name__ == "__main__":
    main()
