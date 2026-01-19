# -*- coding: utf-8 -*-
"""
Yahoo Auctions Japan Price Scraper
※ヤフオク落札相場をスクレイピング
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

# SSL context (disable verification for Yahoo Japan)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def search_yahoo_sold(query):
    """
    Search Yahoo Auctions completed listings
    Returns list of prices in JPY
    """
    params = {
        'p': query,
        'va': query,
        'istatus': '2',  # Ended auctions only
        'exflg': '1',
        'b': '1',
        'n': '50',
    }
    url = "https://auctions.yahoo.co.jp/search/search?" + urllib.parse.urlencode(params)

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

    # Extract prices in yen
    price_matches = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*円', html)

    prices = []
    seen = set()
    for p in price_matches:
        val = int(p.replace(',', ''))
        if val >= 100 and val not in seen:  # Filter tiny amounts
            seen.add(val)
            prices.append(val)

    return prices[:20]  # Return top 20 unique prices

def extract_search_query(title):
    """Extract search query from Discogs title for Yahoo"""
    if not title:
        return None
    # Remove special characters
    title = re.sub(r'[*=\[\]()]', '', title)
    # Remove common suffixes
    title = re.sub(r'\s*-\s*remaster.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*deluxe.*$', '', title, flags=re.IGNORECASE)
    # Split artist - album and use both
    if ' - ' in title:
        parts = title.split(' - ', 1)
        # Use artist + first part of album
        artist = parts[0].strip()[:30]
        album = parts[1].strip()[:30]
        return f"{artist} {album} CD"
    return title[:50].strip() + " CD"

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Add Yahoo columns if not exist
    for col, coltype in [
        ('yahoo_sold_price', 'REAL'),  # Stored in USD
        ('yahoo_avg_price', 'REAL'),   # Stored in USD
        ('yahoo_sold_count', 'INTEGER'),
    ]:
        try:
            c.execute(f'ALTER TABLE releases ADD COLUMN {col} {coltype}')
            conn.commit()
            print(f"Added column: {col}")
        except:
            pass

    # Get releases to search
    c.execute('''SELECT id, title, discogs_id FROM releases
                 WHERE title IS NOT NULL AND title != ""
                 AND (yahoo_sold_price IS NULL OR yahoo_sold_price = 0)
                 GROUP BY discogs_id
                 ORDER BY median_price DESC NULLS LAST
                 LIMIT 300''')
    releases = c.fetchall()

    print(f"Searching Yahoo Auctions for {len(releases)} releases...")
    print("=" * 60)

    found = 0
    for i, (id_, title, discogs_id) in enumerate(releases, 1):
        query = extract_search_query(title)
        if not query:
            continue

        print(f"[{i}/{len(releases)}] {query[:45]}...")
        prices_jpy = search_yahoo_sold(query)
        time.sleep(1)  # Rate limit

        if prices_jpy:
            # Convert to USD (rate: 155 JPY = 1 USD)
            prices_usd = [round(p / 155, 2) for p in prices_jpy]
            avg_price = sum(prices_usd) / len(prices_usd)
            latest_price = prices_usd[0]

            c.execute('''UPDATE releases SET
                         yahoo_sold_price=?, yahoo_avg_price=?, yahoo_sold_count=?
                         WHERE discogs_id=?''',
                      (latest_price, round(avg_price, 2), len(prices_usd), discogs_id))
            found += 1
            print(f"    ¥{prices_jpy[0]:,} (${latest_price:.2f}) - {len(prices_jpy)} sales")
        else:
            print(f"    No sales found")

        if i % 30 == 0:
            conn.commit()
            print(f"  === Saved {found} records ===")

    conn.commit()
    conn.close()
    print()
    print("=" * 60)
    print(f"Done! Found Yahoo prices for {found}/{len(releases)} releases")

if __name__ == "__main__":
    main()
