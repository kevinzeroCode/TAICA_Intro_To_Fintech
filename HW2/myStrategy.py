# myStrategy.py
# Two TI-only strategies (choose via STRATEGY):
#  1) "BB_KD"        : Bollinger Bands + Stochastic(KD) reversal (long-only)
#  2) "ATR_EMA_MACD" : ATR-like stops + EMA trend filter + MACD entries (long-only)
# Rules:
# - Uses Adj Close only. No ML/DP. Per-call O(1) or tiny slices. Compatible with rrEstimate.py.
# - Added robustness knobs: signal confirmation, cooldown days, min hold days, volatility filters.

import numpy as np

# =============== choose strategy here ===============
STRATEGY = "ATR_EMA_MACD"   # "BB_KD" or "ATR_EMA_MACD"
# ====================================================

# -------- BB_KD parameters (tunable) --------
BB_WIN   = 18     # Bollinger window
BB_K     = 1.8    # band width (std multiplier)
K_N      = 9      # RSV lookback (close-only RSV)
D_N      = 3      # D smoothing (we approximate D≈K to stay light)
KD_NEAR  = 0.3    # near-band tolerance in std units (0~0.5)
# Confirmation & position control (BB_KD)
BB_CONFIRM_UP   = 1   # require N consecutive days confirming entry
BB_COOLDOWN     = 0   # days to wait after exit before new entry
BB_MIN_HOLD     = 0   # minimum hold days (unless hard exit condition)
# -------------------------------------------

# ---- ATR_EMA_MACD parameters (tunable) ----
EMA_TREND   = 200
MACD_FAST   = 10
MACD_SLOW   = 24
MACD_SIGNAL = 8
ATR_WIN     = 10     # ATR proxy window (using |Δclose|)
ATR_SL_MULT = 2.5    # hard stop = entry - ATR_SL_MULT * ATR
ATR_TR_MULT = 2.0    # trailing stop = peak - ATR_TR_MULT * ATR
ATR_MIN     = 0.0    # minimal ATR proxy to allow entries (0.0=off; set small>0 to avoid low vol)
# Confirmation & position control (ATR_EMA_MACD)
AE_CONFIRM_UP   = 1  # entry confirmation days
AE_COOLDOWN     = 0  # cooldown days after exit
AE_MIN_HOLD     = 2  # minimum hold days
# -------------------------------------------

# ------------- persistent states -------------
_initialized = False
# EMA Trend
_trend_seeded = False
_trend_ema = 0.0
# MACD EMAs
_fast_seeded = False
_slow_seeded = False
_sig_seeded  = False
_fast_ema = 0.0
_slow_ema = 0.0
_sig_ema  = 0.0
_prev_hist = None
# KD prev diff
_prev_K_minus_D = None
# position & stops
_pos = 0
_entry = None
_peak  = None
_hold_days = 0
_cooldown = 0
# confirmations
_confirm_up = 0
_confirm_dn = 0
# --------------------------------------------

def _alpha(p): return 2.0 / (p + 1.0)
def _ema_seed_from_slice(arr, period):
    if len(arr) < period: return None
    return float(np.mean(arr[-period:]))
def _ema_update(x, prev, period, seeded):
    if not seeded: return float(x), True
    a = _alpha(period); return a*float(x)+(1.0-a)*prev, True

def _kd_from_close(close, k_n=9, d_n=3, prev_K=None):
    if len(close) < k_n: return None, None
    seg = close[-k_n:]; hi, lo = float(np.max(seg)), float(np.min(seg))
    rsv = 50.0 if hi==lo else (float(close[-1])-lo)/(hi-lo)*100.0
    K = (2.0/3.0)*((prev_K if prev_K is not None else rsv)) + (1.0/3.0)*rsv
    D = K  # light approx
    return K, D

def _bb_from_close(close, win=20, k=2.0):
    if len(close) < win: return None, None, None, None
    seg = close[-win:]; mu=float(np.mean(seg)); sd=float(np.std(seg, ddof=0))
    return mu, sd, mu+k*sd, mu-k*sd

def _atr_proxy_from_close(close, win=14):
    if len(close) < win+1: return None
    rets = np.abs(np.diff(close[-(win+1):])); return float(np.mean(rets))

def _reset_states():
    global _initialized, _trend_seeded, _trend_ema, _fast_seeded, _slow_seeded, _sig_seeded
    global _fast_ema, _slow_ema, _sig_ema, _prev_hist, _prev_K_minus_D
    global _pos, _entry, _peak, _hold_days, _cooldown, _confirm_up, _confirm_dn
    _initialized=True
    _trend_seeded=False; _trend_ema=0.0
    _fast_seeded=False; _slow_seeded=False; _sig_seeded=False
    _fast_ema=0.0; _slow_ema=0.0; _sig_ema=0.0; _prev_hist=None
    _prev_K_minus_D=None
    _pos=0; _entry=None; _peak=None
    _hold_days=0; _cooldown=0
    _confirm_up=0; _confirm_dn=0

