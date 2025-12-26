# HW3: Elliptic Curve Cryptography & ECDSA

This project implements **Elliptic Curve Digital Signature Algorithm (ECDSA)** from scratch using pure Python. It focuses on the **secp256k1** curve, which is the standard elliptic curve used in Bitcoin and Ethereum.

## 🚀 Project Overview

The goal is to implement the core mathematical operations behind digital signatures without relying on external cryptographic libraries (like `cryptography` or `ecdsa`).

### Core Tasks Implemented:
1.  **Finite Field Arithmetic:** Modular inverse using Extended Euclidean Algorithm.
2.  **Elliptic Curve Arithmetic:**
    * Point Addition
    * Point Doubling
    * **Scalar Multiplication:** Implemented using the efficient **Double-and-Add algorithm** ($O(\log n)$ complexity).
3.  **ECDSA Scheme:**
    * **Signature Generation:** Creating $(r, s)$ from a message hash and private key.
    * **Signature Verification:** Validating the signature using the public key.

## 📂 File Description

* **`mySubmission.py`**: The core library containing all mathematical implementations:
    * `extended_gcd(a, b)`: Extended Euclidean Algorithm.
    * `inverse_mod(k, p)`: Modular multiplicative inverse.
    * `add_points(...)` / `double_point(...)`: Curve geometric operations.
    * `double_add_algorithm(...)`: Efficient scalar multiplication ($Q = d \cdot P$).
    * `sign_ecdsa(...)` & `verify_ecdsa(...)`: The signature logic.
* **`main.py`**: The testing script provided by the course. It sets up the **secp256k1** curve parameters, generates test cases, and verifies the correctness and performance of the submission.

## 🧮 Mathematical Background

The implementation is based on the curve equation:

$$y^2 \equiv x^3 + ax + b \pmod p$$

For **secp256k1**, the parameters are:
* $a = 0$
* $b = 7$
* $p = 2^{256} - 2^{32} - 977$

### Signature Verification Logic
To verify a signature $(r, s)$ for a message hash $z$, we calculate:

$$w = s^{-1} \pmod n$$
$$u_1 = z \cdot w \pmod n, \quad u_2 = r \cdot w \pmod n$$
$$(x, y) = u_1 \cdot G + u_2 \cdot Q$$

The signature is valid if $r \equiv x \pmod n$.

## 🛠️ Usage

To run the correctness and performance tests:

```bash
python main.py