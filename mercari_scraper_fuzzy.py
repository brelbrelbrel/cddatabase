# -*- coding: utf-8 -*-
"""Mercari Scraper with RapidFuzz matching"""
import sqlite3
import urllib.parse
import re
import time
import sys
import io

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from rapidfuzz import fuzz

DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
JPY_TO_USD = 155
MIN_MATCH_SCORE = 60

def setup_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--lang=ja')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def normalize_catalog(cat):
    if not cat:
        return ""
    return re.sub(r'[-\s\.]', '', cat).upper()

def extract_items_from_mercari(html):
    items = []

    # Find item titles and prices
    # Mercari structure: item cards with title and price
    titles = re.findall(r'data-testid="item-cell"[^>]*>.*?<span[^>]*>([^<]{5,100})</span>', html, re.DOTALL)

    # Alternative: find all potential titles
    if not titles:
        titles = re.findall(r'<span[^>]*class="[^"]*itemLabel[^"]*"[^>]*>([^<]+)</span>', html)

    # Find prices with yen
    prices_raw = re.findall(r'([\d,]+)\s*\u5186', html)
    prices = []
    for p in prices_raw:
        try:
            val = int(p.replace(',', ''))
            if 100 < val < 500000:
                prices.append(val)
        except:
            pass

    # Build items - pair titles with prices
    for i, price in enumerate(prices[:20]):
        title = titles[i] if i < len(titles) else f"Item {i+1}"
        cat_match = re.search(r'\b([A-Z]{2,5}[-\s]?\d{3,6})\b', title, re.I)
        items.append({
            'title': title.strip() if isinstance(title, str) else str(title),
            'catalog': cat_match.group(1) if cat_match else None,
            'price_jpy': price,
            'price_usd': round(price / JPY_TO_USD, 2)
        })

    return items

def find_best_match(db_title, db_catalog, db_artist, items):
    if not items:
        return None, 0

    db_cat_norm = normalize_catalog(db_catalog)
    db_search = f"{db_artist} {db_title}".lower() if db_artist else db_title.lower()

    best_match = None
    best_score = 0

    for item in items:
        item_title = item.get('title', '')
        item_cat = item.get('catalog', '')

        title_score = fuzz.token_sort_ratio(db_search, item_title.lower())

        cat_score = 0
        if db_cat_norm and item_cat:
            item_cat_norm = normalize_catalog(item_cat)
            if db_cat_norm == item_cat_norm:
                cat_score = 100
            else:
                cat_score = fuzz.ratio(db_cat_norm, item_cat_norm)

        if cat_score > 80:
            total_score = cat_score * 0.7 + title_score * 0.3
        else:
            total_score = title_score

        if total_score > best_score:
            best_score = total_score
            best_match = item

    return best_match, best_score

def search_mercari(driver, query, db_title, db_catalog, db_artist):
    url = f"https://jp.mercari.com/search?keyword={urllib.parse.quote(query)}&status=sold_out"

    try:
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
    except Exception as e:
        return None, 0, []

    items = extract_items_from_mercari(html)
    all_prices = [item['price_usd'] for item in items]

    best, score = find_best_match(db_title, db_catalog, db_artist, items)
    return best, score, all_prices

def extract_artist_title(full_title):
    if ' - ' in full_title:
        parts = full_title.split(' - ', 1)
        return parts[0].strip(), parts[1].strip()
    return None, full_title

def main():
    print("Starting Mercari scraper...", flush=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for col, t in [('mercari_sold_price', 'REAL'), ('mercari_avg_price', 'REAL'),
                   ('mercari_sold_count', 'INTEGER'), ('mercari_match_score', 'REAL')]:
        try:
            c.execute(f'ALTER TABLE releases ADD COLUMN {col} {t}')
        except:
            pass

    c.execute('''SELECT id, title, catalog_number, discogs_id FROM releases
                 WHERE title IS NOT NULL AND title != ""
                 AND (mercari_sold_price IS NULL OR mercari_sold_price = 0)
                 GROUP BY discogs_id ORDER BY median_price DESC NULLS LAST LIMIT 300''')
    releases = c.fetchall()

    print(f"Searching Mercari (fuzzy) for {len(releases)} releases...", flush=True)
    print("=" * 60, flush=True)

    driver = setup_driver()
    found = 0
    high_conf = 0

    try:
        for i, (id_, title, catalog, discogs_id) in enumerate(releases, 1):
            artist, album = extract_artist_title(title)

            # Search by catalog first, then title
            if catalog:
                query = f"{catalog} CD"
            elif artist:
                query = f"{artist[:25]} {album[:25]} CD"
            else:
                query = f"{title[:50]} CD"

            safe_query = query[:45].encode('ascii', 'replace').decode('ascii')
            print(f"[{i}/{len(releases)}] {safe_query}...", flush=True)

            best, score, all_prices = search_mercari(driver, query, title, catalog, artist)
            time.sleep(1)

            if best and score >= MIN_MATCH_SCORE:
                avg = sum(all_prices) / len(all_prices) if all_prices else best['price_usd']
                c.execute('''UPDATE releases SET
                             mercari_sold_price=?, mercari_avg_price=?, mercari_sold_count=?, mercari_match_score=?
                             WHERE discogs_id=?''',
                          (best['price_usd'], round(avg, 2), len(all_prices), round(score, 1), discogs_id))
                found += 1
                if score >= 80:
                    high_conf += 1
                conf = "**" if score >= 80 else "o"
                print(f"  {conf} ${best['price_usd']:.2f} (score:{score:.0f}, {len(all_prices)} items)")
            else:
                print(f"    No match (best:{score:.0f})")

            if i % 20 == 0:
                conn.commit()
                print(f"  === Saved {found} ({high_conf} high conf) ===")
    finally:
        driver.quit()

    conn.commit()
    conn.close()
    print(f"\nDone! {found}/{len(releases)} ({high_conf} high confidence)")

if __name__ == "__main__":
    main()
