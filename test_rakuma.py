# -*- coding: utf-8 -*-
"""Test Rakuma (Rakuten) scraping"""
import urllib.request
import urllib.parse
import ssl
import re
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

query = "King Crimson CD"
# Rakuma sold items
url = f"https://fril.jp/s?query={urllib.parse.quote(query)}&transaction=soldout"
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
    title = re.search(r'<title>([^<]+)</title>', html)
    if title:
        print(f"Title: {title.group(1)[:80]}")

    # Look for prices
    prices = re.findall(r'[¥￥][\s]*([\d,]+)', html)
    print(f"\nYen prices: {len(prices)}")
    for p in list(set(prices))[:10]:
        val = int(p.replace(',', ''))
        print(f"  ¥{val:,} (${val/155:.2f})")

except Exception as e:
    print(f"Error: {e}")
