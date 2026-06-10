import time
import traceback
from datetime import datetime, timezone

import ccxt
import pandas as pd
import requests

import strategy

TELEGRAM_TOKEN = "BURAYA_BOT_TOKENINI_YAZ"
TELEGRAM_CHAT_ID = "BURAYA_CHAT_ID_YAZ"

TIMEFRAME = "15m"
TOP_N = 100
MIN_STRENGTH = 3
CANDLE_LIMIT = 120
QUOTE = "USDT"

exchange = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})
_last_signal_candle = {}

def send_telegram(text):
    if "BURAYA" in TELEGRAM_TOKEN or "BURAYA" in TELEGRAM_CHAT_ID:
        print("[TELEGRAM AYARLANMADI] Mesaj:\n" + text + "\n")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"Telegram gonderim hatasi: {e}")

def get_top_volume_symbols(n=TOP_N):
    tickers = exchange.fetch_tickers()
    rows = []
    for sym, t in tickers.items():
        if not sym.endswith(f"/{QUOTE}:{QUOTE}") and not sym.endswith(f"/{QUOTE}"):
            continue
        qv = t.get("quoteVolume") or 0
        if qv:
            rows.append((sym, qv))
    rows.sort(key=lambda x: x[1], reverse=True)
    return [s for s, _ in rows[:n]]

def fetch_ohlcv_df(symbol):
    data = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=CANDLE_LIMIT)
    if not data or len(data) < 60:
        return None, None
    df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume"])
    last_closed_ts = df["ts"].iloc[-2]
    df = df.iloc[:-1].reset_index(drop=True)
    return df, last_closed_ts

def scan_once(symbols):
    sent = 0
    for sym in symbols:
        try:
            df, candle_ts = fetch_ohlcv_df(sym)
            if df is None:
                continue
            sig = strategy.evaluate(sym, df)
            if not sig or sig["strength"] < MIN_STRENGTH:
                continue
            if _last_signal_candle.get(sym) == candle_ts:
                continue
            _last_signal_candle[sym] = candle_ts
            send_telegram(strategy.format_signal(sig))
            sent += 1
        except ccxt.BaseError:
            continue
        except Exception:
            print(f"[{sym}] beklenmeyen hata:\n{traceback.format_exc()}")
            continue
    return sent

def seconds_to_next_candle():
    now = datetime.now(timezone.utc)
    minutes = now.minute % 15
    secs_into = minutes * 60 + now.second
    return (15 * 60 - secs_into) + 5

def main():
    print("Bot basliyor... Borsa: Binance Futures | Timeframe: 15m")
    send_telegram("🤖 Scalp sinyal botu aktif. 15dk grafikte top-100 coin taraniyor.")
    symbols = get_top_volume_symbols()
    print(f"{len(symbols)} sembol takip ediliyor.")
    last_symbol_refresh = time.time()
    n = scan_once(symbols)
    print(f"Ilk tarama: {n} sinyal gonderildi.")
    while True:
        wait = seconds_to_next_candle()
        print(f"Sonraki mum kapanisina {wait}s bekleniyor...")
        time.sleep(wait)
        if time.time() - last_symbol_refresh > 6 * 3600:
            try:
                symbols = get_top_volume_symbols()
                last_symbol_refresh = time.time()
                print(f"Sembol listesi yenilendi: {len(symbols)} coin.")
            except Exception:
                pass
        try:
            n = scan_once(symbols)
            stamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
            print(f"[{stamp}] Tarama bitti: {n} sinyal.")
        except Exception:
            print(f"Tarama hatasi:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
