import requests
import pandas as pd
import time
import datetime as dt
from keep_alive import keep_alive
keep_alive()

# 🔹 텔레그램 설정
bot_token1 = '6090575536:AAFvYG92OwqX71i3IkcfxMOEN0emgXuq3wE'
chat_id1 = '5092212639'
telegram_url1 = f'https://api.telegram.org/bot{bot_token1}/sendMessage'

def send_message(text):
    requests.post(telegram_url1, data={'chat_id': chat_id1, 'text': text})

# 🔹 볼린저 밴드 상단 계산
def calc_bbu(df):
    if len(df) < 100:
        return None
    ma = df['close'].rolling(100).mean().iloc[-1]
    std = df['close'].rolling(100).std().iloc[-1]
    return ma + 2 * std

# 🔹 Bybit USDT 선물 종목 리스트 가져오기 (최적화됨)
def get_bybit_usdt_futures():
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    res = requests.get(url)
    data = res.json()

    symbols = []
    for item in data.get("result", {}).get("list", []):
        if item["symbol"].endswith("USDT"):  # USDT 마진 선물만 필터링
            symbols.append(item["symbol"])

    return sorted(symbols)

# 🔹 Bybit 현재가
def get_bybit_price(symbol):
    try:
        url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol}"
        res = requests.get(url)
        return float(res.json()['result']['list'][0]['lastPrice'])
    except:
        return None

# 🔹 Bybit OHLCV (캔들)
def get_bybit_ohlcv(symbol, interval="60", limit=120):
    try:
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={interval}&limit={limit}"
        res = requests.get(url)
        data = res.json()
        ohlcv_list = data.get('result', {}).get('list', [])
        df = pd.DataFrame(ohlcv_list)
        df.columns = ['timestamp','open','high','low','close','volume','turnover']
        df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df
    except:
        return pd.DataFrame()

# 🔹 USDT 선물 종목 확인
bybit_usdt_futures = get_bybit_usdt_futures()
send_message(f"📊 Bybit USDT 선물 종목 수: {len(bybit_usdt_futures)}개\n예시: {', '.join(bybit_usdt_futures[:10])}")

# 🔹 감시 시작
send_message("📡 Bybit USDT 선물 감시 시작 (1시간, 4시간, 일봉 기준)")

while True:
    try:
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print("⏰", now)

        for symbol in bybit_usdt_futures:
            price = get_bybit_price(symbol)
            if price is None:
                continue

            df60 = get_bybit_ohlcv(symbol, interval="60")
            df240 = get_bybit_ohlcv(symbol, interval="240")
            df_day = get_bybit_ohlcv(symbol, interval="D")

            if df60.empty or df240.empty or df_day.empty:
                continue

            bbu60 = calc_bbu(df60)
            bbu240 = calc_bbu(df240)
            bbu_day = calc_bbu(df_day)

            if None not in [bbu60, bbu240, bbu_day] and price > bbu60 and price > bbu240 and price > bbu_day:
                send_message(f"[🚀 Bybit 선물] {symbol} 현재가: {price:.2f} (BB 상단 돌파)")

            time.sleep(0.3)  # API 제한 방지

        time.sleep(600)  # 10분 간격

    except Exception as e:
        send_message(f"❌ 오류 발생: {e}")
        time.sleep(10)
