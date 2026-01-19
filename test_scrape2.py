# -*- coding: utf-8 -*-
import urllib.request
import re
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

url = 'https://www.discogs.com/release/12042802'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', errors='ignore')

# Find statistics section with prices
# Pattern: Low/Median/High prices

# Find last sold date
last_sold_match = re.search(r'Last Sold.*?dateTime="([^"]+)"', html)
if last_sold_match:
    print("Last Sold Date:", last_sold_match.group(1))

# Find price statistics - look for Low/Median/High pattern
stats_match = re.search(r'Low.*?</span><span[^>]*>([^<]+)</span>.*?Median.*?</span><span[^>]*>([^<]+)</span>.*?High.*?</span><span[^>]*>([^<]+)</span>', html, re.DOTALL)
if stats_match:
    print("Low:", stats_match.group(1))
    print("Median:", stats_match.group(2))
    print("High:", stats_match.group(3))

# Also check sell/history page for actual last sale price
history_url = 'https://www.discogs.com/sell/history/12042802'
req2 = urllib.request.Request(history_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    html2 = urllib.request.urlopen(req2, timeout=20).read().decode('utf-8', errors='ignore')
    # Find first sale entry
    sale_match = re.search(r'(\d{4}-\d{2}-\d{2}).*?(\$[\d,.]+|\u20ac[\d,.]+)', html2[:5000])
    if sale_match:
        print("Last sale from history:", sale_match.group(1), sale_match.group(2))
except Exception as e:
    print("History page error:", e)
