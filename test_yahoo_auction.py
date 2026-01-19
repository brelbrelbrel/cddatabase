# -*- coding: utf-8 -*-
"""Test Yahoo Auctions Japan scraping"""
import urllib.request
import urllib.parse
import re
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Yahoo Auctions completed listings search
# istatus=2 means ended auctions
query = "King Crimson CD"
params = {
    'p': query,
    'va': query,
    'istatus': '2',  # Ended auctions
    'is_postage_mode': '1',
    'dest_pref_code': '13',  # Tokyo
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
    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode('utf-8', errors='ignore')
    print(f"Response size: {len(html)}")

    # Check title
    title_match = re.search(r'<title>([^<]+)</title>', html)
    if title_match:
        print(f"Title: {title_match.group(1)[:80]}")

    # Look for prices - Yahoo Auctions uses 円 for prices
    # Pattern: 落札価格 or 即決価格
    price_patterns = [
        (r'(\d{1,3}(?:,\d{3})*)\s*円', 'Yen amounts'),
        (r'落札[^0-9]*(\d{1,3}(?:,\d{3})*)', 'Winning bid'),
        (r'Price["\']?\s*:\s*(\d+)', 'JSON price'),
    ]

    for pattern, name in price_patterns:
        matches = re.findall(pattern, html)
        if matches:
            print(f"\n{name}: {len(matches)} matches")
            for m in matches[:10]:
                print(f"  {m}円")
            break

except Exception as e:
    print(f"Error: {e}")
