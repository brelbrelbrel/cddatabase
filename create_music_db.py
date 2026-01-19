# -*- coding: utf-8 -*-
"""
Music Database Creator with Discogs Integration
Usage: python create_music_db.py
"""
import os
import sys
import io
# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import re
import json
import time
import sqlite3
import urllib.request
import urllib.parse
import webbrowser
from pathlib import Path
from datetime import datetime

# Configuration
FLACCUE_DIR = r"C:\Users\kawamura\Desktop\flaccue"
DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
HTML_PATH = r"C:\Users\kawamura\Desktop\music_database.html"
IMAGES_DIR = r"C:\Users\kawamura\Desktop\music_images"

# Discogs API
DISCOGS_SEARCH_URL = "https://api.discogs.com/database/search"
DISCOGS_TOKEN = "WQDfPrbhGrmXKlPIFVRqmHKLDCdLNCobTYHTviKI"
USER_AGENT = "MusicDBCreator/1.0 +https://example.com"

def parse_filename(filename):
    """Parse filename like 'Artist - Album [CATALOG-123].flac' into parts"""
    # Remove extension
    name = re.sub(r'\.flac$', '', filename, flags=re.IGNORECASE)

    # Extract catalog number
    catalog = None
    cat_match = re.search(r'\[([^\]]+)\]$', name)
    if cat_match:
        catalog = cat_match.group(1).strip()
        if catalog.lower() in ['disk1', 'disk2', 'disc1', 'disc2', 'part1', 'part2', 'part3']:
            catalog = None
        name = name[:cat_match.start()].strip()

    # Split artist and album
    artist, album = '', ''
    if ' - ' in name:
        parts = name.split(' - ', 1)
        artist = parts[0].strip()
        album = parts[1].strip() if len(parts) > 1 else ''
    else:
        album = name

    return artist, album, catalog

def do_discogs_search(params):
    """Execute Discogs search with given parameters"""
    try:
        params['per_page'] = 3
        query = urllib.parse.urlencode(params)
        url = f"{DISCOGS_SEARCH_URL}?{query}"
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Authorization': f'Discogs token={DISCOGS_TOKEN}'})

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        if data.get('results'):
            r = data['results'][0]
            return {
                'title': r.get('title', ''),
                'year': r.get('year', ''),
                'genre': ', '.join(r.get('genre', [])),
                'style': ', '.join(r.get('style', [])),
                'label': ', '.join(r.get('label', [])),
                'format': ', '.join(r.get('format', [])),
                'country': r.get('country', ''),
                'cover_url': r.get('cover_image', ''),
                'thumb_url': r.get('thumb', ''),
                'discogs_url': f"https://www.discogs.com{r.get('uri', '')}",
                'discogs_id': r.get('id', ''),
                'community_want': r.get('community', {}).get('want', 0),
                'community_have': r.get('community', {}).get('have', 0),
            }
    except Exception as e:
        print(f"      API Error: {e}")
    return None

def normalize_catalog(catalog):
    """Generate catalog number variants for fuzzy matching"""
    if not catalog:
        return []

    variants = [catalog]  # Original

    # Remove common label prefixes
    labels = ['cpo', 'bis', 'naxos', 'dg', 'emi', 'decca', 'philips', 'sony', 'bmg', 'rca', 'erato', 'harmonia', 'virgin', 'teldec', 'au', 'alcd', 'focd', 'toce', 'phcp', 'coco']
    cat_lower = catalog.lower()
    for label in labels:
        if cat_lower.startswith(label + ' '):
            variants.append(catalog[len(label):].strip())
        elif cat_lower.startswith(label + '-'):
            variants.append(catalog[len(label)+1:].strip())
        elif cat_lower.startswith(label) and len(catalog) > len(label):
            rest = catalog[len(label):].strip()
            if rest and rest[0].isdigit():
                variants.append(rest)

    # Space/hyphen variations
    for v in list(variants):
        if ' ' in v:
            variants.append(v.replace(' ', '-'))
            variants.append(v.replace(' ', ''))
        if '-' in v:
            variants.append(v.replace('-', ' '))
            variants.append(v.replace('-', ''))

    return list(dict.fromkeys([v for v in variants if v]))[:5]  # Max 5 variants

