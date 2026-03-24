import requests
import json
from zabbix_config import ZABBIX_API_URL, USERNAME, PASSWORD, headers

# ログイン用の関数
def zabbix_login():
    login_api = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": USERNAME,
            "password": PASSWORD
        },
        "id": 1
    }

    response = requests.post(ZABBIX_API_URL, data=json.dumps(login_api), headers=headers)
    print("API Response:", response.text)  # レスポンスの内容を確認
    return response.json()['result']

# テスト実行
if __name__ == "__main__":
    try:
        auth_token = zabbix_login()
        print("ログイン成功！")
        print("認証トークン:", auth_token)
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")