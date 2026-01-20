# CD Database Manager (cd-db)

## 📌 プロジェクトの全貌 (Project Overview)
このプロジェクトは、大量のCDコレクションを効率的に管理し、**Discogsマーケットプレイスへ出品（Listing）** するための包括的なツールキットです。
Discogs APIの技術的な制約（画像の直接アップロード不可）や、本人確認（Identity Verification）による制限を回避し、**最も効率的かつ安全に出品作業を進めるための「ハイブリッド・ワークフロー」** を構築しています。

### 核心となる独自の仕組み
1.  **ローカルWebアプリ**: `app.py`
    *   高速なUIでアイテムの選定、価格設定、コンディション入力を実行。
    *   APIを介さず、**出品用CSV** (`discogs_inventory.csv`) を生成してリスクを回避。
    *   商品写真はローカル (`listing_photos/`) に自動保存。
2.  **ブラウザ操作マクロ**: `upload_macro.py`
    *   本来APIでは不可能な「写真のアップロード」を、**ブラウザ自動操作 (Playwright)** で実現。
    *   Discogsの在庫ページとローカルDBを同期し、未送信の写真を自動でアップロードします。

---

## 🛠 システム構成 (Architecture)

### 技術スタック
- **言語**: Python 3.x
- **Webフレームワーク**: Flask (Web UI用)
- **データベース**: SQLite (`music_database.db`)
    - `releases` テーブル: アルバム情報、eBay価格データ、Discogs ID、出品ステータスを管理。
- **自動化**: Playwright (ブラウザ操作マクロ用)
- **フロントエンド**: HTML5, CSS3 (Modern Dark Mode UI)

### ディレクトリ構造
```
cd-db/
├── app.py                # Webアプリ本体（Flask）
├── upload_macro.py       # 出品写真アップロード用マクロ
├── music_database.db     # メインデータベース
├── discogs_inventory.csv # 生成される出品リスト（Discogsインポート用）
├── listing_photos/       # 撮影・保存された商品写真（アイテムIDごと）
├── templates/            # Web UIのHTMLテンプレート
├── static/               # CSSスタイルシート
└── .env                  # Discogsトークンなどの機密情報
```

---

## 🚀 ワークフロー (Workflow Details)

### Phase 1: リスト作成 (Listing Creation)
**ツール**: `app.py` (Web UI)
1.  アプリ (`python app.py`) を起動し、ブラウザ (`http://localhost:5050`) でアクセス。
2.  アイテム情報（eBay取引価格など）を確認し、出品候補を選定。
3.  **「CSVに追加」**: ボタンを押すと、`discogs_inventory.csv` に出品データが追記され、写真は `listing_photos/{id}/` に保存されます。
    *   *メリット*: API制限や認証エラーに邪魔されず、手元で高速にリストを作成できます。

### Phase 2: Discogsへのインポート (Import)
**ツール**: Discogs Webサイト
1.  Web UIの「履歴 (Drafts)」タブから、作成したCSVをダウンロード。
2.  Discogsの [Import Inventory](https://www.discogs.com/sell/upload) ページからCSVをアップロード。
3.  全てのアイテムが「下書き (Draft)」または「出品中 (For Sale)」として一括登録されます。
    *   *注意*: この時点では写真はまだありません。

### Phase 3: 写真の自動アップロード (Photo Automation)
**ツール**: `upload_macro.py` (Macro)
1.  **Sync**: `python upload_macro.py sync` を実行。Discogs上で発行された「出品ID (Listing ID)」をスキャンし、ローカルDBと紐付けます。
2.  **Upload**: `python upload_macro.py upload` を実行。紐付いたIDを元に、ローカルにある写真を自動でDiscogsにアップロードします。

---

## 🔧 技術的な詳細 (Technical Specifics)

### CSVフォーマット
Discogsの一括出品仕様に準拠しています。
- **必須カラム**: `release_id`, `price`, `media_condition`, `comments`
- **ステータス**: デフォルトで `Draft` (下書き) として出力されますが、インポート設定で即時出品も可能です。

### 自動化マクロ (Macro)
- **セッション維持**: 毎回ログインする必要がないよう、Cookie情報を `discogs_session.json` に保存します。
- **同期ロジック**: Discogsの「在庫管理」ページをスクレイピングし、ローカルDBの `discogs_id` と一致するアイテムの `listing_id` を特定・保存します。
- **アップロード**: `input[type='file']` 要素を自動探索し、画像を送信します。

---

## 📦 リポジトリ情報
- **Remote**: `https://github.com/brelbrelbrel/cddatabase.git`
- **Branch**: `main`
- **管理対象外**: `.env` (秘密鍵), `__pycache__`, `listing_photos/` 内の重い画像ファイルなどは `.gitignore` で除外されています。
