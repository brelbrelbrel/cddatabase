# -*- coding: utf-8 -*-
import urllib.request
import re
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

url = 'https://www.ebay.com/sch/i.html?_nkw=King+Crimson+CD&LH_Sold=1&_sacat=176985'
print("URL:", url)

req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
})

try:
    resp = urllib.request.urlopen(req, timeout=30)
    html = resp.read().decode('utf-8', errors='ignore')
    print("Response size:", len(html))

    # Check for blocks
    if 'captcha' in html.lower():
        print("CAPTCHA detected!")
    if 'robot' in html.lower():
        print("Robot check!")

    # Get title
    title = re.search(r'<title>([^<]+)</title>', html)
    if title:
        print("Title:", title.group(1)[:100])

    # Find prices
    prices = re.findall(r'price">([^<]+)<', html)
    print("Prices found:", len(prices))
    for p in prices[:5]:
        print("  ", p)

except Exception as e:
    print("Error:", e)
