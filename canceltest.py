import requests
import json

# --- 設定項目 ---
API_PASSWORD = 'Cinco123manco'
TRADING_PASSWORD = 'Cinco123manco'
BASE_URL = 'http://localhost:18080/kabusapi'
ORDER_ID = '20260114A02N99717048' 

def get_token():
    url = f'{BASE_URL}/token'
    obj = {'ApiPassword': API_PASSWORD}
    response = requests.post(url, json=obj)
    
    if response.status_code != 200:
        print(f"❌ トークン取得失敗: {response.json()}")
        exit()
    return response.json()['Token']

# トークン取得
token = get_token()
print(f"🔑 Token取得成功: {token}")

# 取消注文の送信
def cancel_order(token, order_id):
    url = f"{BASE_URL}/cancelorder"
    
    # ★ここが修正ポイント！ Content-Type を明示する
    headers = {
        "X-API-KEY": token,
        "Content-Type": "application/json"
    }
    
    obj = {
        "Password": TRADING_PASSWORD,
        "OrderId": order_id
    }
    # 余計な空白を削除してJSON化
    json_data = json.dumps(obj, separators=(',', ':')).encode('utf-8')
    
    print(f"📡 注文 {order_id} の取消を送信中...")
    response = requests.put(url, headers=headers, data=json_data)
    return response.json()

# 実行
result = cancel_order(token, ORDER_ID)
print(f"結果: {result}")