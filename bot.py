import time
import traceback
from datetime import datetime, timezone

import ccxt
import pandas as pd
import requests

import strategy

TELEGRAM_TOKEN = "BURAYA_BOT_TOKENINI_YAZ"
TELEGRAM_CHAT_ID = "BURAYA_CHAT_ID_YAZ"

TIMEFRAMES = ["1h", "4h"]
TOP_N = 100
MIN_STRENGTH = 3
CANDLE_LIMIT = 120
QUOTE = "USDT"

TF_MINUTES = {"1h": 60, "4h": 240}

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

def fetch_ohlcv_df(symbol, timeframe):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=CANDLE_LIMIT)
    if not data or len(data) < 60:
        return None, None
    df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume"])
    last_closed_ts = df["ts"].iloc[-2]
    df = df.iloc[:-1].reset_index(drop=True)
    return df, last_closed_ts

def scan_once(symbols, timeframe):
    sent = 0
    for sym in symbols:
        try:
            df, candle_ts = fetch_ohlcv_df(sym, timeframe)
            if df is None:
                continue
            sig = strategy.evaluate(sym, df)
            if not sig or sig["strength"] < MIN_STRENGTH:
                continue
            key = (sym, timeframe)
            if _last_signal_candle.get(key) == candle_ts:
                continue
            _last_signal_candle[key] = candle_ts
            sig["timeframe"] = timeframe
            send_telegram(strategy.format_signal(sig))
            sent += 1
        except ccxt.BaseError:
            continue
        except Exception:
            print(f"[{sym} {timeframe}] beklenmeyen hata:\n{traceback.format_exc()}")
            continue
    return sent

def seconds_to_next_candle(minutes_per_candle):
    now = datetime.now(timezone.utc)
    mins_into = (now.hour * 60 + now.minute) % minutes_per_candle
    secs_into = mins_into * 60 + now.second
    return (minutes_per_candle * 60 - secs_into) + 5

def main():
    print(f"Bot basliyor... Borsa: Binance Futures | Zaman dilimleri: {', '.join(TIMEFRAMES)}")
    send_telegram(f"🤖 Sinyal botu aktif. Zaman dilimleri: {', '.join(TIMEFRAMES)} | top-{TOP_N} coin taraniyor.")
    symbols = get_top_volume_symbols()
    print(f"{len(symbols)} sembol takip ediliyor.")
    last_symbol_refresh = time.time()
    for tf in TIMEFRAMES:
        n = scan_once(symbols, tf)
        print(f"Ilk tarama [{tf}]: {n} sinyal gonderildi.")
    while True:
        waits = {tf: seconds_to_next_candle(TF_MINUTES[tf]) for tf in TIMEFRAMES}
        next_tf = min(waits, key=waits.get)
        wait = waits[next_tf]
        print(f"Sonraki kapanis: {next_tf} ({wait}s) bekleniyor...")
        time.sleep(wait)
        now_due = [tf for tf in TIMEFRAMES if seconds_to_next_candle(TF_MINUTES[tf]) > (TF_MINUTES[tf] * 60 - 30)]
        if not now_due:
            now_due = [next_tf]
        if time.time() - last_symbol_refresh > 6 * 3600:
            try:
                symbols = get_top_volume_symbols()
                last_symbol_refresh = time.time()
                print(f"Sembol listesi yenilendi: {len(symbols)} coin.")
            except Exception:
                pass
        for tf in now_due:
            try:
                n = scan_once(symbols, tf)
                stamp = datetime.now(timezone.utc).strftime("%H:%M UTC")
                print(f"[{stamp}] Tarama bitti [{tf}]: {n} sinyal.")
            except Exception:
                print(f"Tarama hatasi [{tf}]:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
