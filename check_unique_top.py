# -*- coding: utf-8 -*-
import sqlite3
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
c = sqlite3.connect(DB_PATH)

# Stats
total = c.execute("SELECT COUNT(*) FROM releases WHERE discogs_url IS NOT NULL").fetchone()[0]
with_price = c.execute("SELECT COUNT(*) FROM releases WHERE median_price > 0").fetchone()[0]
no_price = c.execute("SELECT COUNT(*) FROM releases WHERE discogs_url IS NOT NULL AND (median_price IS NULL OR median_price = 0)").fetchone()[0]
print(f"Progress: {with_price}/{total} ({100*with_price//total}%)")
print(f"価格データなし: {no_price}件")
print()

# Unique top releases by discogs_id
print("=== TOP 30 高価値アルバム (ユニーク/中央値USD) ===")
print()
rows = c.execute('''
    SELECT title, median_price, high_price, community_want, last_sold_date, discogs_id
    FROM releases
    WHERE median_price > 0
    GROUP BY discogs_id
    ORDER BY median_price DESC
    LIMIT 30
''').fetchall()

for i, r in enumerate(rows, 1):
    title = (r[0] or 'Unknown')[:50]
    med = r[1] or 0
    high = r[2] or 0
    want = r[3] or 0
    date = (r[4] or '')[:10]
    print(f"{i:2}. ${med:>6.2f} (Max:${high:>6.2f}) Want:{want:>3}  {title}")

# Check what's missing prices
print()
print("=== 価格データなしの例 (取引なし?) ===")
missing = c.execute('''
    SELECT title, discogs_url FROM releases
    WHERE discogs_url IS NOT NULL
    AND (median_price IS NULL OR median_price = 0)
    LIMIT 5
''').fetchall()
for r in missing:
    print(f"  - {(r[0] or 'Unknown')[:40]}")

c.close()
