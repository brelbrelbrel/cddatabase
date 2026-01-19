# -*- coding: utf-8 -*-
"""
Fix mismatched Discogs entries - clear bad matches and re-search with artist validation
"""
import sqlite3
import urllib.request
import urllib.parse
import json
import time
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
IMAGES_DIR = r"C:\Users\kawamura\Desktop\music_images"
DISCOGS_TOKEN = "WQDfPrbhGrmXKlPIFVRqmHKLDCdLNCobTYHTviKI"
USER_AGENT = "MusicDBCreator/1.0"

def do_search(params):
    try:
        params['per_page'] = 5
        url = f"https://api.discogs.com/database/search?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={
            'User-Agent': USER_AGENT,
            'Authorization': f'Discogs token={DISCOGS_TOKEN}'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8')).get('results', [])
    except Exception as e:
        print(f"  API Error: {e}")
        return []

def artist_match(filename_artist, discogs_title):
    """Check if artist from filename appears in Discogs title"""
    if not filename_artist:
        return False
    # Discogs title format: "Artist - Album"
    fa = filename_artist.lower().split()[0]  # First word of artist
    dt = discogs_title.lower()
    return fa in dt

def search_with_validation(artist, album):
    """Search Discogs and validate artist matches"""
    if not artist:
        return None

    # Strategy 1: Artist + Album
    if album:
        print(f"  [1] artist+album: {artist[:20]} / {album[:25]}")
        results = do_search({'artist': artist, 'release_title': album})
        for r in results:
            if artist_match(artist, r.get('title', '')):
                return r
        time.sleep(1)

    # Strategy 2: General query
    if album:
        query = f"{artist} {album}"[:50]
        print(f"  [2] query: {query}")
        results = do_search({'q': query, 'type': 'release'})
        for r in results:
            if artist_match(artist, r.get('title', '')):
                return r
        time.sleep(1)

    # Strategy 3: Artist only
    print(f"  [3] artist only: {artist[:30]}")
    results = do_search({'artist': artist, 'type': 'release'})
    for r in results:
        if artist_match(artist, r.get('title', '')):
            return r

    return None

def get_price_info(release_id):
    try:
        url = f"https://api.discogs.com/releases/{release_id}"
        req = urllib.request.Request(url, headers={
            'User-Agent': USER_AGENT,
            'Authorization': f'Discogs token={DISCOGS_TOKEN}'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return {
            'lowest_price': data.get('lowest_price'),
            'num_for_sale': data.get('num_for_sale', 0),
            'tracklist': json.dumps([t.get('title', '') for t in data.get('tracklist', [])])
        }
    except:
        return {}

def download_image(url, discogs_id):
    if not url or not discogs_id:
        return None
    Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)
    ext = '.png' if '.png' in url.lower() else '.jpg'
    local_path = Path(IMAGES_DIR) / f"{discogs_id}{ext}"
    if local_path.exists():
        return str(local_path)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(local_path, 'wb') as f:
                f.write(resp.read())
        return str(local_path)
    except:
        return None

def parse_filename(filename):
    name = re.sub(r'\.flac$', '', filename, flags=re.IGNORECASE)
    catalog = None
    cat_match = re.search(r'\[([^\]]+)\]$', name)
    if cat_match:
        catalog = cat_match.group(1).strip()
        # Invalid catalog numbers
        if catalog in ['_', '', '-'] or catalog.lower() in ['disk1', 'disk2', 'disc1', 'disc2']:
            catalog = None
        name = name[:cat_match.start()].strip()

    artist, album = '', ''
    if ' - ' in name:
        parts = name.split(' - ', 1)
        artist = parts[0].strip()
        album = parts[1].strip() if len(parts) > 1 else ''
    else:
        album = name
    return artist, album, catalog

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Find mismatched entries (filename artist doesn't match Discogs title)
    print("Finding mismatched entries...")
    c.execute('''SELECT id, file_path, filename, title FROM releases
                 WHERE title IS NOT NULL AND title != ''
                 AND catalog_number IN ('_', '-', '') OR catalog_number IS NULL''')
    rows = c.fetchall()

    # Also find entries where filename artist doesn't appear in title
    c.execute('''SELECT id, file_path, filename, title FROM releases
                 WHERE title IS NOT NULL''')
    all_rows = c.fetchall()

    mismatched = []
    for row in all_rows:
        id_, fp, fn, title = row
        artist, album, cat = parse_filename(fn)
        if artist and title:
            if not artist_match(artist, title):
                mismatched.append(row)

    print(f"Found {len(mismatched)} mismatched entries")

    # Clear and re-search
    fixed = 0
    not_found = 0

    for i, (id_, fp, fn, old_title) in enumerate(mismatched, 1):
        artist, album, catalog = parse_filename(fn)
        print(f"\n[{i}/{len(mismatched)}] {fn[:60]}")
        print(f"  Old match: {old_title[:40] if old_title else 'None'}")

        result = search_with_validation(artist, album)
        time.sleep(1)

        if result:
            info = {
                'title': result.get('title', ''),
                'year': result.get('year', ''),
                'genre': ', '.join(result.get('genre', [])),
                'style': ', '.join(result.get('style', [])),
                'label': ', '.join(result.get('label', [])),
                'format': ', '.join(result.get('format', [])),
                'country': result.get('country', ''),
                'cover_url': result.get('cover_image', ''),
                'thumb_url': result.get('thumb', ''),
                'discogs_url': f"https://www.discogs.com{result.get('uri', '')}",
                'discogs_id': result.get('id', ''),
            }

            # Get price
            price_info = get_price_info(info['discogs_id'])
            time.sleep(1)

            # Download image
            local_img = download_image(info.get('cover_url') or info.get('thumb_url'), info['discogs_id'])

            c.execute('''UPDATE releases SET
                title=?, year=?, genre=?, style=?, label=?, format=?, country=?,
                cover_url=?, thumb_url=?, local_image=?, discogs_url=?, discogs_id=?,
                lowest_price=?, num_for_sale=?, tracklist=?
                WHERE id=?''',
                (info['title'], info['year'], info['genre'], info['style'],
                 info['label'], info['format'], info['country'],
                 info['cover_url'], info['thumb_url'], local_img,
                 info['discogs_url'], info['discogs_id'],
                 price_info.get('lowest_price'), price_info.get('num_for_sale', 0),
                 price_info.get('tracklist', '[]'), id_))

            print(f"  NEW: {info['title'][:50]}")
            fixed += 1
        else:
            # Clear bad match, keep only file info
            c.execute('''UPDATE releases SET
                title=NULL, year=NULL, genre=NULL, style=NULL, label=NULL, format=NULL,
                country=NULL, cover_url=NULL, thumb_url=NULL, local_image=NULL,
                discogs_url=NULL, discogs_id=NULL, lowest_price=NULL, num_for_sale=NULL,
                tracklist=NULL, community_want=NULL, community_have=NULL
                WHERE id=?''', (id_,))
            print(f"  Not found on Discogs")
            not_found += 1

        if i % 20 == 0:
            conn.commit()
            print(f"  [Saved]")

    conn.commit()
    conn.close()

    print(f"\n{'='*50}")
    print(f"Done! Fixed: {fixed}, Not found: {not_found}")

if __name__ == "__main__":
    main()
