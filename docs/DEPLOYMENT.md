# Встановлення та відкат (mon, Zabbix 8.0.0rc1)

**Підготовка:** експортувати чинний шаблон `KWDS UPS Megatec by TCP` і зберегти snapshot/backup скрипта. Перевірити реальний `ExternalScripts` і `Timeout` у діючій конфігурації, зокрема можливі include. В історії був `Timeout=4`, а виклик колектора з timeout=3.

## Локальні тести

```bash
# будь-який Linux з Python3
python3 -m unittest discover -s tests -v
python3 -m py_compile collector/ups_megatec.py
```

## Встановлення скрипта (тільки після резервної копії)

```bash
# mon, root, запустити з кореня repo
install -d -o root -g root -m 755 /usr/lib/zabbix/externalscripts
cp -a /usr/lib/zabbix/externalscripts/ups_megatec.py /usr/lib/zabbix/externalscripts/ups_megatec.py.bak-before-kwds
install -o root -g root -m 755 collector/ups_megatec.py /usr/lib/zabbix/externalscripts/ups_megatec.py
python3 -m py_compile /usr/lib/zabbix/externalscripts/ups_megatec.py
sudo -u zabbix /usr/lib/zabbix/externalscripts/ups_megatec.py 172.16.0.25 9999 3
```

Після успішного тесту імпортувати `zabbix/KWDS_UPS_V10_7_Final_Zabbix8.yaml` у **Data collection → Templates → Import**. **Update existing** увімкнути для потрібних сутностей; **Delete missing** — вимкнути. Імпорт перевіряти за фактичними повідомленнями Zabbix, бо 8.0.0rc1 має особливості формату.

Перевірити Zabbix host `mt_PWR_Pochaiv` (visible `PWR_Ups-Mon - Почаїв - 0.25`), master item external check:

```text
ups_megatec.py["{$UPS.IP}","{$UPS.PORT}","{$UPS.TIMEOUT}"]
```

Натиснути **Execute now** на master item і перевірити dependent keys, формули, dashboard, No data. Окремо перевірити обробку втрати TCP: stderr з exit=1 не повинен вважатися валідним JSON. Переконатися, що **Zabbix Actions** дійсно надсилають алерти, бо trigger != доставка повідомлення.

## Відкат

```bash
# mon, root
cp -a /usr/lib/zabbix/externalscripts/ups_megatec.py.bak-before-kwds /usr/lib/zabbix/externalscripts/ups_megatec.py
```

Відкотити template шляхом імпорту збереженої резервної копії. **Не використовувати Delete missing як спосіб відкату** без звіряння, які сутності він видалить. Restart Zabbix server для заміни external script зазвичай не потрібний.
