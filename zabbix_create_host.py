import json
import csv
import requests
from pathlib import Path

from zabbix_config import ZABBIX_API_URL, headers
from zabbix_get_token import zabbix_login


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


def build_display_name(host_name: str, utm_no: str, specific_id: str) -> str:
    if not utm_no:
        raise ValueError("utm_no が空です")
    if not specific_id:
        raise ValueError("specific_id が空です")
    return f"{utm_no}_{specific_id}_{host_name}"


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
        group_field, host_name, display_name, if_type, main_, useip, ip_or_dns, port, utm_no, specific_id = cols

        group_names = [g.strip() for g in group_field.split(",") if g.strip()]
        if not group_names:
            print(f"NG L{ln}: hostgroup empty")
            continue

        try:
            if host_get(auth, host_name):
                print(f"SKIP(既存) L{ln}: {host_name}")
                continue

            groupids = hostgroup_get_ids_by_names(auth, group_names)
            iface = make_interface(int(if_type), int(main_), int(useip), ip_or_dns, port)

            visible_name = display_name if display_name else build_display_name(host_name, utm_no, specific_id)

            res = host_create(auth, host_name, visible_name, groupids, iface, templateids)

            if "error" in res:
                print(f"NG L{ln}: {host_name} -> {res['error']}")
            else:
                hostids = res.get("result", {}).get("hostids", [])
                print(f"OK L{ln}: {host_name} name={visible_name} groups={group_names} -> {hostids}")

        except Exception as e:
            print(f"ERROR L{ln}: {host_name} -> {e}")


if __name__ == "__main__":
    main()