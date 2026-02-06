# ※Pythonが前提(V3.8～,検証3.13.7)

- 仮想環境の有効化 （作業フォルダ移行後下記コマンドを実施）
  - .\venv\Scripts\activate

- 仮想環境の無効化
  - deactivate

- hostgroup_create_listに作成したいホストグループ名を記載する
- zabbix_create_hostgroup.pyを実行
- host_create_list.csvに必要事項を記載(詳細は下記)
- zabbix_create_host.pyを実行

## hostgroup_create_list

複数グループ作成は行ごとに記載する

## host_create_list.csv

### 詳細

- 1列目：
  - ホストグループ名。監視対象ホストを所属させるホストグループ名を記載する
  - 複数のホストグループを登録する際は、ダブルクォーテーション("")で記載する

- 2列目：
  - ホスト名。Zabbixに登録する**ID**を記載する

- 3列目：
  - 表示名。管理画面に表示する名前を記載する

- 4列目：
  - インターフェースタイプ。基本1でOK
  - (1:Zabbixエージェント、2:SNMP、3:IPMI、4:JMX)

- 5列目：
  - インターフェースをデフォルトで使用するか否か
  - 基本は1。
  - (0:使用しない、1:使用する)

- 6列目：
  - 接続にDNSとIPアドレスのどちらを使用するか
  - 基本は1.
  - (0:DNSに接続して監視を行う、1:IPアドレスで監視を行う)

- 7列目：
  - IPアドレス

- 8列目：
  - インターフェースが使用するポート
  - Zabbixエージェントで監視する場合は「10051」を指定する。
  - SNMPの監視は「161」

- 9列目：
  - UTM番号
  
- 10列目：
  - ユーザーID

---

- <https://www.zabbix.com/documentation/7.0/en/manual/api/reference/host/create>
- <https://www.zabbix.com/documentation/7.0/en/manual/api/reference/host/object#host>
- <https://devlog.arksystems.co.jp/2019/08/06/8884/>
