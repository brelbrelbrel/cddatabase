# Music Database Project - プロジェクト詳細

## 概要
FLACファイルコレクション (1154枚) の価格調査・販売管理システム。
Discogs/eBay/ヤフオク/メルカリの販売価格を収集し、HTMLで一覧表示。

---

## GitHub情報

| 項目 | 値 |
|------|-----|
| Repository | https://github.com/brelbrelbrel/brelbrelbrel.git |
| Branch | main |
| 備考 | 現在ETF戦略コードがmain、音楽DBコードは未コミット |

**注意**: 音楽DBプロジェクトはGitHubにコミットされていない。
リモートPC (`100.121.71.47`) のDesktopにのみ存在。

---

## ディレクトリ構造

### リモートPC (kawamura@100.121.71.47)
```
C:\Users\kawamura\Desktop\
├── flaccue/                          # FLACファイル格納 (1154枚)
│   ├── CLASSIC/                      # クラシック
│   │   └── Alfred Brendel/
│   │       └── Album [CATALOG]/
│   │           └── *.flac
│   ├── ROCK/                         # ロック・洋楽
│   ├── JAZZ/                         # ジャズ
│   └── ...
│
├── music_images/                     # ダウンロード済みカバー画像
│
├── music_database.db                 # SQLiteデータベース (メイン)
├── music_database.html               # 価格一覧HTML
│
├── create_music_db.py                # DB作成 + Discogs API
├── fix_html.py                       # HTML生成
│
├── ebay_scraper_fuzzy.py             # eBay価格スクレイピング ★
├── yahoo_scraper_fuzzy.py            # ヤフオク価格スクレイピング ★
├── mercari_scraper_fuzzy.py          # メルカリ価格スクレイピング ★
│
├── add_ebay_cols.py                  # DBカラム追加 (eBay)
├── add_yahoo_cols.py                 # DBカラム追加 (Yahoo)
├── check_top_ebay.py                 # 高額アイテム確認
│
└── test_*.py, debug_*.py             # 各種テスト・デバッグ用
```

### ローカルPC (C:\Users\user)
```
C:\Users\user\
├── ebay_scraper_fuzzy.py             # 編集用コピー
├── yahoo_scraper_fuzzy.py            # 編集用コピー
├── mercari_scraper_fuzzy.py          # 編集用コピー
├── check_top_ebay.py                 # 統計確認スクリプト
└── MUSIC_DB_PROJECT.md               # このファイル
```

---

## データベーススキーマ

### releases テーブル (38カラム)

```sql
CREATE TABLE releases (
    -- 基本情報
    id INTEGER PRIMARY KEY,
    file_path TEXT,                   -- FLACファイルパス
    filename TEXT,                    -- ファイル名
    catalog_number TEXT,              -- カタログ番号 (例: TOCP-65911)
    genre_folder TEXT,                -- フォルダ分類 (CLASSIC/ROCK等)

    -- Discogs情報
    title TEXT,                       -- "Artist - Album"
    year TEXT,
    genre TEXT,
    style TEXT,
    label TEXT,
    format TEXT,
    country TEXT,
    cover_url TEXT,
    thumb_url TEXT,
    local_image TEXT,                 -- ローカル画像パス
    discogs_url TEXT,
    discogs_id INTEGER,
    community_want INTEGER,
    community_have INTEGER,
    tracklist TEXT,                   -- JSON配列

    -- Discogs価格
    lowest_price REAL,                -- 現在出品最安値
    num_for_sale INTEGER,
    median_price REAL,                -- 中央値 ★重要
    highest_price REAL,
    high_price REAL,
    last_sold_date TEXT,

    -- eBay価格
    ebay_sold_price REAL,             -- 落札価格
    ebay_avg_price REAL,              -- 平均価格
    ebay_sold_count INTEGER,          -- 販売件数
    ebay_match_score REAL,            -- マッチスコア (0-100)

    -- ヤフオク価格
    yahoo_sold_price REAL,
    yahoo_avg_price REAL,
    yahoo_sold_count INTEGER,
    yahoo_match_score REAL,

    -- メルカリ価格
    mercari_sold_price REAL,
    mercari_avg_price REAL,
    mercari_sold_count INTEGER,
    mercari_match_score REAL,

    created_at TIMESTAMP
);
```

---

## 主要スクリプト詳細

