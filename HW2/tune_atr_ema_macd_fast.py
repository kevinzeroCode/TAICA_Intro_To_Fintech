# tune_atr_ema_macd_fast.py
# Fast tuner for ATR+EMA+MACD without subprocess, no ML/DP.
# Strategy params are the globals in myStrategy.py (ATR_EMA_MACD branch).
#
# Usage:
#   python tune_atr_ema_macd_fast.py public.csv
#
import sys, json, random
from pathlib import Path
import importlib
import numpy as np
import pandas as pd

# ------------------------- helper: load CSV -------------------------
def load_adj_close(csv_path: Path) -> np.ndarray:
    df = pd.read_csv(csv_path)
    if "Adj Close" not in df.columns:
        raise ValueError(f'CSV must contain "Adj Close". Found: {list(df.columns)}')
    return df["Adj Close"].astype(float).values

# -------------------- in-process rr evaluator ----------------------
def evaluate_rr(adj: np.ndarray, params: dict) -> float:
    """
    Set myStrategy module-level constants, then run a single backtest loop
    that mirrors rrEstimate.py's logic (full in/out). Returns decimal rr.
    """
    import myStrategy as strat

    # select strategy & set constants
    strat.STRATEGY = "ATR_EMA_MACD"
    for k, v in params.items():
        setattr(strat, k, v)

    capital = 1000.0
    stock = 0.0
    total = 0.0

    # ensure internal states reset on first call (myStrategy already does this when len(past)==0)
    for i, p in enumerate(adj):
        past = adj[:i]
        act = strat.myStrategy(past, float(p))
        if i == 0:
            total = capital
        if act == 1 and stock == 0.0:
            stock = capital / p
            capital = 0.0
        elif act == -1 and stock > 0.0:
            capital = stock * p
            stock = 0.0
        total = capital + stock * p

    return (total - 1000.0) / 1000.0

# ------------------------- search utilities ------------------------
def clamp_int(x, lo, hi): return int(max(lo, min(hi, round(x))))

def neighborhood(params):
    """Generate small local tweaks around current params."""
    p = dict(params)
    nbrs = []

    # integer knobs
    for k, delta in [("EMA_TREND", 20), ("ATR_WIN", 2), ("MACD_FAST", 1), ("MACD_SLOW", 2), ("MACD_SIGNAL", 1),
                     ("AE_CONFIRM_UP", 1), ("AE_COOLDOWN", 1), ("AE_MIN_HOLD", 1)]:
        if k in p:
            for s in (-1, +1):
                q = dict(p)
                q[k] = clamp_int(p[k] + s*delta, 2, 500)
                nbrs.append(q)

    # float knobs
    for k, step in [("ATR_SL_MULT", 0.25), ("ATR_TR_MULT", 0.25), ("ATR_MIN", 1e-3)]:
        if k in p:
            for s in (-1.0, +1.0):
                q = dict(p); q[k] = max(0.0, p[k] + s*step)
                nbrs.append(q)

    # MACD constraint slow >= fast + 6
    filtered = []
    for q in nbrs:
        if q["MACD_SLOW"] < q["MACD_FAST"] + 6:
            q["MACD_SLOW"] = q["MACD_FAST"] + 6
        filtered.append(q)
    return filtered

def coarse_grid():
    # small, safe grid just to get a decent starting point
    for et in [180, 200, 220]:
        for aw in [10, 14, 20]:
            for sl in [1.0, 1.5, 2.0]:
                for tr in [1.5, 2.0, 2.5]:
                    for amin in [0.0, 1e-3]:
                        for f in [10, 12]:
                            for s in [24, 26]:
                                if s < f + 6: 
                                    s = f + 6
                                for sig in [7, 9]:
                                    for cu in [1, 2]:
                                        for cd in [0, 2, 3]:
                                            for mh in [0, 1, 2]:
                                                yield {
                                                    "EMA_TREND": et, "ATR_WIN": aw,
                                                    "ATR_SL_MULT": sl, "ATR_TR_MULT": tr, "ATR_MIN": amin,
                                                    "MACD_FAST": f, "MACD_SLOW": s, "MACD_SIGNAL": sig,
                                                    "AE_CONFIRM_UP": cu, "AE_COOLDOWN": cd, "AE_MIN_HOLD": mh
                                                }

def coordinate_descent(adj, start_params, max_passes=5):
    """Greedy coordinate descent with local neighborhood moves."""
    best = start_params
    best_rr = evaluate_rr(adj, best)
    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for cand in neighborhood(best):
            rr = evaluate_rr(adj, cand)
            if rr > best_rr:
                best, best_rr = cand, rr
                improved = True
    return best, best_rr

