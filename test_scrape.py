# -*- coding: utf-8 -*-
import urllib.request
import re

url = 'https://www.discogs.com/release/12042802'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', errors='ignore')

print("Page length:", len(html))

# Look for statistics section
if 'Last Sold' in html:
    print("'Last Sold' text found in page")
    # Find context around it
    idx = html.find('Last Sold')
    print("Context:", repr(html[idx:idx+200]))
else:
    print("'Last Sold' NOT found")

if 'Median' in html:
    print("'Median' text found")
    idx = html.find('Median')
    print("Context:", repr(html[idx:idx+200]))
