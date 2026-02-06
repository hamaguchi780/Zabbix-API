import json
import csv
import requests

from zabbix_config import ZABBIX_API_URL, headers
from zabbix_get_token import zabbix_login
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIST_FILE = HERE / "host_create_list.csv"

TEMPLATE_NAMES = ["YUYAMA_Template_IRIS"]
DEFAULT_HOST_STATUS = 1  # 1=無効, 0=有効
VALID_IF_TYPES = {1, 2, 3, 4}


def load_rows_csv(path: str):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for ln, cols in enumerate(reader, 1):
            if not cols:
                continue
            if cols[0].strip().startswith("#"):
                continue
            if len(cols) != 10:
                raise ValueError(f"{path}:{ln} フォーマット不正(10列必要): {cols}")
            rows.append((ln, [c.strip() for c in cols]))
    return rows


def api_call(auth, method, params, _id=1):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "auth": auth, "id": _id}
    r = requests.post(ZABBIX_API_URL, data=json.dumps(payload), headers=headers)
    r.raise_for_status()
    return r.json()


def host_get(auth, host_name: str):
    res = api_call(auth, "host.get", {"output": ["hostid", "host"], "filter": {"host": [host_name]}}, 1)
    if "error" in res:
        raise RuntimeError(res["error"])
    return res.get("result", [])


def hostgroup_get_ids_by_names(auth, group_names):
    res = api_call(auth, "hostgroup.get", {"output": ["groupid", "name"], "filter": {"name": group_names}}, 1)
    if "error" in res:
        raise RuntimeError(res["error"])
    found = {g["name"]: g["groupid"] for g in res.get("result", [])}
    missing = [n for n in group_names if n not in found]
    if missing:
        raise RuntimeError(f"hostgroup not found: {missing}")
    return [found[n] for n in group_names]


def template_get_ids_by_names(auth, names):
    res = api_call(auth, "template.get", {"output": ["templateid", "host"], "filter": {"host": names}}, 1)
    if "error" in res:
        raise RuntimeError(res["error"])
    found = {t["host"]: t["templateid"] for t in res.get("result", [])}
    missing = [n for n in names if n not in found]
    if missing:
        raise RuntimeError(f"template not found: {missing}")
    return [found[n] for n in names]


def make_interface(if_type: int, main: int, useip: int, ip_or_dns: str, port: str):
    if if_type not in VALID_IF_TYPES:
        raise ValueError(f"IFタイプ不正: {if_type} (1/2/3/4)")
    if main not in (0, 1) or useip not in (0, 1):
        raise ValueError("main/useip は 0 or 1")
    return {
        "type": if_type,
        "main": main,
        "useip": useip,
        "ip": ip_or_dns if useip == 1 else "",
        "dns": "" if useip == 1 else ip_or_dns,
        "port": str(port),
    }


# === 要件通り：ホスト名/表示名の組み立て ===
# host: 00<特定ID(4桁ゼロ埋め)>_BrainBoxCloud
# name: <UTM番号>_00<特定ID(4桁ゼロ埋め)>_<CSV3列目>
def build_host_and_visible_name(utm_no: str, specific_id: str, display_name_part: str):
    sid4 = str(int(specific_id)).zfill(4)
    host_name = f"00{sid4}_BrainBoxCloud"          # 1234 -> 001234_BrainBoxCloud
    visible_name = f"{utm_no}_00{sid4}_{display_name_part}"
    return host_name, visible_name


def host_create(auth, host_name: str, visible_name: str, groupids, iface: dict, templateids):
    params = {
        "host": host_name,
        "name": visible_name,  # 表示名
        "status": DEFAULT_HOST_STATUS,
        "groups": [{"groupid": gid} for gid in groupids],
        "interfaces": [iface],
        "templates": [{"templateid": tid} for tid in templateids],
    }
    return api_call(auth, "host.create", params, 1)


def main():
    auth = zabbix_login()

    templateids = template_get_ids_by_names(auth, TEMPLATE_NAMES)
    print(f"Templates: {list(zip(TEMPLATE_NAMES, templateids))}")

    rows = load_rows_csv(LIST_FILE)

    for ln, cols in rows:
        group_field, host, display_name_part, if_type, main_, useip, ip_or_dns, port, utm_no, specific_id = cols

        group_names = [g.strip() for g in group_field.split(",") if g.strip()]
        if not group_names:
            print(f"NG L{ln}: hostgroup empty")
            continue

        try:
            host, visible_name = build_host_and_visible_name(utm_no, specific_id, display_name_part)

            if host_get(auth, host):
                print(f"SKIP(既存) L{ln}: {host}")
                continue

            groupids = hostgroup_get_ids_by_names(auth, group_names)
            iface = make_interface(int(if_type), int(main_), int(useip), ip_or_dns, port)

            res = host_create(auth, host, visible_name, groupids, iface, templateids)

            if "error" in res:
                print(f"NG L{ln}: {host} -> {res['error']}")
            else:
                hostids = res.get("result", {}).get("hostids", [])
                print(f"OK L{ln}: {host} name={visible_name} groups={group_names} -> {hostids}")

        except Exception as e:
            print(f"ERROR L{ln}: {host} -> {e}")


if __name__ == "__main__":
    main()