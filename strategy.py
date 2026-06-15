import patterns
from indicators import analyze_market

SERMAYE_USD = 100.0
MAX_KALDIRAC = 10
RISK_YUZDESI = 0.5
ATR_SL_CARPANI = 1.2
ATR_TP_CARPANI = 1.6

def _position_sizing(entry, stop, leverage=MAX_KALDIRAC):
    stop_dist_pct = abs(entry - stop) / entry
    notional = SERMAYE_USD * leverage
    risk_usd = notional * stop_dist_pct
    return notional, risk_usd

def evaluate(symbol, df):
    if df is None or len(df) < 60:
        return None
    market = analyze_market(df)
    found, pattern_dir = patterns.detect(df)
    if pattern_dir == 0 or not found:
        return None
    trend = market["trend"]
    rsi_state = market["rsi_state"]
    macd_state = market["macd_state"]
    direction = None
    reasons = []
    if pattern_dir > 0 and trend == "YUKSELIS" and rsi_state != "asiri alim" and macd_state == "pozitif":
        direction = "LONG"
        reasons.append("Boga formasyonu yukselis trendi ile hizali")
        reasons.append(f"RSI {market['rsi']} (asiri alim degil)")
        reasons.append("MACD pozitif (momentum yukari)")
    elif pattern_dir < 0 and trend == "DUSUS" and rsi_state != "asiri satim" and macd_state == "negatif":
        direction = "SHORT"
        reasons.append("Ayi formasyonu dusus trendi ile hizali")
        reasons.append(f"RSI {market['rsi']} (asiri satim degil)")
        reasons.append("MACD negatif (momentum asagi)")
    else:
        return None
    entry = market["price"]
    atr_val = market["atr"]
    if direction == "LONG":
        stop = entry - ATR_SL_CARPANI * atr_val
        target = entry + ATR_TP_CARPANI * atr_val
    else:
        stop = entry + ATR_SL_CARPANI * atr_val
        target = entry - ATR_TP_CARPANI * atr_val
    notional, risk_usd = _position_sizing(entry, stop)
    reward_usd = notional * abs(target - entry) / entry
    rr = reward_usd / risk_usd if risk_usd else 0
    strength = 1
    strength += min(len(found), 2)
    if market["vol_spike"]:
        strength += 1
        reasons.append("Hacim ortalamanin uzerinde (teyit)")
    if abs(market["trend_score"]) == 3:
        strength += 1
    strength = min(strength, 5)
    return {
        "symbol": symbol, "direction": direction, "entry": entry,
        "stop": stop, "target": target, "leverage": MAX_KALDIRAC,
        "notional": notional, "risk_usd": risk_usd, "reward_usd": reward_usd,
        "rr": rr, "strength": strength, "patterns": found,
        "reasons": reasons, "market": market,
    }

def format_signal(sig):
    arrow = "🟢 LONG (AL)" if sig["direction"] == "LONG" else "🔴 SHORT (SAT)"
    stars = "⭐" * sig["strength"]
    m = sig["market"]
    tf = sig.get("timeframe", "")
    tf_label = f"  ⏱ {tf}" if tf else ""
    lines = [
        f"{arrow}  —  {sig['symbol']}{tf_label}",
        f"Guc: {stars} ({sig['strength']}/5)",
        "",
        f"📊 Piyasa durumu: {m['trend']}",
        f"   RSI: {m['rsi']} ({m['rsi_state']}) | MACD: {m['macd_state']}",
        f"   Volatilite (ATR): %{m['atr_pct']}",
        "",
        f"🕯 Formasyon(lar): {', '.join(sig['patterns'])}",
        "",
        f"💵 Giris:  {sig['entry']:.6g}",
        f"🛑 Stop:   {sig['stop']:.6g}",
        f"🎯 Hedef:  {sig['target']:.6g}",
        f"⚖️ Kaldirac: {sig['leverage']}x | Pozisyon: ~{sig['notional']:.0f}$",
        "",
        f"📈 Tahmini kazanc: +{sig['reward_usd']:.2f}$",
        f"📉 Tahmini zarar:  -{sig['risk_usd']:.2f}$",
        f"   Risk/Odul: 1:{sig['rr']:.2f}",
        "",
        "🔎 Neden: " + "; ".join(sig["reasons"]),
        "",
        "⚠️ Yatirim tavsiyesi degildir. Sinyal olasilik temellidir; kayip riski gercektir.",
    ]
    return "\n".join(lines)
