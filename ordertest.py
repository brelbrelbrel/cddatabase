import urllib.request
import json
import pprint

# 設定
API_PASSWORD = 'Cinco123manco'
TRADING_PASSWORD = 'Cinco123manco'
BASE_URL = 'http://localhost:18080/kabusapi'

def get_token():
    url = f'{BASE_URL}/token'
    obj = {'ApiPassword': API_PASSWORD}
    data = json.dumps(obj).encode('utf-8')
    req = urllib.request.Request(url, data, method='POST')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())['Token']

try:
    # 1. 最新トークン取得
    token = get_token()
    print(f"🔑 Token: {token}")

    # 2. 注文データ作成
    # 変換エラー(4001005)を避けるため、公式ドキュメントの「現物買い」必須項目のみに絞っています
    obj = {
        'Password': TRADING_PASSWORD,
        'Symbol': '9404',        # 日本テレビ
        'Exchange': 1,           # 東証
        'SecurityType': 1,       # 株式
        'Side': '2',             # 買
        'CashMargin': 1,         # 現物
        'DelivType': 2,          # 0:指定なし
        'FundType': 'AA',        # 半角スペース2つ（重要：自動選択）
        'AccountType': 2,        # 2:特定口座（4ではなく2が標準）
        'Qty': 100,
        'FrontOrderType': 20,    # 指値
        'Price': 3800,
        'ExpireDay': 0           # 当日
    }

    # JSON変換（余計なスペースを入れない設定）
    json_data = json.dumps(obj, separators=(',', ':')).encode('utf-8')

    # 3. 送信
    url = f'{BASE_URL}/sendorder'
    req = urllib.request.Request(url, json_data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-KEY', token)

    print("📡 注文を送信中...")
    with urllib.request.urlopen(req) as res:
        content = json.loads(res.read())
        pprint.pprint(content)

except urllib.error.HTTPError as e:
    # 4001005が出る場合は、ここで「何が」ダメだったのか生データを出します
    print(f"❌ HTTP Error {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"❌ Error: {e}")