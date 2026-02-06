import json
import requests

from zabbix_config import ZABBIX_API_URL, headers
from zabbix_get_token import zabbix_login  # あなたのログイン関数のファイル名に合わせて変更

TEMPLATE_NAMES = [
    "YUYAMA_Template_IRIS", "Update Check",
    # "将来追加するテンプレート名",
]

def template_get(auth_token: str, names: list[str]):
    payload = {
        "jsonrpc": "2.0",
        "method": "template.get",
        "params": {
            "output": ["templateid", "host", "name"],
            "filter": {"host": names}  # 通常テンプレート名は host
        },
        "auth": auth_token,
        "id": 1
    }
    r = requests.post(ZABBIX_API_URL, data=json.dumps(payload), headers=headers)
    r.raise_for_status()
    return r.json()

def main():
    auth_token = zabbix_login()

    res = template_get(auth_token, TEMPLATE_NAMES)
    if "error" in res:
        print(f"NG -> {res['error']}")
        return

    found = {t.get("host"): t for t in res.get("result", [])}

    for name in TEMPLATE_NAMES:
        t = found.get(name)
        if t:
            print(f"FOUND: {name} templateid={t.get('templateid')}")
        else:
            print(f"NOTFOUND: {name}")

if __name__ == "__main__":
    main()