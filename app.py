import urllib.request
import urllib.parse
import json
import sqlite3
import os
import datetime
import csv
from flask import Flask, request, render_template, redirect, url_for, flash, get_flashed_messages, send_file
from werkzeug.utils import secure_filename

# --- Configuration ---
# Load .env manually to avoid dependency
if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_for_flash')

# Relative Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "music_database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "listing_photos")
CSV_PATH = os.path.join(BASE_DIR, "discogs_inventory.csv")

# Ensure directories exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Ensure CSV exists with header
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Discogs Bulk Upload Header
        writer.writerow(['release_id', 'price', 'media_condition', 'sleeve_condition', 'comments', 'status', 'external_id'])

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def append_to_csv(release_id, price, condition, comments, item_id):
    try:
        with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # formatted for Discogs
            writer.writerow([
                release_id, 
                f"{price:.2f}", 
                condition, 
                condition, # Sleeve condition same as media for now
                comments, 
                'Draft', # Note: Discogs import might ignore this and set to For Sale, but useful for reference
                item_id  # external_id for tracking
            ])
        return True, None
    except Exception as e:
        return False, str(e)

# --- Routes ---

@app.route('/')
def index():
    mode = request.args.get('mode', 'guide')
    conn = get_db()
    item = None
    count = 0
    sub_stage = "guide"
    
    if mode == 'guide':
        # 1. Listing Phase (Score >= 80, Not Listed)
        # Note: listing_status 'Draft' here now means "Added to CSV"
        query_list = "SELECT * FROM releases WHERE ebay_match_score >= 80 AND (listing_status IS NULL OR listing_status != 'CSV_Ready')"
        item = conn.execute(query_list + " LIMIT 1").fetchone()
        
        if item:
             sub_stage = "list"
             count = conn.execute("SELECT COUNT(*) FROM releases WHERE ebay_match_score >= 80 AND (listing_status IS NULL OR listing_status != 'CSV_Ready')").fetchone()[0]
        else:
             # 2. Review Phase (Score < 80)
             query_review = "SELECT * FROM releases WHERE ebay_match_score > 0 AND ebay_match_score < 80"
             item = conn.execute(query_review + " LIMIT 1").fetchone()
             sub_stage = "review"
             count = conn.execute("SELECT COUNT(*) FROM releases WHERE ebay_match_score > 0 AND ebay_match_score < 80").fetchone()[0]
             
    elif mode == 'drafts':
        sub_stage = "drafts"
        csv_rows = []
        if os.path.exists(CSV_PATH):
            try:
                with open(CSV_PATH, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        csv_rows.append(row)
                # Show newest first
                csv_rows.reverse()
            except Exception as e:
                print(f"CSV Read Error: {e}")
        
        count = len(csv_rows)
        # item is not used in drafts mode for the card view, but we pass rows
        return render_template('index.html', item=None, count=count, mode=mode, stage=sub_stage, csv_rows=csv_rows)
        
    conn.close()
    return render_template('index.html', item=item, count=count, mode=mode, stage=sub_stage)

@app.route('/confirm/<int:item_id>', methods=['POST'])
def confirm(item_id):
    conn = get_db()
    conn.execute("UPDATE releases SET ebay_match_score = 100 WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash('✅ 確認しました！出品ステップへ進みます。', 'success')
    return redirect(url_for('index'))

@app.route('/reject/<int:item_id>', methods=['POST'])
def reject(item_id):
    conn = get_db()
    conn.execute("""
        UPDATE releases 
        SET ebay_sold_price = NULL, 
            ebay_avg_price = NULL, 
            ebay_sold_count = NULL, 
            ebay_match_score = NULL 
        WHERE id = ?
    """, (item_id,))
    conn.commit()
    conn.close()
    flash('❌ 却下しました。マッチングデータをクリアしました。', 'info')
    return redirect(url_for('index'))

@app.route('/list_discogs/<int:item_id>', methods=['POST'])
def list_discogs(item_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM releases WHERE id = ?", (item_id,)).fetchone()
    
    if not item or not item['discogs_id']:
        return "エラー: Discogs IDがありません", 400
        
    manual_price = request.form.get('price')
    condition = request.form.get('condition', 'Near Mint (NM or M-)')
    missing_obi = 'missing_obi' in request.form
    
    # Handle Photo Upload (Just saving locally for now)
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename:
            item_folder = os.path.join(UPLOAD_FOLDER, str(item_id))
            if not os.path.exists(item_folder):
                os.makedirs(item_folder)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{secure_filename(file.filename)}"
            file.save(os.path.join(item_folder, filename))
            # Photos can't be added to CSV import directly, need hosting
            # We just save them here for manual reference

    # Price logic
    if manual_price:
        price = float(manual_price)
    else:
        price = item['median_price'] if item['median_price'] and item['median_price'] > 0 else 9.99

    comments = "Unplayed / Unused item from warehouse stock."
    if missing_obi:
        comments += " Missing Obi / 帯なし."
    
    # Save to CSV
    success, error = append_to_csv(item['discogs_id'], price, condition, comments, item_id)
    
    if success:
        # listing_status changed from 'Draft' to 'CSV_Ready'
        conn.execute("UPDATE releases SET listing_status = 'CSV_Ready' WHERE id = ?", (item_id,))
        conn.commit()
        flash(f"✅ CSVに追加しました！ (ID: {item_id})", "success")
    else:
        flash(f"❌ CSV書き込みエラー: {error}", "error")
        
    conn.close()
    return redirect(url_for('index', mode='guide'))

@app.route('/download_csv')
def download_csv():
    if os.path.exists(CSV_PATH):
        return send_file(CSV_PATH, as_attachment=True, download_name='discogs_inventory.csv')
    else:
        flash("CSVファイルがまだ作成されていません", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    print("Starting Music DB Manager (CSV Mode)...")
    app.run(host='0.0.0.0', debug=True, port=5050)
