# auto_tune_atr_ema_macd.py
# Grid-search ATR/EMA/MACD params on <csv>, write best back, then run rrEstimate.py
import sys, re, json, subprocess
from pathlib import Path
import pandas as pd

EMA_TREND_GRID   = [160,180,200,220]
ATR_WIN_GRID     = [10,14,20]
ATR_SL_MULT_GRID = [1.0, 1.5, 2.0]
ATR_TR_MULT_GRID = [1.5, 2.0, 2.5]
ATR_MIN_GRID     = [0.0, 1e-3]      # 低波動期過濾(可關閉0.0)
MACD_FAST_GRID   = [10,12]
MACD_SLOW_GRID   = [24,26]
MACD_SIGNAL_GRID = [7,9]
CONF_UP_GRID     = [1,2]
COOLDOWN_GRID    = [0,2,3]
MINHOLD_GRID     = [0,1,2]

def valid(f,s): return (s >= f + 6)

def patch(src, params):
    src = re.sub(r'STRATEGY\s*=\s*".*?"', 'STRATEGY = "ATR_EMA_MACD"', src)
    rep = {
        r'EMA_TREND\s*=\s*\d+':          f'EMA_TREND   = {params["EMA_TREND"]}',
        r'ATR_WIN\s*=\s*\d+':            f'ATR_WIN     = {params["ATR_WIN"]}',
        r'ATR_SL_MULT\s*=\s*[\d\.]+':    f'ATR_SL_MULT = {params["ATR_SL_MULT"]}',
        r'ATR_TR_MULT\s*=\s*[\d\.]+':    f'ATR_TR_MULT = {params["ATR_TR_MULT"]}',
        r'ATR_MIN\s*=\s*[\d\.eE\-]+':    f'ATR_MIN     = {params["ATR_MIN"]}',
        r'MACD_FAST\s*=\s*\d+':          f'MACD_FAST   = {params["MACD_FAST"]}',
        r'MACD_SLOW\s*=\s*\d+':          f'MACD_SLOW   = {params["MACD_SLOW"]}',
        r'MACD_SIGNAL\s*=\s*\d+':        f'MACD_SIGNAL = {params["MACD_SIGNAL"]}',
        r'AE_CONFIRM_UP\s*=\s*\d+':      f'AE_CONFIRM_UP   = {params["AE_CONFIRM_UP"]}',
        r'AE_COOLDOWN\s*=\s*\d+':        f'AE_COOLDOWN     = {params["AE_COOLDOWN"]}',
        r'AE_MIN_HOLD\s*=\s*\d+':        f'AE_MIN_HOLD     = {params["AE_MIN_HOLD"]}',
    }
    for pat, s in rep.items(): src = re.sub(pat, s, src)
    return src

def run_rr(csv_path):
    out = subprocess.check_output([sys.executable, "rrEstimate.py", csv_path],
                                  stderr=subprocess.STDOUT, text=True)
    m = re.search(r'rr\s*=\s*([-+]?\d+(\.\d+)?)\s*%?', out)
    if not m: return None
    val = float(m.group(1))
    return val/100.0 if out.strip().endswith("%") or abs(val)>1.5 else val

def main():
    if len(sys.argv)<2:
        print("Usage: python auto_tune_atr_ema_macd.py <csv_path>"); sys.exit(1)
    csv_path = sys.argv[1]
    if not Path(csv_path).exists(): print("CSV not found:", csv_path); sys.exit(2)
    cols = pd.read_csv(csv_path, nrows=1).columns.tolist()
    if "Adj Close" not in cols: print('CSV must contain "Adj Close". Found:', cols); sys.exit(3)

    ms = Path("myStrategy.py")
    if not ms.exists(): print("myStrategy.py not found."); sys.exit(4)
    original = ms.read_text(encoding="utf-8")

    best = {"rr": -1e18}
    for et in EMA_TREND_GRID:
        for aw in ATR_WIN_GRID:
            for sl in ATR_SL_MULT_GRID:
                for tr in ATR_TR_MULT_GRID:
                    for amin in ATR_MIN_GRID:
                        for f in MACD_FAST_GRID:
                            for s in MACD_SLOW_GRID:
                                if not valid(f,s): continue
                                for sig in MACD_SIGNAL_GRID:
                                    for cu in CONF_UP_GRID:
                                        for cd in COOLDOWN_GRID:
                                            for mh in MINHOLD_GRID:
                                                params = {
                                                    "EMA_TREND": et, "ATR_WIN": aw,
                                                    "ATR_SL_MULT": sl, "ATR_TR_MULT": tr, "ATR_MIN": amin,
                                                    "MACD_FAST": f, "MACD_SLOW": s, "MACD_SIGNAL": sig,
                                                    "AE_CONFIRM_UP": cu, "AE_COOLDOWN": cd, "AE_MIN_HOLD": mh
                                                }
                                                patched = patch(original, params)
                                                ms.write_text(patched, encoding="utf-8")
                                                try:
                                                    rr = run_rr(csv_path)
                                                except subprocess.CalledProcessError as e:
                                                    print("rrEstimate failed:\n", e.output); continue
                                                if rr is not None and rr > best["rr"]:
                                                    best = {"rr": rr, **params}
                                                    print(f"[BEST so far] rr={rr:.6f} params={json.dumps(params)}", flush=True)

    if best["rr"] <= -1e17:
        print("No valid combo found. Restoring original.")
        ms.write_text(original, encoding="utf-8"); sys.exit(5)
    final_src = patch(original, best)
    ms.write_text(final_src, encoding="utf-8")
    print("==== FINAL BEST (ATR_EMA_MACD) ====")
    print(json.dumps(best, indent=2))
    print(f"rr={best['rr']:.6f}")
    out = run_rr(csv_path)
    print(f"Final rr={out:.6f}" if out is not None else "Final rr run failed.")

if __name__ == "__main__":
    main()
