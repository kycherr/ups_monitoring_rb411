# Дані та формули

## Конкретні ключі

Збір: `ups.InputVoltage`, `ups.OutputVoltage`, `ups.UpsLoad`, `ups.UpsFreq`, `ups.UpsTemp`, `ups.UpsStatus`, `ups.OnBattery`, `ups.BatteryLow`, `ups.BatteryRaw`, `ups.FaultVoltage`, `ups.StatusBits`.

Залежні/розраховані в Zabbix: `ups.BatteryVoltage`, `ups.CellVoltageEstimated`, `ups.OutputPowerEstimated`, `ups.CapacityConfigured`, `ups.RuntimeEstimated`, `ups.RuntimeFormatted`, `ups.PowerStateCode`. `ups.BatteryCharge` зарезервований і **SOC не калібровано**.

- `BatteryRaw`: поле Megatec, в V10.5 округлення в Python до сотих; `2.2` у JSON дорівнює `2.20` при форматуванні UI.
- `BatteryVoltage = BatteryRaw × {$UPS.BATTERY.MULTIPLIER}`. Для Почаєва 2.28 × 12 = 27.36 V. Калібрування множника по вимірюванню шини потрібне.
- `CellVoltageEstimated = BatteryRaw × {$UPS.CELL.MULTIPLIER}`. Для прикладу 2.20 × 1.875 = 4.125 V, UI округляє до 4.13 V; **не є показником реальної окремої комірки BMS**.
- `OutputPowerEstimated ≈ {$UPS.POWER.RATED.W} × ups.UpsLoad / 100`. При 1000 W і 37% ≈ 370 W. Перевірити, що номінал справді **W**, а не VA.
- `RuntimeEstimated`: задана в YAML нелінійна модель із `CAPACITY`, `BATTERY.VOLT.MIN/MAX`, `USABLE`, `EFF`, `OutputPowerEstimated`, вихід у годинах. `RuntimeFormatted` перетворює на `N год M хв`. Крива емпірична (exponent 1.5), для змішаних 6S/7S Li-ion похибка може бути великою.
- `PowerStateCode`: 0 невідомо, 1 мережа, 2 батарея, 3 battery low; UI value mapping українською.

## Масштабування

Один template і один ExternalScript для багатьох UPS. На кожний створювати **окремий Zabbix host**, настроювати IP/порт, пороги й батарейні макроси. Навантаження polling оцінювати за фактичною тривалістю викликів і `StartExternalPollers`; існує ризик одночасних підключень до RAW Serial для одного UPS. Інтервал 10m означає, що швидка зміна стану не гарантовано виявиться раніше наступного успішного опитування.

## Стан перевірок

**Підтверджено з історії:** скрипт повертав валідний JSON за 0.398 s, Zabbix відображав напругу, навантаження, частоту, температуру, обчислював напругу батареї, пізніше показував `9 год 31 хв` у dashboard. Збої `Connection refused`, `Invalid Q1 response` були, остаточну кореневу причину не підтверджено. Нові V10.5 files були локально перевірені, але поточне розгортання не підтверджено.