# ------------------------------ main ------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python tune_atr_ema_macd_fast.py <csv_path>")
        sys.exit(1)
    csv_path = Path(sys.argv[1]).resolve()
    adj = load_adj_close(csv_path)

    # Import myStrategy once
    sys.path.insert(0, str(Path.cwd()))
    importlib.invalidate_caches()
    import myStrategy  # noqa

    # 1) coarse grid to get seed
    seed = None
    seed_rr = -1e18
    tried = 0
    for params in coarse_grid():
        rr = evaluate_rr(adj, params)
        tried += 1
        if rr > seed_rr:
            seed, seed_rr = params, rr
            print(f"[SEED] rr={rr:.6f} params={json.dumps(params)}")

    # 2) coordinate descent around the seed
    best, best_rr = coordinate_descent(adj, seed, max_passes=5)
    print("==== CD BEST ====")
    print(json.dumps(best, indent=2)); print(f"rr={best_rr:.6f}")

    # 3) random restarts near the best
    for _ in range(10):
        jitter = dict(best)
        # small random perturbations
        jitter["EMA_TREND"]   = clamp_int(jitter["EMA_TREND"] + random.choice([-20,0,20]), 50, 500)
        jitter["ATR_WIN"]     = clamp_int(jitter["ATR_WIN"] + random.choice([-2,0,2]), 5, 60)
        jitter["MACD_FAST"]   = clamp_int(jitter["MACD_FAST"] + random.choice([-1,0,1]), 2, 30)
        jitter["MACD_SLOW"]   = clamp_int(max(jitter["MACD_SLOW"] + random.choice([-2,0,2]), jitter["MACD_FAST"]+6), 8, 60)
        jitter["MACD_SIGNAL"] = clamp_int(jitter["MACD_SIGNAL"] + random.choice([-1,0,1]), 2, 20)
        for k in ["ATR_SL_MULT","ATR_TR_MULT"]:
            jitter[k] = max(0.0, jitter[k] + random.choice([-0.25,0,0.25]))
        rr = evaluate_rr(adj, jitter)
        if rr > best_rr:
            best, best_rr = jitter, rr
            print(f"[RESTART↑] rr={rr:.6f} params={json.dumps(jitter)}")

    # 4) write back to myStrategy.py
    ms_path = Path("myStrategy.py")
    src = ms_path.read_text(encoding="utf-8")
    import re
    src = re.sub(r'STRATEGY\s*=\s*".*?"', 'STRATEGY = "ATR_EMA_MACD"', src)
    repl = {
        r'EMA_TREND\s*=\s*\d+':          f'EMA_TREND   = {best["EMA_TREND"]}',
        r'ATR_WIN\s*=\s*\d+':            f'ATR_WIN     = {best["ATR_WIN"]}',
        r'ATR_SL_MULT\s*=\s*[\d\.]+':    f'ATR_SL_MULT = {best["ATR_SL_MULT"]}',
        r'ATR_TR_MULT\s*=\s*[\d\.]+':    f'ATR_TR_MULT = {best["ATR_TR_MULT"]}',
        r'ATR_MIN\s*=\s*[\d\.eE\-]+':    f'ATR_MIN     = {best.get("ATR_MIN", 0.0)}',
        r'MACD_FAST\s*=\s*\d+':          f'MACD_FAST   = {best["MACD_FAST"]}',
        r'MACD_SLOW\s*=\s*\d+':          f'MACD_SLOW   = {best["MACD_SLOW"]}',
        r'MACD_SIGNAL\s*=\s*\d+':        f'MACD_SIGNAL = {best["MACD_SIGNAL"]}',
        r'AE_CONFIRM_UP\s*=\s*\d+':      f'AE_CONFIRM_UP   = {best["AE_CONFIRM_UP"]}',
        r'AE_COOLDOWN\s*=\s*\d+':        f'AE_COOLDOWN     = {best["AE_COOLDOWN"]}',
        r'AE_MIN_HOLD\s*=\s*\d+':        f'AE_MIN_HOLD     = {best["AE_MIN_HOLD"]}',
    }
    for pat, rep in repl.items():
        src = re.sub(pat, rep, src)
    ms_path.write_text(src, encoding="utf-8")

    print("==== FINAL (written to myStrategy.py) ====")
    print(json.dumps(best, indent=2)); print(f"rr={best_rr:.6f}")
    print("Now you can run:  python rrEstimate.py", csv_path.name)

if __name__ == "__main__":
    main()
