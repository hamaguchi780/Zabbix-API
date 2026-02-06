import json
import requests

from zabbix_config import ZABBIX_API_URL, headers
from zabbix_get_token import zabbix_login  # 既存のトークン取得関数を利用

LIST_FILE = "usergroup_create_list"  # 画像のファイル名に合わせる（拡張子なし想定）

def load_group_names(path: str):
    names = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if not name:
                continue
            if name.startswith("#"):
                continue
            names.append(name)
    return names

def usergroup_get(auth_token: str, name: str):
    payload = {
        "jsonrpc": "2.0",
        "method": "usergroup.get",
        "params": {
            "filter": {"name": [name]}
        },
        "auth": auth_token,
        "id": 1
    }
    r = requests.post(ZABBIX_API_URL, data=json.dumps(payload), headers=headers)
    r.raise_for_status()
    return r.json().get("result", [])

def usergroup_create(auth_token: str, name: str):
    payload = {
        "jsonrpc": "2.0",
        "method": "usergroup.create",
        "params": {
            "name": name
        },
        "auth": auth_token,
        "id": 1
    }
    r = requests.post(ZABBIX_API_URL, data=json.dumps(payload), headers=headers)
    r.raise_for_status()
    return r.json()

def main():
    auth_token = zabbix_login()
    names = load_group_names(LIST_FILE)

    if not names:
        print(f"{LIST_FILE} にグループ名がありません。")
        return

    for name in names:
        try:
            exists = usergroup_get(auth_token, name)
            if exists:
                print(f"SKIP(既存): {name}")
                continue

            res = usergroup_create(auth_token, name)
            if "error" in res:
                print(f"NG: {name} -> {res['error']}")
            else:
                ids = res.get("result", {}).get("usrgrpids", [])
                print(f"OK: {name} -> {ids}")
        except Exception as e:
            print(f"ERROR: {name} -> {e}")

if __name__ == "__main__":
    main()