### 1. create_music_db.py
**目的**: FLACファイルをスキャンしてDBを作成、Discogs APIで情報取得

```python
# 処理フロー
1. C:\Users\kawamura\Desktop\flaccue\ を再帰スキャン
2. ファイル名からアーティスト・アルバム・カタログ番号を抽出
   例: "David Bowie - Hunky Dory [TOCP-65911].flac"
   → artist="David Bowie", album="Hunky Dory", catalog="TOCP-65911"
3. Discogs API検索 (カタログ番号 → タイトル → アーティスト)
4. 価格情報取得 (marketplace statistics)
5. カバー画像ダウンロード
6. DBに保存
```

**設定**:
```python
FLACCUE_DIR = r"C:\Users\kawamura\Desktop\flaccue"
DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
DISCOGS_TOKEN = "WQDfPrbhGrmXKlPIFVRqmHKLDCdLNCobTYHTviKI"
```

---

### 2. ebay_scraper_fuzzy.py ★
**目的**: eBay sold items から落札価格を取得

```python
# 依存関係
from selenium import webdriver           # ブラウザ自動化
from rapidfuzz import fuzz                # ファジーマッチング

# 設定
DB_PATH = r"C:\Users\kawamura\Desktop\music_database.db"
JPY_TO_USD = 155                          # 円→ドル換算レート
MIN_MATCH_SCORE = 60                      # 最低マッチスコア

# 処理フロー
1. DBから未処理リリース300件取得 (median_price DESC)
2. 検索クエリ生成:
   - 優先: "{artist} {album} CD" (国際市場向け)
   - 次点: "{catalog} CD"
3. eBay検索 (LH_Complete=1&LH_Sold=1&_sacat=176985)
4. HTML解析:
   - 価格: s-card__price から抽出
   - タイトル: s-card__title > su-styled-text から抽出
5. RapidFuzzでマッチング:
   - token_sort_ratio() でタイトル比較
   - catalog番号が一致すれば70%加重
6. スコア60以上でDBに保存

# 重要な修正履歴
- 検索優先順位: catalog → artist/album に変更 (洋楽対応)
- 価格パース: JPY対応追加 ("2,328 円" → $15.02)
- タイトル抽出: eBay HTML構造変更に対応
```

**マッチングロジック**:
```python
def find_best_match(db_title, db_catalog, db_artist, items):
    for item in items:
        title_score = fuzz.token_sort_ratio(db_search, item_title)

        if catalog_match > 80:
            total_score = catalog_score * 0.7 + title_score * 0.3
        else:
            total_score = title_score

    return best_match if score >= 60 else None
```

---

### 3. yahoo_scraper_fuzzy.py
**目的**: ヤフオク落札価格を取得

```python
# 特徴
- Selenium不要 (urllib.request使用)
- カタログ番号優先検索 (日本市場)
- 同じRapidFuzzマッチングロジック

# 検索URL
https://auctions.yahoo.co.jp/closedsearch/closedsearch?
    p={query}&va={query}&auccat=22260
    # 22260 = 音楽 > CD
```

---

### 4. mercari_scraper_fuzzy.py
**目的**: メルカリ sold items を取得

```python
# 特徴
- Selenium必須 (JavaScript読み込み)
- 結果: 0件 (スコアが低すぎる)
- 原因: メルカリのタイトルが短縮・省略されすぎ

# 検索URL
https://jp.mercari.com/search?keyword={query}&status=sold_out
```

---

### 5. fix_html.py
**目的**: DBからHTMLを生成

```python
# 機能
- 全1154件を読み込み
- JSONとしてHTMLに埋め込み
- ソート: Discogs/eBay/Yahoo/メルカリ 高い順/低い順
- フィルター: 全て/価格あり/価格なし
- TOP 10ランキング表示
- モーダルで詳細表示 (4プラットフォーム価格比較)
- 音楽再生機能 (file:// プロトコル)
```

---

## 現在のデータ統計

| プラットフォーム | 件数 | 高信頼 | 合計金額 |
|-----------------|------|--------|---------|
| 総リリース数 | 1,154 | - | - |
| Discogs | 790 | - | $21,533.46 |
| eBay | 182 | 52 | $4,875.19 |
| ヤフオク | 63 | - | - |
| メルカリ | 0 | - | - |

---

## 現在の問題点

### 1. メルカリスコアが低い (クリティカル)
**症状**: 全300件で最高スコア28、マッチ0件