def _logic_bb_kd(pastPriceVec, price):
    global _prev_K_minus_D, _pos, _entry, _peak, _hold_days, _cooldown, _confirm_up, _confirm_dn
    prices = np.append(pastPriceVec, price)
    action = 0

    mu, sd, upper, lower = _bb_from_close(prices, win=BB_WIN, k=BB_K)
    if mu is None or sd <= 1e-12:
        # update counters
        if _cooldown>0: _cooldown -= 1
        if _pos==1: _hold_days += 1
        return 0

    z = (price - mu) / sd
    near_lower = (z <= -(BB_K - KD_NEAR))
    near_upper = (z >=  (BB_K - KD_NEAR))

    K, D = _kd_from_close(prices, k_n=K_N, d_n=D_N, prev_K=None)
    kd_up = kd_dn = False
    if K is not None and D is not None and _prev_K_minus_D is not None:
        kd_up = (_prev_K_minus_D <= 0.0) and ((K-D) > 0.0)
        kd_dn = (_prev_K_minus_D >= 0.0) and ((K-D) < 0.0)

    # confirmation logic
    entry_cond = near_lower and kd_up
    exit_cond  = near_upper or kd_dn

    _confirm_up = _confirm_up + 1 if entry_cond else 0
    _confirm_dn = _confirm_dn + 1 if exit_cond  else 0

    # cooldown tick
    if _cooldown > 0: _cooldown -= 1

    if _pos == 0:
        if _cooldown == 0 and _confirm_up >= max(1, BB_CONFIRM_UP):
            action=1; _pos=1; _entry=float(price); _peak=float(price)
            _hold_days=0; _confirm_up=0
    else:
        # allow exit if min hold reached, or hard exit condition (kd_dn/near_upper)
        can_exit = (_hold_days >= max(0, BB_MIN_HOLD)) or exit_cond
        if can_exit and _confirm_dn >= 1:
            action=-1; _pos=0; _entry=None; _peak=None
            _cooldown = max(0, BB_COOLDOWN); _hold_days=0; _confirm_dn=0
        else:
            _peak = max(_peak, float(price)) if _peak is not None else float(price)
            _hold_days += 1

    _prev_K_minus_D = (K-D) if (K is not None and D is not None) else _prev_K_minus_D
    return action

def _logic_atr_ema_macd(pastPriceVec, price):
    global _trend_seeded, _trend_ema, _fast_seeded, _slow_seeded, _sig_seeded
    global _fast_ema, _slow_ema, _sig_ema, _prev_hist
    global _pos, _entry, _peak, _hold_days, _cooldown, _confirm_up, _confirm_dn

    p=float(price); prices=np.append(pastPriceVec, p); action=0

    # Trend EMA
    if not _trend_seeded and len(prices) >= EMA_TREND:
        seed=_ema_seed_from_slice(prices, EMA_TREND)
        if seed is not None: _trend_ema, _trend_seeded = float(seed), True
    if _trend_seeded: _trend_ema,_=_ema_update(p,_trend_ema,EMA_TREND,True)

    # MACD EMAs
    if not _fast_seeded and len(prices) >= MACD_FAST:
        seed=_ema_seed_from_slice(prices, MACD_FAST)
        if seed is not None: _fast_ema,_fast_seeded=float(seed),True
    if not _slow_seeded and len(prices) >= MACD_SLOW:
        seed=_ema_seed_from_slice(prices, MACD_SLOW)
        if seed is not None: _slow_ema,_slow_seeded=float(seed),True

    if _fast_seeded: _fast_ema,_=_ema_update(p,_fast_ema,MACD_FAST,True)
    if _slow_seeded: _slow_ema,_=_ema_update(p,_slow_ema,MACD_SLOW,True)
    if not (_fast_seeded and _slow_seeded):
        if _cooldown>0: _cooldown -= 1
        if _pos==1: _hold_days += 1
        return 0

    macd=_fast_ema-_slow_ema
    if not _sig_seeded: _sig_ema,_sig_seeded=macd,True
    else: _sig_ema,_=_ema_update(macd,_sig_ema,MACD_SIGNAL,True)
    hist=macd-_sig_ema

    hist_up = (_prev_hist is not None) and (_prev_hist <= 0.0) and (hist > 0.0)
    hist_dn = (_prev_hist is not None) and (_prev_hist >= 0.0) and (hist < 0.0)
    trend_ok  = (not _trend_seeded) or (p > _trend_ema)
    trend_bad = _trend_seeded and (p < _trend_ema)

    atr = _atr_proxy_from_close(prices, win=ATR_WIN)
    vol_ok = (atr is None) or (atr > ATR_MIN)

    hard_stop = trail_stop = False
    if _pos==1:
        _peak = max(_peak,p) if _peak is not None else p
        if atr is not None:
            hard_stop  = (_entry is not None) and (p <= _entry - ATR_SL_MULT*atr)
            trail_stop = (_peak  is not None) and (p <= _peak  - ATR_TR_MULT*atr)

    # confirmation and cooldown
    if _cooldown > 0: _cooldown -= 1

    entry_cond = vol_ok and trend_ok and (hist_up or hist > 0.0)
    exit_cond  = (hist_dn or trend_bad or hard_stop or trail_stop)

    _confirm_up = _confirm_up + 1 if entry_cond else 0
    _confirm_dn = _confirm_dn + 1 if exit_cond  else 0

    if _pos==0:
        if _cooldown==0 and _confirm_up >= max(1, AE_CONFIRM_UP):
            action=1; _pos=1; _entry=p; _peak=p; _hold_days=0; _confirm_up=0
    else:
        can_exit = (_hold_days >= max(0, AE_MIN_HOLD)) or hard_stop or trend_bad
        if can_exit and _confirm_dn >= 1:
            action=-1; _pos=0; _entry=None; _peak=None
            _cooldown = max(0, AE_COOLDOWN); _hold_days=0; _confirm_dn=0
        else:
            _hold_days += 1

    _prev_hist = hist
    return action

def myStrategy(pastPriceVec, currentPrice):
    global _initialized
    if len(pastPriceVec)==0: _reset_states()
    if STRATEGY=="BB_KD":
        return _logic_bb_kd(pastPriceVec, currentPrice)
    else:
        return _logic_atr_ema_macd(pastPriceVec, currentPrice)
