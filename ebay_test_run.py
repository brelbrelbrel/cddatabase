# -*- coding: utf-8 -*-
"""Quick test run of eBay scraper - first 10 items only"""
import sqlite3
import urllib.request
import urllib.parse
import re
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def search_ebay_sold(query, category=176985):
    params = {
        '_nkw': query,
        'LH_Complete': '1',
        'LH_Sold': '1',
        '_sacat': str(category),
    }
    url = "https://www.ebay.com/sch/i.html?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
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

    seen = set()
    unique = []
    for p in prices:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique

def parse_ebay_price(price_str):
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

def extract_query(title):
    if not title:
        return None
    title = re.sub(r'\s*\([^)]*remaster[^)]*\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\([^)]*edition[^)]*\)', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\[[^\]]*\]', '', title)
    if len(title) > 80:
        title = title[:80]
    return title.strip()

# Main
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('''SELECT id, title, discogs_id FROM releases
             WHERE title IS NOT NULL AND title != ""
             GROUP BY discogs_id
             ORDER BY median_price DESC NULLS LAST
             LIMIT 10''')
releases = c.fetchall()

print(f"Testing eBay scraper on {len(releases)} releases...")
print("=" * 60)

found = 0
for i, (id_, title, discogs_id) in enumerate(releases, 1):
    query = extract_query(title)
    if not query:
        continue

    print(f"\n[{i}] {query[:50]}")
    prices = search_ebay_sold(query)
    time.sleep(2)

    if prices:
        avg = sum(prices) / len(prices)
        latest = prices[0]
        c.execute('''UPDATE releases SET ebay_sold_price=?, ebay_avg_price=?, ebay_sold_count=?
                     WHERE discogs_id=?''', (latest, round(avg, 2), len(prices), discogs_id))
        found += 1
        print(f"    -> {len(prices)} sales found: ${latest:.2f} (avg: ${avg:.2f})")
    else:
        print(f"    -> No sales found")

conn.commit()
conn.close()
print(f"\n{'='*60}")
print(f"Done! Found prices for {found}/{len(releases)} releases")
