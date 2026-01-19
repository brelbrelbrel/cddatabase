# -*- coding: utf-8 -*-
import sqlite3

c = sqlite3.connect(r'C:\Users\kawamura\Desktop\music_database.db')
c.row_factory = sqlite3.Row

print("=== eBay TOP 10 ===")
rows = c.execute('''SELECT title, catalog_number, median_price, ebay_sold_price, yahoo_sold_price, ebay_match_score
                    FROM releases WHERE ebay_sold_price > 0
                    ORDER BY ebay_sold_price DESC LIMIT 10''').fetchall()
for r in rows:
    title = (str(r['title'])[:35] if r['title'] else '')
    cat = r['catalog_number'] or ''
    print(f"${r['ebay_sold_price']:.2f} | {title:35} | {cat} | D:${r['median_price'] or 0:.2f} | score:{r['ebay_match_score']:.0f}")

print("\n=== Yahoo TOP 10 ===")
rows = c.execute('''SELECT title, catalog_number, yahoo_sold_price, yahoo_match_score
                    FROM releases WHERE yahoo_sold_price > 0
                    ORDER BY yahoo_sold_price DESC LIMIT 10''').fetchall()
for r in rows:
    title = (str(r['title'])[:35] if r['title'] else '')
    print(f"${r['yahoo_sold_price']:.2f} | {title:35} | score:{r['yahoo_match_score']:.0f}")

print("\n=== Summary ===")
cur = c.cursor()
total = cur.execute('SELECT COUNT(*) FROM releases').fetchone()[0]
discogs = cur.execute('SELECT COUNT(*) FROM releases WHERE median_price > 0').fetchone()[0]
ebay = cur.execute('SELECT COUNT(*) FROM releases WHERE ebay_sold_price > 0').fetchone()[0]
ebay_hi = cur.execute('SELECT COUNT(*) FROM releases WHERE ebay_match_score >= 80').fetchone()[0]
yahoo = cur.execute('SELECT COUNT(*) FROM releases WHERE yahoo_sold_price > 0').fetchone()[0]
total_discogs = cur.execute('SELECT SUM(median_price) FROM releases WHERE median_price > 0').fetchone()[0] or 0
total_ebay = cur.execute('SELECT SUM(ebay_sold_price) FROM releases WHERE ebay_sold_price > 0').fetchone()[0] or 0

print(f"Total releases: {total}")
print(f"Discogs prices: {discogs} (total ${total_discogs:.2f})")
print(f"eBay prices: {ebay} ({ebay_hi} high conf) (total ${total_ebay:.2f})")
print(f"Yahoo prices: {yahoo}")
