# -*- coding: utf-8 -*-
"""
Add sold price statistics from Discogs API
"""
import sqlite3
import urllib.request
import json
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
DISCOGS_TOKEN = "WQDfPrbhGrmXKlPIFVRqmHKLDCdLNCobTYHTviKI"
USER_AGENT = "MusicDBCreator/1.0"

def get_price_stats(release_id):
    """Get price statistics including median sold price"""
    try:
        url = f"https://api.discogs.com/marketplace/stats/{release_id}"
        req = urllib.request.Request(url, headers={
            'User-Agent': USER_AGENT,
            'Authorization': f'Discogs token={DISCOGS_TOKEN}'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        return {
            'lowest_price': data.get('lowest_price', {}).get('value'),
            'median_price': data.get('median_price', {}).get('value'),
            'highest_price': data.get('highest_price', {}).get('value'),
        }
    except Exception as e:
        return None

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Add new columns if not exist
    try:
        c.execute('ALTER TABLE releases ADD COLUMN median_price REAL')
        c.execute('ALTER TABLE releases ADD COLUMN highest_price REAL')
        conn.commit()
        print("Added new price columns")
    except:
        print("Price columns already exist")

    # Get releases with discogs_id
    c.execute('SELECT id, discogs_id, title FROM releases WHERE discogs_id IS NOT NULL')
    releases = c.fetchall()

    print(f"Fetching price stats for {len(releases)} releases...")

    updated = 0
    for i, (id_, discogs_id, title) in enumerate(releases, 1):
        stats = get_price_stats(discogs_id)
        time.sleep(1.1)  # Rate limit

        if stats and stats.get('median_price'):
            c.execute('''UPDATE releases SET
                lowest_price=?, median_price=?, highest_price=?
                WHERE id=?''',
                (stats.get('lowest_price'), stats.get('median_price'),
                 stats.get('highest_price'), id_))
            updated += 1
            print(f"[{i}/{len(releases)}] {title[:40]}: median=${stats.get('median_price')}")
        else:
            print(f"[{i}/{len(releases)}] {title[:40]}: no sales data")

        if i % 50 == 0:
            conn.commit()
            print(f"  [Saved]")

    conn.commit()
    conn.close()
    print(f"\nDone! Updated {updated} releases with median prices")

if __name__ == "__main__":
    main()