def search_discogs(artist, album, catalog):
    """Search Discogs with multiple fuzzy strategies"""

    # Strategy 1: Catalog number variations
    if catalog:
        for cat_variant in normalize_catalog(catalog):
            print(f"    [1] catno: {cat_variant}")
            result = do_discogs_search({'catno': cat_variant})
            if result:
                return result
            time.sleep(1)

    # Strategy 2: Artist + catalog in general query
    if artist and catalog:
        cat_clean = re.sub(r'^[a-zA-Z]+[\s\-]*', '', catalog)  # Remove label prefix
        query = f"{artist} {cat_clean}"
        print(f"    [2] query artist+cat: {query[:40]}")
        result = do_discogs_search({'q': query, 'type': 'release'})
        if result:
            return result
        time.sleep(1)

    # Strategy 3: Artist + Album title
    if artist and album:
        print(f"    [3] artist+album: {artist[:20]} / {album[:20]}")
        result = do_discogs_search({'artist': artist, 'release_title': album})
        if result:
            return result
        time.sleep(1)

    # Strategy 4: General query
    if artist and album:
        query = f"{artist} {album}"[:50]
        print(f"    [4] query: {query}")
        result = do_discogs_search({'q': query, 'type': 'release'})
        if result:
            return result
        time.sleep(1)

    # Strategy 5: Artist only (last resort)
    if artist:
        print(f"    [5] artist only: {artist[:30]}")
        result = do_discogs_search({'artist': artist, 'type': 'release'})
        if result:
            return result

    return None

def get_release_price(release_id):
    """Get marketplace price for a release"""
    try:
        url = f"https://api.discogs.com/releases/{release_id}"
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Authorization': f'Discogs token={DISCOGS_TOKEN}'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return {
            'lowest_price': data.get('lowest_price'),
            'num_for_sale': data.get('num_for_sale', 0),
            'tracklist': [t.get('title', '') for t in data.get('tracklist', [])]
        }
    except:
        return None

def download_image(url, discogs_id):
    """Download image to local folder, return local path"""
    if not url or not discogs_id:
        return None

    # Create images directory
    Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)

    # Determine extension from URL
    ext = '.jpg'
    if '.png' in url.lower():
        ext = '.png'

    local_path = Path(IMAGES_DIR) / f"{discogs_id}{ext}"

    # Skip if already exists
    if local_path.exists():
        return str(local_path)

    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(local_path, 'wb') as f:
                f.write(resp.read())
        print(f"      Image saved: {discogs_id}{ext}")
        return str(local_path)
    except Exception as e:
        print(f"      Image download error: {e}")
        return None

