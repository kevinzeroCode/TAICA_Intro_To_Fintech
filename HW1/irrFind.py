def irrFind(cashFlowVec, cashFlowPeriod, compoundPeriod):
    tol=1e-13
    max_iter=100
    # 每年複利次數 m（例如月複利 m=12、季複利 m=4、年複利 m=1）
    # 每兩筆現金流之間跨越的複利期數 d
    def npv(r):
        m = 12.0 / compoundPeriod
        d = float(cashFlowPeriod) / float(compoundPeriod)
        base = 1.0 + r / m               # 每個「複利期」的名目利率
        step = base ** d                  # 相鄰兩筆現金流間的成長因子
        inv = 1.0 / step                  # 折現一步的因子
        factor = 1.0                      # i=0 時折現因子為 1
        s = 0.0
        # NPV = Σ CF_i / (1 + r/m)^{m * (i * cashFlowPeriod/12)}
        #     = Σ CF_i * (1/step)^i
        for i, c in enumerate(cashFlowVec):
            if i > 0:
                factor *= inv
            s += c * factor
        return s

    a, b = -0.1, 0.1
    fa, fb = npv(a), npv(b)

    if fa == 0.0:
        return a
    if fb == 0.0:
        return b

    # 若有夾擊到根，優先用二分法（穩）
    if fa * fb < 0.0:
        lo, hi = a, b
        flo, fhi = fa, fb
        for _ in range(max_iter):
            mid = 0.5 * (lo + hi)
            fm = npv(mid)
            if abs(fm) < tol or (hi - lo) < tol:
                return mid
            if flo * fm <= 0.0:
                hi, fhi = mid, fm
            else:
                lo, flo = mid, fm
        return 0.5 * (lo + hi)

    # 否則用「區間內割線法」保底嘗試
    x0, x1 = a, b
    f0, f1 = fa, fb
    for _ in range(max_iter):
        denom = (f1 - f0)
        if abs(denom) < 1e-18:
            break
        x2 = x1 - f1 * (x1 - x0) / denom
        # 夾回合法定區間，避免跳出 [-0.1, 0.1]
        if x2 < a: x2 = a
        if x2 > b: x2 = b
        f2 = npv(x2)
        if abs(f2) < tol:
            return x2
        x0, f0, x1, f1 = x1, f1, x2, f2

    # 最後保底：回傳中點（理論上很少走到這裡）
    return (a + b) * 0.5