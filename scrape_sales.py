# -*- coding: utf-8 -*-
"""
Scrape sale statistics from Discogs release pages
※直近販売履歴をスクレイピング - Working version
"""
import sqlite3
import urllib.request
import re
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def parse_price(price_str):
    """Convert price string to float (USD equivalent)"""
    if not price_str:
        return None
    # Remove currency symbols and convert
    price_str = price_str.strip()
    # Extract number
    match = re.search(r'[\d,.]+', price_str)
    if not match:
        return None
    num_str = match.group().replace(',', '')
    try:
        value = float(num_str)
    except:
        return None

    # Rough currency conversion to USD
    if '¥' in price_str or '円' in price_str:
        return round(value / 150, 2)  # JPY to USD
    elif '€' in price_str:
        return round(value * 1.08, 2)  # EUR to USD
    elif '£' in price_str:
        return round(value * 1.27, 2)  # GBP to USD
    else:  # Assume USD
        return value

def fetch_and_parse(url):
    """Fetch page and extract sale statistics"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

    result = {}

    # Last sold date
    date_match = re.search(r'Last Sold.*?dateTime="([^"]+)"', html)
    if date_match:
        result['last_sold_date'] = date_match.group(1)

    # Price statistics (Low/Median/High)
    stats_match = re.search(
        r'Low.*?</span><span[^>]*>([^<]+)</span>.*?'
        r'Median.*?</span><span[^>]*>([^<]+)</span>.*?'
        r'High.*?</span><span[^>]*>([^<]+)</span>',
        html, re.DOTALL
    )
    if stats_match:
        result['low_price'] = parse_price(stats_match.group(1))
        result['median_price'] = parse_price(stats_match.group(2))
        result['high_price'] = parse_price(stats_match.group(3))

    return result if result else None

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Add columns if not exist
    for col in ['last_sold_date', 'median_price', 'high_price']:
        try:
            c.execute(f'ALTER TABLE releases ADD COLUMN {col} TEXT' if 'date' in col else f'ALTER TABLE releases ADD COLUMN {col} REAL')
            conn.commit()
        except:
            pass

    # Get releases with discogs_url, prioritize by want count
    c.execute('''SELECT id, discogs_url, title FROM releases
                 WHERE discogs_url IS NOT NULL AND discogs_url != ""
                 AND (median_price IS NULL OR median_price = 0)
                 ORDER BY community_want DESC NULLS LAST''')
    releases = c.fetchall()

    print(f"Scraping {len(releases)} releases for sale statistics...")
    print("(Prices converted to USD)")
    print()

    updated = 0
    for i, (id_, url, title) in enumerate(releases, 1):
        print(f"[{i}/{len(releases)}] {(title or 'Unknown')[:45]}...")

        stats = fetch_and_parse(url)
        time.sleep(1.5)  # Rate limit

        if stats and stats.get('median_price'):
            c.execute('''UPDATE releases SET
                         median_price=?, high_price=?, last_sold_date=?
                         WHERE id=?''',
                      (stats.get('median_price'), stats.get('high_price'),
                       stats.get('last_sold_date'), id_))
            updated += 1
            print(f"  Median: ${stats.get('median_price')} | Last: {stats.get('last_sold_date', '?')}")
        else:
            print(f"  No sale data")

        if i % 30 == 0:
            conn.commit()
            print(f"  === Saved {updated} records ===")

    conn.commit()
    conn.close()
    print(f"\n{'='*50}")
    print(f"Done! Updated {updated}/{len(releases)} with sale statistics")
    print("TODO: 直近販売金額の個別取得は今後実装予定")

if __name__ == "__main__":
    main()
