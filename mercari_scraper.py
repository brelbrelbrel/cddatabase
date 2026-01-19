# -*- coding: utf-8 -*-
"""
Mercari Price Scraper
※メルカリ売り切れ商品の価格をスクレイピング
"""
import sqlite3
import urllib.request
import urllib.parse
import ssl
import re
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def search_mercari_sold(query):
    """Search Mercari sold items"""
    url = f"https://jp.mercari.com/search?keyword={urllib.parse.quote(query)}&status=sold_out"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ja-JP,ja;q=0.9',
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=30, context=ssl_context)
        html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  Error: {e}")
        return []

    # Extract prices
    prices = []
    matches = re.findall(r'[¥￥]\s*([\d,]+)', html)
    seen = set()
    for m in matches:
        val = int(m.replace(',', ''))
        if val >= 100 and val <= 500000 and val not in seen:
            seen.add(val)
            prices.append(val)

    return prices[:15]

def extract_search_query(title):
    """Extract search query from Discogs title"""
    if not title:
        return None
    title = re.sub(r'[*=\[\]()]', '', title)
    title = re.sub(r'\s*-\s*remaster.*$', '', title, flags=re.IGNORECASE)
    if ' - ' in title:
        parts = title.split(' - ', 1)
        artist = parts[0].strip()[:25]
        album = parts[1].strip()[:25]
        return f"{artist} {album} CD"
    return title[:40].strip() + " CD"

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Add Mercari columns
    for col, coltype in [
        ('mercari_sold_price', 'REAL'),
        ('mercari_avg_price', 'REAL'),
        ('mercari_sold_count', 'INTEGER'),
    ]:
        try:
            c.execute(f'ALTER TABLE releases ADD COLUMN {col} {coltype}')
            conn.commit()
            print(f"Added: {col}")
        except:
            pass

    # Get releases
    c.execute('''SELECT id, title, discogs_id FROM releases
                 WHERE title IS NOT NULL AND title != ""
                 AND (mercari_sold_price IS NULL OR mercari_sold_price = 0)
                 GROUP BY discogs_id
                 ORDER BY median_price DESC NULLS LAST
                 LIMIT 300''')
    releases = c.fetchall()

    print(f"Searching Mercari for {len(releases)} releases...")
    print("=" * 60)

    found = 0
    for i, (id_, title, discogs_id) in enumerate(releases, 1):
        query = extract_search_query(title)
        if not query:
            continue

        print(f"[{i}/{len(releases)}] {query[:40]}...")
        prices_jpy = search_mercari_sold(query)
        time.sleep(1)

        if prices_jpy:
            prices_usd = [round(p / 155, 2) for p in prices_jpy]
            avg_price = sum(prices_usd) / len(prices_usd)
            latest_price = prices_usd[0]

            c.execute('''UPDATE releases SET
                         mercari_sold_price=?, mercari_avg_price=?, mercari_sold_count=?
                         WHERE discogs_id=?''',
                      (latest_price, round(avg_price, 2), len(prices_usd), discogs_id))
            found += 1
            print(f"    ¥{prices_jpy[0]:,} (${latest_price:.2f}) - {len(prices_jpy)} items")
        else:
            print(f"    No items found")

        if i % 30 == 0:
            conn.commit()
            print(f"  === Saved {found} records ===")

    conn.commit()
    conn.close()
    print()
    print("=" * 60)
    print(f"Done! Found Mercari prices for {found}/{len(releases)} releases")

if __name__ == "__main__":
    main()
