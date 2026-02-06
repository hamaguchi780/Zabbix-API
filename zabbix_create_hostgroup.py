import json
import requests

from zabbix_config import ZABBIX_API_URL, headers
from zabbix_get_token import zabbix_login  # あなたのログイン関数のあるファイル名に合わせてください

from pathlib import Path

HERE = Path(__file__).resolve().parent # 環境によって修正する
LIST_FILE = HERE / "hostgroup_create_list"

def load_group_names(path: str):
    names = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if not name or name.startswith("#"):
                continue
            names.append(name)
    return names

def hostgroup_get(auth_token: str, name: str):
    payload = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "output": ["groupid", "name"],
            "filter": {"name": [name]}
        },
        "auth": auth_token,
        "id": 1
    }
    r = requests.post(ZABBIX_API_URL, data=json.dumps(payload), headers=headers)
    r.raise_for_status()
    return r.json()

def hostgroup_create(auth_token: str, name: str):
    payload = {
        "jsonrpc": "2.0",
        "method": "hostgroup.create",
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
            res_get = hostgroup_get(auth_token, name)
            if "error" in res_get:
                print(f"GET_NG: {name} -> {res_get['error']}")
                continue

            if res_get.get("result"):
                print(f"SKIP(既存): {name}")
                continue

            res_create = hostgroup_create(auth_token, name)
            if "error" in res_create:
                print(f"CREATE_NG: {name} -> {res_create['error']}")
            else:
                ids = res_create.get("result", {}).get("groupids", [])
                print(f"OK: {name} -> {ids}")

        except Exception as e:
            print(f"ERROR: {name} -> {e}")

if __name__ == "__main__":
    main()