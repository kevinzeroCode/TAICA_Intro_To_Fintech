#############################################################
# Problem 0: Find base point
def GetCurveParameters():
    # Certicom secp256-k1
    # Hints: https://en.bitcoin.it/wiki/Secp256k1
    _p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    _a = 0x0000000000000000000000000000000000000000000000000000000000000000
    _b = 0x0000000000000000000000000000000000000000000000000000000000000007
    _Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
    _Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
    _Gz = 0x0000000000000000000000000000000000000000000000000000000000000001
    _n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    _h = 0x01
    return _p, _a, _b, _Gx, _Gy, _Gz, _n, _h


#############################################################
# Problem 1: Evaluate 4G
def compute4G(G, callback_get_INFINITY):
    """Compute 4G"""
    twoG = G.double()
    fourG = twoG.double()
    """ Your code here """
    result = callback_get_INFINITY()
    return fourG


#############################################################
# Problem 2: Evaluate 5G
def compute5G(G, callback_get_INFINITY):
    """Compute 5G"""
    twoG = G.double()
    fourG = twoG.double()
    fiveG = fourG + G
    """ Your code here """
    result = callback_get_INFINITY()
    return fiveG


#############################################################
# Problem 3: Evaluate dG
# Problem 4: Double-and-Add algorithm
def double_and_add(n, point, callback_get_INFINITY):
    """Calculate n * point using the Double-and-Add algorithm."""

    """ Your code here """
    result = callback_get_INFINITY()
    num_doubles = 0
    num_additions = 0
    bits = bin(n)[2:]

    started = False 
    for bit in bits:
        if not started:
            if bit == '1':
                result = point       # 第一次遇到1，直接設成P，不算add
                started = True
            continue                 # 跳過這輪，不執行double
        # 之後的位元才真的開始
        result = result.double()
        num_doubles += 1
        if bit == '1':
            result = result + point
            num_additions += 1

    return result, num_doubles, num_additions


#############################################################
# Problem 5: Optimized Double-and-Add algorithm
def optimized_double_and_add(n, point, callback_get_INFINITY):
    """Optimized Double-and-Add algorithm that simplifies sequences of consecutive 1's."""

    """ Your code here """
    result = callback_get_INFINITY()
    if n == 0:
        return callback_get_INFINITY(), 0, 0

    num_doubles = 0
    num_additions = 0

    naf = []
    m = n
    while m > 0:
        if m & 1:
            ui = 2 - (m & 3)
            naf.append(ui)
            m -= naf[-1]
        else:
            naf.append(0)
        m >>= 1
    
    Curve = point.curve()
    p_mod = Curve.p()
    negP = -point

    started = False
    for ui in reversed(naf):
        if not started:
            if ui == 1:
                result = point
                started = True
                continue
            elif ui == -1:
                result = negP
                started = True
                continue
            else:
                # 還沒遇到第一個非零位，持續跳過
                continue

        # 之後每一位：先 double，再視 ui 做加/減
        result = result.double()
        num_doubles += 1
        if ui == 1:
            result = result + point
            num_additions += 1
        elif ui == -1:
            result = result + negP
            num_additions += 1

    return result, num_doubles, num_additions


#############################################################
# Problem 6: Sign a Bitcoin transaction with a random k and private key d
def sign_transaction(private_key, hashID, callback_getG, callback_get_n, callback_randint):
    """Sign a bitcoin transaction using the private key."""

    """ Your code here """
    G = callback_getG()
    n = callback_get_n()
    z = int(hashID, 16)

    def mul(k, P):
        result = None
        for b in bin(k)[2:]:          # MSB -> LSB
            if result is None:
                if b == '1':
                    result = P
                continue
            result = result.double()
            if b == '1':
                result = result + P
        return result

    while True:
        k = callback_randint(1, n - 1)
        if not (1 <= k < n):
            continue

        R = mul(k, G)
        r = R.x() % n
        if r == 0:
            continue

        k_inv = pow(k, -1, n)
        s = (k_inv * (z + r * private_key)) % n
        if s == 0:
            continue

        signature = (r, s)
        return signature


##############################################################
# Step 7: Verify the digital signature with the public key Q
def verify_signature(public_key, hashID, signature, callback_getG, callback_get_n, callback_get_INFINITY):
    """Verify the digital signature."""

    """ Your code here """
    G = callback_getG()
    n = callback_get_n()
    z = int(hashID, 16)
    r, s = signature

    # Step 2: 檢查 r, s 範圍
    if not (1 <= r < n and 1 <= s < n):
        return False

    # Step 3: w = s^{-1} mod n
    w = pow(s, -1, n)

    # Step 4: u1, u2
    u1 = (z * w) % n
    u2 = (r * w) % n

    # Step 5: X = u1*G + u2*public_key
    P1 = double_and_add(u1, G, callback_get_INFINITY)[0]
    P2 = double_and_add(u2, public_key, callback_get_INFINITY)[0]
    X = P1 + P2

    # 如果很保險想處理 X 是無窮遠點，也可以多寫一行：
    # if X == callback_get_INFINITY():
    #     return False

    # Step 6: 比較 X.x() mod n 是否等於 r
    v = X.x() % n
    infinity_point = callback_get_INFINITY()
    is_valid_signature = (v == r)

    return is_valid_signature

