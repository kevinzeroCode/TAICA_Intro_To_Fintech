# HW1: IRR Calculator

This project calculates the **Internal Rate of Return (IRR)** using numerical analysis methods. It determines the interest rate that makes the Net Present Value (NPV) of a series of cash flows equal to zero.

## 🚀 Features

* **NPV Calculation:** Computes Net Present Value based on cash flows, periods, and compounding frequency.
* **Hybrid Numerical Method:**
    * **Bisection Method:** Used primarily for stability when the root is bracketed.
    * **Secant Method:** Used for faster convergence within the interval.
* **Precision:** Iterates until the error is within a tolerance of `1e-13`.

## 📂 Files

* `goMain.py`: Entry point. Handles input parsing and calling the solver.
* `irrFind.py`: Core logic. Contains the `irrFind` function and numerical methods.

## 🛠️ Usage

### Input Format
The program reads from standard input (`stdin`). Each line should contain:
`[CashFlow_1] ... [CashFlow_N] [CashFlowPeriod] [CompoundPeriod]`

* The last two numbers are `CashFlowPeriod` and `CompoundPeriod`.
* The preceding numbers are the cash flow vector.

### Running the Code

```bash
# Run with input redirection
python goMain.py < input.txt

# Or save output to a file
python goMain.py < input.txt > output.txt