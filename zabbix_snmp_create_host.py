import json
import csv
import requests

from zabbix_config import ZABBIX_API_URL, headers
from zabbix_get_token import zabbix_login

from pathlib import Path

HERE = Path(__file__).resolve().parent # 環境によって修正する
LIST_FILE = HERE / "snmp_host_create_list.csv"

TEMPLATE_NAMES = ["FortiGate by SNMP"]
DEFAULT_HOST_STATUS = 1  # 1=無効, 0=有効

SNMPV3_DETAILS = {
    "version": "3",
    "bulk": "1",
    "securityname": "ZabbixUser",
    "securitylevel": "2",
    "authpassphrase": "Zabbix_BrainBoxCloud134",
    "privpassphrase": "Zabbix_BrainBoxCloud134",
    "authprotocol": "3",
    "privprotocol": "3",
    "contextname": "",
    "max_repetitions": "10",
}


def load_rows_csv(path):
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


def make_snmp_interface_v3(ip: str, port: str):
    return {
        "type": 2,  # SNMP
        "main": 1,
        "useip": 1,
        "ip": ip,
        "dns": "",
        "port": str(port or "161"),
        "details": SNMPV3_DETAILS,
    }


def build_host_name(utm_no: str):
    return f"UTM{utm_no}-SNMP"


def host_create(auth, host_name: str, groupids, iface: dict, templateids):
    params = {
        "host": host_name,
        "status": DEFAULT_HOST_STATUS,
        "groups": [{"groupid": gid} for gid in groupids],
        "interfaces": [iface],
        "templates": [{"templateid": tid} for tid in templateids],
    }
    return api_call(auth, "host.create", params, 1)


def main():
    auth = zabbix_login()
    templateids = template_get_ids_by_names(auth, TEMPLATE_NAMES)

    rows = load_rows_csv(LIST_FILE)

    for ln, cols in rows:
        group_field, _host, _disp, _iftype, _main, _useip, ip, port, utm_no, _specific_id = cols

        group_names = [g.strip() for g in group_field.split(",") if g.strip()]
        if not group_names or not ip or not utm_no:
            print(f"NG L{ln}: 必須不足 group/ip/utm_no")
            continue

        host = build_host_name(utm_no)

        try:
            if host_get(auth, host):
                print(f"SKIP(既存) L{ln}: {host}")
                continue

            groupids = hostgroup_get_ids_by_names(auth, group_names)
            iface = make_snmp_interface_v3(ip, port)

            res = host_create(auth, host, groupids, iface, templateids)

            if "error" in res:
                print(f"NG L{ln}: {host} -> {res['error']}")
            else:
                print(f"OK L{ln}: {host} -> {res.get('result', {}).get('hostids', [])}")

        except Exception as e:
            print(f"ERROR L{ln}: {host} -> {e}")


if __name__ == "__main__":
    main()