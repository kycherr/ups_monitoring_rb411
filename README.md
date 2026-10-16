# KWDS UPS Monitoring

Моніторинг Megatec UPS через **MikroTik RB411 RAW Serial TCP → Zabbix 8.0.0rc1**. Фінальна редакція **V10.7 від 2026-10-16**; базова версія збирача — **V10.5**. Це зафіксована версія проєкту, не доказ встановлення саме цих файлів на продуктивному сервері.

## Архітектура

```text
Megatec UPS (RS-232, 2400 8N1, Q1) ── RB411 (RAW TCP :9999)
                                         │
                                    IP network
                                         │
                           mon: Zabbix Server external check
                           /usr/lib/zabbix/externalscripts/ups_megatec.py
                                         │ JSON
                              dependent items + macros
                                         │
                             triggers / graphs / dashboard
```

- Один універсальний Python-скрипт, лише стандартна бібліотека Python 3; надсилає **тільки Q1**, не керує ДБЖ.
- Для кожного UPS створюється свій Zabbix host із власними макросами IP, порту, коефіцієнтів, ємності, порогів та інтервалу.
- **Не запускати паралельно** старий `ups_tcp_zabbix.py` (trapper) і новий External check на тому самому RAW Serial до перевірки конкуренції за порт.
- Відсоток SOC Li-ion НЕ обчислюється з Q1 як достовірний заряд; обчислення напруги комірки та автономності — **оцінки**.

## Вміст

| Шлях | Призначення |
|---|---|
| `collector/ups_megatec.py` | Універсальний колектор V10.5 без змін |
| `zabbix/KWDS_UPS_V10_7_Final_Zabbix8.yaml` | Актуальний шаблон: українські макроси, стан живлення текстом, дашборд |
| `docs/RB411.md` | Інвентаризація RB411, CLI перевірки, обмеження BLE |
| `docs/ARCHITECTURE.md` | Дані, розрахунки, масштабування, невизначеності |
| `docs/DEPLOYMENT.md` | Встановлення, імпорт, тест, відкат |
| `docs/TRIGGERS.md` | Пороги, сповіщення, перевірки |
| `docs/OPERATIONS.md` | Інциденти та діагностика |
| `examples/pochaiv.host-macros.example` | Відомі й запропоновані макроси хоста |
| `tests/test_collector.py` | Offline-тести парсера та форматування |

## Швидкий старт

```bash
python3 -m unittest discover -s tests -v
sudo -u zabbix python3 /usr/lib/zabbix/externalscripts/ups_megatec.py 172.16.0.25 9999 3
```

Точні кроки безпечного встановлення: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Характеристики RB411: [docs/RB411.md](docs/RB411.md).

## Статуси

**Перевірено історичним фактом:** `mon` отримував валідний JSON із `172.16.0.25:9999`, dependent items у Zabbix оновлювалися, `BatteryRaw 2.28 × 12 = 27.36 V`, відображався оцінний runtime. Відкриті питання: точність батарейних коефіцієнтів, стан CPU RB411 після останніх змін, реальний стан alert delivery і чи імпортований V10.5 зараз у продуктиві.

**Не зберігати в Git:** пароль, API token, backup RouterOS з ключами, SNMP community, приватні Zabbix exports із секретними macro values.

## Зміни V10.7

- У першій картці `ups.PowerStateText` відображає **МЕРЕЖА / БАТАРЕЯ / НИЗЬКИЙ ЗАРЯД / НЕВІДОМО**, без додатку `(1.00)`.
- `ups.PowerStateCode` лишився для діагностики та value mapping.
- Фон першої картки тепер статичний: Zabbix Item value не підтримує динамічний фон за порогами для текстових значень. Наявні тригери на роботу від АКБ і низький заряд продовжують діяти незалежно.
- Інші картки, графіки, макроси, пороги й Python не змінювалися щодо V10.6.

**Продуктивний імпорт V10.7 не підтверджений.**
