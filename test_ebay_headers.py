# -*- coding: utf-8 -*-
import urllib.request
import re
import sys
import io
import gzip
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

url = 'https://www.ebay.com/sch/i.html?_nkw=King+Crimson+CD&LH_Sold=1'

# Full browser headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

req = urllib.request.Request(url, headers=headers)

try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = resp.read()

    # Handle gzip
    if resp.info().get('Content-Encoding') == 'gzip':
        data = gzip.decompress(data)

    html = data.decode('utf-8', errors='ignore')
    print("Response size:", len(html))

    # Get title
    title = re.search(r'<title>([^<]+)</title>', html)
    if title:
        print("Title:", title.group(1)[:100])

    # Check for blocks
    if 'Pardon Our Interruption' in html:
        print("BLOCKED: Anti-bot page")
    elif 'captcha' in html.lower():
        print("BLOCKED: CAPTCHA")
    else:
        # Find prices
        prices = re.findall(r'price">([^<]+)<', html)
        print("Prices found:", len(prices))
        for p in prices[:5]:
            print("  ", p)

except Exception as e:
    print("Error:", e)
