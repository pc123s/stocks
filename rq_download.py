# -*- coding: utf-8 -*-
"""用 rqdatac 下载近三年 5 分钟K线: 上证指数(000001.XSHG) + 机器人ETF(562500.XSHG)

用法(需先拿到 RQData 试用 License Key 和 token):
  方式1(推荐): 写入 rq_credentials.txt 第3行=License Key, 第4行=token
  方式2: python rq_download.py <license_key> <token>
运行时需设置代理环境变量(本机直连外网不通):
  RQDATAC_PROXY="http://proxyhk.zte.com.cn:80" python rq_download.py

输出: data/rq_上证指数_5min.csv, data/rq_机器人ETF_562500_5min.csv
"""
import rqdatac, sys, csv, os, time
import pandas as pd
from datetime import date, timedelta

CRED = r'D:/stock/ETF/rq_credentials.txt'
OUT = r'D:/stock/ETF/data'

def read_cred():
    try:
        lines = [l.strip() for l in open(CRED, encoding='utf-8').read().splitlines() if l.strip()]
        if len(lines) >= 4:
            return lines[2], lines[3]
    except Exception:
        pass
    return None, None

license_key, token = read_cred()
if not license_key and len(sys.argv) >= 3:
    license_key, token = sys.argv[1], sys.argv[2]
if not license_key:
    print('缺少 License Key/token: 请写入 rq_credentials.txt 第3、4行, 或作为命令行参数传入')
    sys.exit(1)

rqdatac.init(username=license_key, password=token, connect_timeout=15, timeout=120)
print('rqdatac 登录成功')

SYMBOLS = {
    '000001.XSHG': ('上证指数', 'rq_上证指数_5min.csv'),
    '562500.XSHG': ('机器人ETF', 'rq_机器人ETF_562500_5min.csv'),
}
START = date(2023, 10, 21)
END = date(2026, 10, 21)

for sym, (label, fname) in SYMBOLS.items():
    print(f'== {label} ({sym}) ==')
    frames = []
    d = START
    while d <= END:
        e = min(d + timedelta(days=30), END)
        try:
            df = rqdatac.get_price(sym, start_date=d.isoformat(), end_date=e.isoformat(),
                                   frequency='5m',
                                   fields=['open', 'high', 'low', 'close', 'volume', 'total_turnover'])
            if len(df):
                frames.append(df)
                print(f'  {d} ~ {e}: {len(df)} rows')
            else:
                print(f'  {d} ~ {e}: 0 rows (可能非交易日或超出试用范围)')
        except Exception as ex:
            print(f'  {d} ~ {e}: ERR {type(ex).__name__} {str(ex)[:120]}')
        d = e + timedelta(days=1)
        time.sleep(1)

    if not frames:
        print(f'  !! {label}: 没有取到任何数据')
        continue
    merged = pd.concat(frames)
    merged = merged[~merged.index.duplicated(keep='last')].sort_index()
    print(f'  total: {len(merged)} rows, {merged.index[0]} ~ {merged.index[-1]}')

    # 计算涨跌幅/振幅(相对前一根bar收盘)
    prev_close = merged['close'].shift(1)
    pct = (merged['close'] - prev_close) / prev_close * 100
    amp = (merged['high'] - merged['low']) / prev_close * 100
    chg = merged['close'] - prev_close

    path = os.path.join(OUT, fname)
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['时间', '开盘', '收盘', '最高', '最低', '成交量', '成交额(元)',
                    '振幅(%)', '涨跌幅(%)', '涨跌额'])
        for ts, row in merged.iterrows():
            w.writerow([
                ts.strftime('%Y-%m-%d %H:%M:%S'),
                row['open'], row['close'], row['high'], row['low'],
                row['volume'], row['total_turnover'],
                round(amp[ts], 2), round(pct[ts], 2), round(chg[ts], 4),
            ])
    print(f'  saved -> {path}')