def create_database():
    """Create SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS releases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE,
        filename TEXT,
        catalog_number TEXT,
        genre_folder TEXT,
        title TEXT,
        year TEXT,
        genre TEXT,
        style TEXT,
        label TEXT,
        format TEXT,
        country TEXT,
        cover_url TEXT,
        thumb_url TEXT,
        local_image TEXT,
        discogs_url TEXT,
        discogs_id INTEGER,
        community_want INTEGER DEFAULT 0,
        community_have INTEGER DEFAULT 0,
        lowest_price REAL,
        num_for_sale INTEGER DEFAULT 0,
        tracklist TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    return conn

def scan_files(conn):
    """Scan and populate database"""
    c = conn.cursor()

    print("Scanning FLAC files...")
    flac_files = list(Path(FLACCUE_DIR).rglob("*.flac"))

    # Parse all files
    files_to_process = []
    for f in flac_files:
        artist, album, catalog = parse_filename(f.name)
        if catalog or artist:  # Process if has catalog or artist
            files_to_process.append((f, artist, album, catalog))

    total = len(files_to_process)
    print(f"Found {len(flac_files)} FLAC files, {total} to process")
    print()

    processed = 0
    found = 0

    for i, (flac, artist, album, catalog) in enumerate(files_to_process, 1):
        # Check if already in DB
        c.execute("SELECT id FROM releases WHERE file_path = ?", (str(flac),))
        if c.fetchone():
            print(f"[{i}/{total}] SKIP (in DB): {flac.name[:50]}")
            continue

        # Get folder info
        rel_path = flac.relative_to(FLACCUE_DIR)
        genre_folder = rel_path.parts[0] if len(rel_path.parts) > 1 else ""

        print(f"[{i}/{total}] {artist[:20]} - {album[:25]} [{catalog or 'N/A'}]")

        info = search_discogs(artist, album, catalog)
        time.sleep(0.5)  # Rate limit between files

        if info:
            found += 1
            print(f"    Found: {info['title'][:50]}")

            # Get price info
            if info.get('discogs_id'):
                price_info = get_release_price(info['discogs_id'])
                time.sleep(1.2)
                if price_info:
                    info['lowest_price'] = price_info.get('lowest_price')
                    info['num_for_sale'] = price_info.get('num_for_sale', 0)
                    info['tracklist'] = json.dumps(price_info.get('tracklist', []))
                    if info['lowest_price']:
                        print(f"    Price: ${info['lowest_price']}")

            # Download cover image
            local_img = download_image(info.get('cover_url') or info.get('thumb_url'), info.get('discogs_id'))

            c.execute('''INSERT INTO releases
                (file_path, filename, catalog_number, genre_folder,
                title, year, genre, style, label, format, country,
                cover_url, thumb_url, local_image, discogs_url, discogs_id,
                community_want, community_have, lowest_price, num_for_sale, tracklist)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (str(flac), flac.name, catalog, genre_folder,
                info.get('title'), info.get('year'), info.get('genre'),
                info.get('style'), info.get('label'), info.get('format'),
                info.get('country'), info.get('cover_url'), info.get('thumb_url'),
                local_img, info.get('discogs_url'), info.get('discogs_id'),
                info.get('community_want', 0), info.get('community_have', 0),
                info.get('lowest_price'), info.get('num_for_sale', 0),
                info.get('tracklist', '[]')))
        else:
            print(f"    Not found")
            c.execute('''INSERT INTO releases
                (file_path, filename, catalog_number, genre_folder)
                VALUES (?, ?, ?, ?)''',
                (str(flac), flac.name, catalog, genre_folder))

        processed += 1
        if processed % 10 == 0:
            conn.commit()
            print(f"    [Saved {processed} records]")

    conn.commit()
    print(f"\nDone: {processed} processed, {found} found on Discogs")
    return found

def generate_html(conn):
    """Generate HTML viewer"""
    c = conn.cursor()
    c.execute('''SELECT * FROM releases ORDER BY
        CASE WHEN lowest_price IS NOT NULL THEN 0 ELSE 1 END,
        lowest_price DESC, community_want DESC''')
    releases = c.fetchall()
    cols = [desc[0] for desc in c.description]

    html = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Music Database</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#1a1a2e;color:#eee;padding:20px}
h1{text-align:center;color:#00d4ff;margin-bottom:20px}
.controls{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;justify-content:center}
input,select{padding:10px;border:none;border-radius:5px;background:#16213e;color:#eee}
.stats{text-align:center;margin-bottom:20px;color:#888}
.ranking{margin-bottom:30px}
.ranking h2{color:#ffd93d;text-align:center;margin-bottom:15px}
.ranking-list{display:flex;gap:15px;overflow-x:auto;padding:10px 0}
.ranking-item{min-width:120px;text-align:center;cursor:pointer}
.ranking-item:hover{transform:scale(1.05)}
.ranking-item img{width:100px;height:100px;object-fit:cover;border-radius:5px}
.ranking-num{font-size:20px;font-weight:bold;color:#ffd93d}
.ranking-price{color:#00ff88;font-weight:bold}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px}
.card{background:#16213e;border-radius:10px;overflow:hidden;cursor:pointer;transition:transform 0.2s}
.card:hover{transform:translateY(-5px);box-shadow:0 10px 30px rgba(0,212,255,0.2)}
.card img{width:100%;height:180px;object-fit:cover;background:#0f3460}
.card-body{padding:15px}
.card-title{font-size:13px;font-weight:bold;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-catalog{color:#ffd93d;font-family:monospace;font-size:12px}
.card-info{font-size:11px;color:#888;margin:3px 0}
.card-price{color:#00ff88;font-weight:bold}
.card-want{color:#ff6b6b}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:1000;overflow-y:auto}
.modal-content{max-width:700px;margin:30px auto;background:#16213e;border-radius:10px;padding:25px}
.modal-close{float:right;font-size:28px;cursor:pointer;color:#888}
.modal-close:hover{color:#fff}
.modal-img{width:100%;max-height:350px;object-fit:contain;margin-bottom:15px;border-radius:5px}
.modal h2{margin-bottom:15px}
.modal p{margin:8px 0}
.genre-tag{display:inline-block;background:#0f3460;padding:3px 8px;border-radius:3px;margin:2px;font-size:11px}
.tracklist{background:#0f3460;padding:15px;border-radius:5px;margin-top:15px;max-height:200px;overflow-y:auto}
.tracklist li{margin:5px 0;font-size:13px}
.play-btn{background:#00d4ff;color:#000;padding:10px 20px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;margin-top:15px}
.play-btn:hover{background:#00a8cc}
audio{width:100%;margin-top:15px}
.no-img{background:#0f3460;display:flex;align-items:center;justify-content:center;color:#444;font-size:40px}
</style>
</head>
<body>
<h1>🎵 Music Database</h1>
<div class="controls">
<input type="text" id="search" placeholder="Search..." oninput="filter()">
<select id="genre" onchange="filter()"><option value="">All Genres</option></select>
<select id="sort" onchange="sort()">
<option value="price_desc">Price ↓</option>
<option value="price_asc">Price ↑</option>
<option value="want_desc">Want ↓</option>
<option value="year_desc">Year ↓</option>
<option value="name">Name</option>
</select>
</div>
<div class="stats" id="stats"></div>
<div class="ranking"><h2>💰 Value Ranking</h2><div class="ranking-list" id="ranking"></div></div>
<div class="grid" id="grid"></div>
<div class="modal" id="modal" onclick="if(event.target===this)closeModal()">
<div class="modal-content" id="modalContent"></div>
</div>
<script>
const data=''' + json.dumps([dict(zip(cols, r)) for r in releases], ensure_ascii=False) + ''';
let filtered=[...data];

function init(){
const genres=[...new Set(data.map(r=>r.genre_folder).filter(g=>g))].sort();
const sel=document.getElementById('genre');
genres.forEach(g=>{const o=document.createElement('option');o.value=g;o.textContent=g;sel.appendChild(o)});
showRanking();
render();
}

function showRanking(){
const ranked=data.filter(r=>r.lowest_price>0).sort((a,b)=>b.lowest_price-a.lowest_price).slice(0,10);
document.getElementById('ranking').innerHTML=ranked.map((r,i)=>`
<div class="ranking-item" onclick="showDetail(${data.indexOf(r)})">
<div class="ranking-num">#${i+1}</div>
<img src="${r.thumb_url||''}" onerror="this.outerHTML='<div class=no-img style=width:100px;height:100px>🎵</div>'">
<div class="ranking-price">$${r.lowest_price?.toFixed(2)||'?'}</div>
<div style="font-size:10px;color:#888">${r.catalog_number||''}</div>
</div>`).join('');
}

function render(){
document.getElementById('grid').innerHTML=filtered.map((r,i)=>{
const idx=data.indexOf(r);
return `<div class="card" onclick="showDetail(${idx})">
<img src="${r.thumb_url||''}" onerror="this.outerHTML='<div class=no-img style=height:180px>🎵</div>'">
<div class="card-body">
<div class="card-title">${r.title||r.filename}</div>
<div class="card-catalog">[${r.catalog_number||'N/A'}]</div>
<div class="card-info">${r.label||''} ${r.year?'('+r.year+')':''}</div>
${r.lowest_price?`<div class="card-price">$${r.lowest_price.toFixed(2)}</div>`:''}
${r.community_want?`<div class="card-info card-want">♥${r.community_want} want</div>`:''}
</div></div>`}).join('');
document.getElementById('stats').textContent=`${filtered.length} / ${data.length} releases`;
}

function filter(){
const q=document.getElementById('search').value.toLowerCase();
const g=document.getElementById('genre').value;
filtered=data.filter(r=>{
const match=!q||(r.title||'').toLowerCase().includes(q)||(r.catalog_number||'').toLowerCase().includes(q)||(r.label||'').toLowerCase().includes(q)||(r.filename||'').toLowerCase().includes(q);
const gMatch=!g||r.genre_folder===g;
return match&&gMatch;
});
sort();
}

function sort(){
const s=document.getElementById('sort').value;
filtered.sort((a,b)=>{
switch(s){
case'price_desc':return(b.lowest_price||0)-(a.lowest_price||0);
case'price_asc':return(a.lowest_price||9999)-(b.lowest_price||9999);
case'want_desc':return(b.community_want||0)-(a.community_want||0);
case'year_desc':return(parseInt(b.year)||0)-(parseInt(a.year)||0);
case'name':return(a.title||a.filename||'').localeCompare(b.title||b.filename||'');
}
});
render();
}

function showDetail(i){
const r=data[i];
let tracks=[];try{tracks=JSON.parse(r.tracklist||'[]')}catch(e){}
document.getElementById('modalContent').innerHTML=`
<span class="modal-close" onclick="closeModal()">×</span>
<img class="modal-img" src="${r.cover_url||r.thumb_url||''}" onerror="this.style.display='none'">
<h2>${r.title||r.filename}</h2>
<p><strong>Catalog:</strong> <span class="card-catalog">${r.catalog_number||'N/A'}</span></p>
<p><strong>Label:</strong> ${r.label||'?'}</p>
<p><strong>Year:</strong> ${r.year||'?'} | <strong>Country:</strong> ${r.country||'?'}</p>
<p><strong>Format:</strong> ${r.format||'?'}</p>
${r.genre?`<p><strong>Genre:</strong> ${r.genre.split(',').map(g=>'<span class="genre-tag">'+g.trim()+'</span>').join('')}</p>`:''}
${r.lowest_price?`<p class="card-price" style="font-size:20px">💰 $${r.lowest_price.toFixed(2)} (${r.num_for_sale} for sale)</p>`:''}
${r.community_want?`<p class="card-want">♥ ${r.community_want} want / ${r.community_have} have</p>`:''}
${r.discogs_url?`<p><a href="${r.discogs_url}" target="_blank" style="color:#00d4ff">View on Discogs →</a></p>`:''}
<p style="font-size:11px;color:#666">File: ${r.file_path}</p>
<button class="play-btn" onclick="play('${r.file_path.replace(/\\/g,'/')}')">▶ Play</button>
<audio id="audio" controls style="display:none"></audio>
${tracks.length?`<div class="tracklist"><strong>Tracklist:</strong><ol>${tracks.map(t=>'<li>'+t+'</li>').join('')}</ol></div>`:''}
`;
document.getElementById('modal').style.display='block';
}

function closeModal(){document.getElementById('modal').style.display='none';const a=document.getElementById('audio');if(a)a.pause()}
function play(p){const a=document.getElementById('audio');a.src='file:///'+p;a.style.display='block';a.play()}
document.onkeydown=e=>{if(e.key==='Escape')closeModal()};
init();
</script>
</body>
</html>'''

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML saved: {HTML_PATH}")

def print_ranking(conn):
    """Print value ranking"""
    c = conn.cursor()
    c.execute('''SELECT catalog_number, title, label, year, lowest_price, community_want, discogs_url
        FROM releases WHERE lowest_price IS NOT NULL ORDER BY lowest_price DESC LIMIT 20''')

    print("\n" + "="*60)
    print("💰 VALUE RANKING (Top 20)")
    print("="*60)
    for i, (cat, title, label, year, price, want, url) in enumerate(c.fetchall(), 1):
        print(f"{i:2}. ${price:.2f} [{cat}]")
        print(f"    {(title or '')[:50]}")
        print(f"    {label} ({year}) - {want} want")
        print()

def main():
    print("="*60)
    print("Music Database Creator")
    print("="*60)
    print(f"Source: {FLACCUE_DIR}")
    print(f"Database: {DB_PATH}")
    print()

    conn = create_database()
    found = scan_files(conn)

    print("\nGenerating HTML viewer...")
    generate_html(conn)

    print_ranking(conn)

    conn.close()
    print("\n✅ Complete!")
    import webbrowser
    webbrowser.open(f'file:///{HTML_PATH}')
    # input removed for background

if __name__ == "__main__":
    main()
