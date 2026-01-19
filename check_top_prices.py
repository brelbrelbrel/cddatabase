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
print(f"Progress: {with_price}/{total} ({100*with_price//total}%)")
print()

# Top 25
print("=== TOP 25 高価値アルバム (中央値/USD) ===")
print()
rows = c.execute('''
    SELECT title, median_price, high_price, community_want, last_sold_date
    FROM releases
    WHERE median_price > 0
    ORDER BY median_price DESC
    LIMIT 25
''').fetchall()

for i, r in enumerate(rows, 1):
    title = (r[0] or 'Unknown')[:48]
    med = r[1] or 0
    high = r[2] or 0
    want = r[3] or 0
    date = (r[4] or '')[:10]
    print(f"{i:2}. ${med:>6.2f} (Max:${high:>6.2f}) Want:{want:>3}  {title}")

print()
print("=== 統計 ===")
avg = c.execute("SELECT AVG(median_price) FROM releases WHERE median_price > 0").fetchone()[0]
max_p = c.execute("SELECT MAX(median_price) FROM releases WHERE median_price > 0").fetchone()[0]
print(f"平均中央値: ${avg:.2f}")
print(f"最高中央値: ${max_p:.2f}")
c.close()
