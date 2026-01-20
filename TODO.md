# Project Todo List

## 🚨 最優先 (Priority: High)
Discogsでの販売を開始するために必須のアクションです。

- [ ] **Discogs 本人確認 (Identity Verification)**
    - [ ] Discogsの「出品者設定 (Seller Settings)」から本人確認書類（免許証・パスポート等）を提出。
    - [ ] 承認メールを受信し、出品制限を解除する。
    - *現状*: これが完了しないと、CSVをインポートしても出品が公開されません。

- [ ] **配送ポリシー (Shipping Policies) の設定**
    - [ ] 日本郵便（EMS, eパケットなど）またはクーリエ（FedEx/DHL）の料金表に基づき、Discogsで送料を設定する。
    - [ ] 特に北米・欧州・アジア向けの送料を明確にする。

## 💻 開発・運用タスク (Development & Operations)

### 短期目標 (Short-term)
- [ ] **テスト出品の実施**
    - [ ] `app.py` で数点リストを作成する。
    - [ ] `discogs_inventory.csv` をDiscogsにインポートしてみる。
    - [ ] `upload_macro.py` を動かし、写真が正しく反映されるか確認する。

- [ ] **在庫 (Inventory) の整合性チェック**
    - [ ] ローカルDBの価格と、実際にDiscogsに出品された価格が一致しているか定期チェックする仕組みの検討。

### 中長期目標 (Long-term)
- [ ] **eBay併売対応 (Cross-listing)**
    - [ ] 現在はDiscogs専用だが、同じデータを使ってeBay用のCSVを出力する機能の追加。
- [ ] **価格改定の自動化 (Repricing)**
    - [ ] 定期的にDiscogsの市場価格 (`median_price`) を再取得し、価格を自動調整する機能の実装。
- [ ] **ダッシュボードの強化**
    - [ ] 売上分析や、出品数の推移をグラフ表示する機能。

## ✅ 完了済み (Completed)
- [x] プロジェクトフォルダの整理とGit初期化
- [x] Webアプリ (`app.py`) の日本語化・モダンUI化
- [x] Discogs API依存からの脱却（CSV出力モードの実装）
- [x] 写真アップロード自動化マクロ (`upload_macro.py`) の開発
- [x] GitHubリポジトリ (`brelbrelbrel/cddatabase`) へのプッシュ