**原因**:
- メルカリの出品タイトルが省略されすぎ
- 例: "Daft Punk CD" (本来: "Daft Punk - Homework [Virgin]")
- カタログ番号が含まれない

**対策案**:
```python
# 案1: スコア閾値を下げる (60 → 40)
# 案2: 価格レンジでフィルタリング追加
# 案3: メルカリは諦める (eBay/Yahoo で十分)
```

---

### 2. eBayマッチ精度 (中程度)
**症状**: 182件中52件のみ高信頼 (score >= 80)

**原因**:
- 同じアルバムでも版違い (日本盤/US盤/UK盤)
- コンピレーションアルバムの混同
- スコア60-79は誤マッチの可能性あり

**対策案**:
```python
# 案1: country/label でフィルタリング
# 案2: 手動レビュー機能追加
# 案3: 高信頼 (score >= 80) のみ使用
```

---

### 3. 重複リリース
**症状**: 同じdiscogs_idで複数レコード

**原因**:
- 複数ディスクセット (Disc 1, Disc 2)
- 同じアルバムの異なるフォーマット

**対策**:
```sql
-- 現在のクエリ
GROUP BY discogs_id ORDER BY median_price DESC
-- これで重複は回避しているが、HTMLには全件表示
```

---

### 4. 価格の信頼性
**症状**: 一部の価格が異常に高い/低い

**例**:
- King Crimson - Larks' Tongues: eBay $193.94 vs Discogs $33.48
- 理由: eBayで別版 (SHM-CD, Deluxe等) がヒット

**対策案**:
```python
# 価格差が大きい場合は警告フラグ
if abs(ebay_price - discogs_price) / discogs_price > 2:
    flag = "PRICE_MISMATCH"
```

---

### 5. エンコーディング問題 (解決済み)
**症状**: SSH経由で日本語出力エラー

**解決策**:
```python
# NG
print("価格: ¥1,000")
# OK
safe_text = text.encode('ascii', 'replace').decode('ascii')
print(safe_text)
```

---

### 6. eBay HTML構造変更 (解決済み)
**症状**: タイトル抽出が0件

**解決策**:
```python
# 旧 (動かない)
titles = re.findall(r'class="[^"]*s-card__title[^"]*"[^>]*>([^<]+)', html)

# 新 (動作)
titles = re.findall(r's-card__title.*?su-styled-text[^>]*>([^<]+)', html, re.DOTALL)
```

---

### 7. GitHubに未コミット
**リスク**: リモートPCのデータ消失時に復旧不可

**対策**:
```bash
# リモートで新規リポジトリ作成
cd C:\Users\kawamura\Desktop
git init
git add *.py *.md
git commit -m "Music database project"
git remote add origin https://github.com/...
git push -u origin main

# 注意: music_database.db (大容量) は .gitignore 推奨
```

---

## 未実装機能

### 1. 自動出品フォーム
- [ ] Discogs出品API連携
- [ ] eBayセラーAPI連携
- [ ] ヤフオクCSVエクスポート

### 2. 在庫管理
- [ ] 販売済みフラグ
- [ ] 複数プラットフォーム在庫同期

### 3. 価格更新
- [ ] 定期的な価格再取得
- [ ] 価格変動アラート

---

## 接続情報

| 項目 | 値 |
|------|-----|
| リモートPC | kawamura@100.121.71.47 (Tailscale) |
| SSH | `ssh kawamura@100.121.71.47` |
| SCP | `scp file.py kawamura@100.121.71.47:C:/Users/kawamura/Desktop/` |

---

## 実行方法

```bash
# 1. Discogs価格取得 (初回のみ)
ssh kawamura@100.121.71.47 "cd C:\Users\kawamura\Desktop && python create_music_db.py"

# 2. eBay価格取得
ssh kawamura@100.121.71.47 "cd C:\Users\kawamura\Desktop && python ebay_scraper_fuzzy.py"

# 3. ヤフオク価格取得
ssh kawamura@100.121.71.47 "cd C:\Users\kawamura\Desktop && python yahoo_scraper_fuzzy.py"

# 4. HTML更新
ssh kawamura@100.121.71.47 "cd C:\Users\kawamura\Desktop && python fix_html.py"

# 5. HTMLをブラウザで開く
# C:\Users\kawamura\Desktop\music_database.html
```
