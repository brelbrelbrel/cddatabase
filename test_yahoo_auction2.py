# -*- coding: utf-8 -*-
"""Test Yahoo Auctions Japan scraping with SSL fix"""
import urllib.request
import urllib.parse
import ssl
import re
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Disable SSL verification (for testing)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

query = "King Crimson CD"
params = {
    'p': query,
    'va': query,
    'istatus': '2',  # Ended auctions
    'exflg': '1',
    'b': '1',
    'n': '50',
}

url = "https://auctions.yahoo.co.jp/search/search?" + urllib.parse.urlencode(params)
print(f"URL: {url}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ja-JP,ja;q=0.9',
}

try:
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=30, context=ssl_context)
    html = resp.read().decode('utf-8', errors='ignore')
    print(f"Response size: {len(html)}")

    # Check title
    title_match = re.search(r'<title>([^<]+)</title>', html)
    if title_match:
        print(f"Title: {title_match.group(1)[:80]}")

    # Count auction items
    item_count = html.count('Product__title')
    print(f"Items found (Product__title): {item_count}")

    # Look for prices
    price_matches = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*円', html)
    print(f"\nYen prices found: {len(price_matches)}")
    # Show unique prices
    unique_prices = []
    for p in price_matches:
        val = int(p.replace(',', ''))
        if val not in unique_prices and val > 100:  # Filter tiny amounts
            unique_prices.append(val)
    for p in unique_prices[:15]:
        print(f"  {p:,}円 (${p/155:.2f})")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
