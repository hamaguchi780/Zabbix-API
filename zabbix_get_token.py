# import requests
# import json

# # Zabbix API の設定
# ZABBIX_API_URL = "http://140.227.178.194/zabbix/api_jsonrpc.php"  # ここを実際のURLに変更
# USERNAME = "BrainBoxCloudZABBIXadmin"  # Zabbixの実際のユーザー名に変更
# PASSWORD = "D8dA6_7wFa9fA523[]a/dd56AS"  # 実際のパスワードに変更

# # APIヘッダーの設定
# headers = {
#     'Content-Type': 'application/json-rpc'
# }

# # ログイン用の関数
# def zabbix_login():
#     login_api = {
#         "jsonrpc": "2.0",
#         "method": "user.login",
#         "params": {
#             "username": USERNAME,
#             "password": PASSWORD
#         },
#         "id": 1
#     }
    
#     response = requests.post(ZABBIX_API_URL, data=json.dumps(login_api), headers=headers)
#     print("API Response:", response.text)  # レスポンスの内容を確認
#     return response.json()['result']

# # テスト実行
# if __name__ == "__main__":
#     try:
#         auth_token = zabbix_login()
#         print("ログイン成功！")
#         print("認証トークン:", auth_token)
#     except Exception as e:
#         print(f"エラーが発生しました: {str(e)}")

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