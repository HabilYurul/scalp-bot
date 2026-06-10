import numpy as np

def _body(o, c): return abs(c - o)
def _range(h, l): return max(h - l, 1e-9)
def _upper_wick(o, h, c): return h - max(o, c)
def _lower_wick(o, l, c): return min(o, c) - l
def _is_bull(o, c): return c > o
def _is_bear(o, c): return c < o

def doji(o, h, l, c):
    if _body(o, c) <= 0.1 * _range(h, l): return "Doji"
    return None

def hammer(o, h, l, c):
    body = _body(o, c); lw = _lower_wick(o, l, c); uw = _upper_wick(o, h, c)
    if body > 0 and lw >= 2 * body and uw <= 0.4 * body: return "Hammer (Cekic)"
    return None

def inverted_hammer(o, h, l, c):
    body = _body(o, c); lw = _lower_wick(o, l, c); uw = _upper_wick(o, h, c)
    if body > 0 and uw >= 2 * body and lw <= 0.4 * body: return "Inverted Hammer (Ters Cekic)"
    return None

def shooting_star(o, h, l, c, prev_bull):
    body = _body(o, c); uw = _upper_wick(o, h, c); lw = _lower_wick(o, l, c)
    if prev_bull and body > 0 and uw >= 2 * body and lw <= 0.4 * body: return "Shooting Star (Kayan Yildiz)"
    return None

def marubozu(o, h, l, c):
    body = _body(o, c)
    if body >= 0.95 * _range(h, l):
        return "Bullish Marubozu" if _is_bull(o, c) else "Bearish Marubozu"
    return None

def engulfing(o1, c1, o2, c2):
    if _is_bear(o1, c1) and _is_bull(o2, c2) and c2 >= o1 and o2 <= c1: return "Bullish Engulfing (Yutan Boga)"
    if _is_bull(o1, c1) and _is_bear(o2, c2) and o2 >= c1 and c2 <= o1: return "Bearish Engulfing (Yutan Ayi)"
    return None

def harami(o1, c1, o2, c2):
    big = (min(o1, c1), max(o1, c1)); small = (min(o2, c2), max(o2, c2))
    if small[0] >= big[0] and small[1] <= big[1] and _body(o2, c2) < _body(o1, c1):
        if _is_bear(o1, c1) and _is_bull(o2, c2): return "Bullish Harami (Hamile Boga)"
        if _is_bull(o1, c1) and _is_bear(o2, c2): return "Bearish Harami (Hamile Ayi)"
    return None

def piercing_dark_cloud(o1, h1, l1, c1, o2, h2, l2, c2):
    mid1 = (o1 + c1) / 2
    if _is_bear(o1, c1) and _is_bull(o2, c2) and o2 < c1 and c2 > mid1 and c2 < o1: return "Piercing Line (Delen Mum)"
    if _is_bull(o1, c1) and _is_bear(o2, c2) and o2 > c1 and c2 < mid1 and c2 > o1: return "Dark Cloud Cover (Kara Bulut Ortusu)"
    return None

def tweezer(o1, h1, l1, c1, o2, h2, l2, c2):
    tol = 0.0015
    if abs(l1 - l2) / max(l1, 1e-9) <= tol and _is_bear(o1, c1) and _is_bull(o2, c2): return "Tweezer Bottom (Cimbiz Dip)"
    if abs(h1 - h2) / max(h1, 1e-9) <= tol and _is_bull(o1, c1) and _is_bear(o2, c2): return "Tweezer Top (Cimbiz Tepe)"
    return None

def star(o1, c1, o2, h2, l2, c2, o3, c3):
    small2 = _body(o2, c2) <= 0.5 * _body(o1, c1)
    if _is_bear(o1, c1) and small2 and _is_bull(o3, c3) and c3 > (o1 + c1) / 2: return "Morning Star (Sabah Yildizi)"
    if _is_bull(o1, c1) and small2 and _is_bear(o3, c3) and c3 < (o1 + c1) / 2: return "Evening Star (Aksam Yildizi)"
    return None

def three_soldiers_crows(o1, c1, o2, c2, o3, c3):
    if _is_bull(o1, c1) and _is_bull(o2, c2) and _is_bull(o3, c3) and c1 < c2 < c3 and o2 > o1 and o3 > o2: return "Three White Soldiers (Uc Beyaz Asker)"
    if _is_bear(o1, c1) and _is_bear(o2, c2) and _is_bear(o3, c3) and c1 > c2 > c3 and o2 < o1 and o3 < o2: return "Three Black Crows (Uc Siyah Karga)"
    return None

BULLISH = {"Hammer (Cekic)", "Inverted Hammer (Ters Cekic)", "Bullish Marubozu", "Bullish Engulfing (Yutan Boga)", "Bullish Harami (Hamile Boga)", "Piercing Line (Delen Mum)", "Tweezer Bottom (Cimbiz Dip)", "Morning Star (Sabah Yildizi)", "Three White Soldiers (Uc Beyaz Asker)"}
BEARISH = {"Shooting Star (Kayan Yildiz)", "Bearish Marubozu", "Bearish Engulfing (Yutan Ayi)", "Bearish Harami (Hamile Ayi)", "Dark Cloud Cover (Kara Bulut Ortusu)", "Tweezer Top (Cimbiz Tepe)", "Evening Star (Aksam Yildizi)", "Three Black Crows (Uc Siyah Karga)"}

def detect(df):
    if len(df) < 4: return [], 0
    o = df["open"].values; h = df["high"].values; l = df["low"].values; c = df["close"].values
    found = []
    for fn in (doji, hammer, inverted_hammer, marubozu):
        r = fn(o[-1], h[-1], l[-1], c[-1])
        if r: found.append(r)
    r = shooting_star(o[-1], h[-1], l[-1], c[-1], _is_bull(o[-2], c[-2]))
    if r: found.append(r)
    for r in (engulfing(o[-2], c[-2], o[-1], c[-1]), harami(o[-2], c[-2], o[-1], c[-1]), piercing_dark_cloud(o[-2], h[-2], l[-2], c[-2], o[-1], h[-1], l[-1], c[-1]), tweezer(o[-2], h[-2], l[-2], c[-2], o[-1], h[-1], l[-1], c[-1])):
        if r: found.append(r)
    for r in (star(o[-3], c[-3], o[-2], h[-2], l[-2], c[-2], o[-1], c[-1]), three_soldiers_crows(o[-3], c[-3], o[-2], c[-2], o[-1], c[-1])):
        if r: found.append(r)
    bull = sum(1 for f in found if f in BULLISH); bear = sum(1 for f in found if f in BEARISH)
    net = (1 if bull > bear else -1 if bear > bull else 0)
    return found, net
