# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect(r"C:\Users\kawamura\Desktop\music_database.db")
c = conn.cursor()

# Get existing columns
existing = [x[1] for x in c.execute('PRAGMA table_info(releases)').fetchall()]
print("Existing columns:", len(existing))

# Add new columns
for col, coltype in [('ebay_sold_price', 'REAL'), ('ebay_avg_price', 'REAL'), ('ebay_sold_count', 'INTEGER')]:
    if col not in existing:
        c.execute(f'ALTER TABLE releases ADD COLUMN {col} {coltype}')
        print(f'Added: {col}')
    else:
        print(f'{col}: already exists')

conn.commit()
conn.close()
print("Done!")
