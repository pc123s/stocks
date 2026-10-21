# -*- coding: utf-8 -*-
"""下载东方财富行情数据: 上证指数(000001) 和 机器人ETF(562500)
- 5分钟K线: 2026-08-24 起(数据源实际保留起点约 2026-08-31)
- 日线K线: 2023-10-21 起(近三年)
输出: data/ 目录下 UTF-8(BOM) CSV, 可直接用 Excel 打开
"""
import urllib.request, json, time, csv, os
from datetime import date, timedelta

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(OUT, exist_ok=True)

UA = {'User-Agent': 'Mozilla/5.0'}
FIELDS2 = 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61'
HEADERS = ['时间', '开盘', '收盘', '最高', '最低', '成交量(手)', '成交额(元)', '振幅(%)', '涨跌幅(%)', '涨跌额', '换手率(%)']

def fetch(secid, klt, beg, end):
    """返回 (名称, 代码, [bar,...]), 每根 bar 为字段列表"""
    url = (f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}'
           f'&klt={klt}&fqt=0&lmt=300&beg={beg}&end={end}&fields1=f1,f2,f3,f4,f5,f6&fields2={FIELDS2}')
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read().decode('utf-8'))
            data = d.get('data')
            if not data:
                return None, None, []
            return data.get('name'), data.get('code'), [k.split(',') for k in (data.get('klines') or [])]
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))

def download(secid, klt, start, end, chunk_days, fname):
    rows, name, ndays = {}, None, 0
    d = start
    while d <= end:
        e = min(d + timedelta(days=chunk_days - 1), end)
        n, code, batch = fetch(secid, klt, d.strftime('%Y%m%d'), e.strftime('%Y%m%d'))
        name = n or name
        for r in batch:
            rows[r[0]] = r
        ndays += 1
        if klt == 5 or ndays % 5 == 0:
            print(f'  [{name or "?"}] {d} ~ {e}: +{len(batch)}')
        d = e + timedelta(days=1)
        time.sleep(0.2)
    path = os.path.join(OUT, fname)
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(HEADERS)
        for k in sorted(rows):
            w.writerow(rows[k])
    print(f'  saved -> {path}  ({len(rows)} rows)')
    return rows

TODAY = date.today()
print('TODAY =', TODAY)
print('== 5分钟K线 ==')
r1 = download('1.000001', 5, date(2026, 8, 24), TODAY, 3, '上证指数_5min.csv')
r2 = download('1.562500', 5, date(2026, 8, 24), TODAY, 3, '机器人ETF_562500_5min.csv')
print('== 日线K线(近三年) ==')
r3 = download('1.000001', 101, date(2023, 10, 21), TODAY, 30, '上证指数_daily.csv')
r4 = download('1.562500', 101, date(2023, 10, 21), TODAY, 30, '机器人ETF_562500_daily.csv')

print('\n== 汇总 ==')
for label, rows in [('上证指数 5min', r1), ('机器人ETF 5min', r2),
                    ('上证指数 daily', r3), ('机器人ETF daily', r4)]:
    ks = sorted(rows)
    print(f'{label}: {len(ks)} 根, {ks[0]} ~ {ks[-1]}')
