# auto_tune_bb_kd.py
# Grid-search BB+KD params on <csv>, write best back to myStrategy.py, then run rrEstimate.py
import sys, re, json, subprocess
from pathlib import Path
import pandas as pd

# 你可以依需求擴/縮網格
BB_WIN_GRID   = [18,20,22,24]
BB_K_GRID     = [1.8, 2.0, 2.2]
K_N_GRID      = [9,14]
KD_NEAR_GRID  = [0.3,0.5]
CONF_UP_GRID  = [1,2]
COOLDOWN_GRID = [0,2,3]
MINHOLD_GRID  = [0,1,2]

def patch(src, params):
    src = re.sub(r'STRATEGY\s*=\s*".*?"', 'STRATEGY = "BB_KD"', src)
    rep = {
        r'BB_WIN\s*=\s*\d+':        f'BB_WIN   = {params["BB_WIN"]}',
        r'BB_K\s*=\s*[\d\.]+':      f'BB_K     = {params["BB_K"]}',
        r'K_N\s*=\s*\d+':           f'K_N      = {params["K_N"]}',
        r'KD_NEAR\s*=\s*[\d\.]+':   f'KD_NEAR  = {params["KD_NEAR"]}',
        r'BB_CONFIRM_UP\s*=\s*\d+': f'BB_CONFIRM_UP   = {params["BB_CONFIRM_UP"]}',
        r'BB_COOLDOWN\s*=\s*\d+':   f'BB_COOLDOWN     = {params["BB_COOLDOWN"]}',
        r'BB_MIN_HOLD\s*=\s*\d+':   f'BB_MIN_HOLD     = {params["BB_MIN_HOLD"]}',
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
        print("Usage: python auto_tune_bb_kd.py <csv_path>"); sys.exit(1)
    csv_path = sys.argv[1]
    if not Path(csv_path).exists(): print("CSV not found:", csv_path); sys.exit(2)
    cols = pd.read_csv(csv_path, nrows=1).columns.tolist()
    if "Adj Close" not in cols: print('CSV must contain "Adj Close". Found:', cols); sys.exit(3)

    ms = Path("myStrategy.py")
    if not ms.exists(): print("myStrategy.py not found."); sys.exit(4)
    original = ms.read_text(encoding="utf-8")

    best = {"rr": -1e18}
    for bbwin in BB_WIN_GRID:
        for bbk in BB_K_GRID:
            for kn in K_N_GRID:
                for kdnear in KD_NEAR_GRID:
                    for cu in CONF_UP_GRID:
                        for cd in COOLDOWN_GRID:
                            for mh in MINHOLD_GRID:
                                params = {
                                    "BB_WIN": bbwin, "BB_K": bbk, "K_N": kn, "KD_NEAR": kdnear,
                                    "BB_CONFIRM_UP": cu, "BB_COOLDOWN": cd, "BB_MIN_HOLD": mh
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
    print("==== FINAL BEST (BB_KD) ====")
    print(json.dumps(best, indent=2))
    print(f"rr={best['rr']:.6f}")
    out = run_rr(csv_path)
    print(f"Final rr={out:.6f}" if out is not None else "Final rr run failed.")

if __name__ == "__main__":
    main()
