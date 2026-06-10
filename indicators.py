import numpy as np
import pandas as pd

def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50)

def macd(series, fast=12, slow=26, signal=9):
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def atr(df, period=14):
    high = df["high"]; low = df["low"]; close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()

def analyze_market(df):
    close = df["close"]
    ema20 = ema(close, 20)
    ema50 = ema(close, 50)
    rsi14 = rsi(close, 14)
    macd_line, signal_line, hist = macd(close)
    atr14 = atr(df, 14)
    last = -1
    score = 0
    if close.iloc[last] > ema20.iloc[last]: score += 1
    else: score -= 1
    if ema20.iloc[last] > ema50.iloc[last]: score += 1
    else: score -= 1
    if hist.iloc[last] > 0: score += 1
    else: score -= 1
    if score >= 2: trend = "YUKSELIS"
    elif score <= -2: trend = "DUSUS"
    else: trend = "YATAY"
    rsi_val = float(rsi14.iloc[last])
    if rsi_val >= 70: rsi_state = "asiri alim"
    elif rsi_val <= 30: rsi_state = "asiri satim"
    else: rsi_state = "notr"
    vol = df["volume"]
    vol_spike = bool(vol.iloc[last] > 1.5 * vol.rolling(20).mean().iloc[last])
    atr_val = float(atr14.iloc[last])
    atr_pct = atr_val / float(close.iloc[last]) * 100
    return {
        "trend": trend,
        "trend_score": score,
        "rsi": round(rsi_val, 1),
        "rsi_state": rsi_state,
        "macd_state": "pozitif" if hist.iloc[last] > 0 else "negatif",
        "vol_spike": vol_spike,
        "atr": atr_val,
        "atr_pct": round(atr_pct, 2),
        "price": float(close.iloc[last]),
    }
