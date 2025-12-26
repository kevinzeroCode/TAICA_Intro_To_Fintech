# HW2: Automated Trading Strategy & Parameter Tuning

This project implements a quantitative trading strategy using various **Technical Indicators**. The goal is to maximize the Return on Investment (ROI) by automatically tuning strategy parameters based on historical price data.

## 🚀 Project Overview

The core objective is to determine the optimal **Entry (Buy)** and **Exit (Sell)** points for a given stock/ETF using algorithmic trading logic.

* **Data Source:** `public.csv` (Historical Open, High, Low, Close, Volume data).
* **Evaluation Metric:** Annualized Return Rate (RR).
* **Optimization Method:** Exhaustive Search (Grid Search) & Heuristic Tuning.

## 📂 File Description

### 1. Core Strategy & Evaluation
* **`myStrategy.py`**: The main strategy logic. It analyzes the price data and returns a trading signal (`1` for Buy, `-1` for Sell, `0` for Hold).
* **`rrEstimate.py`**: The evaluator script. It loads `public.csv`, executes `myStrategy.py`, and calculates the final Return Rate to score the strategy.

### 2. Parameter Tuning (Optimization)
Scripts used to find the best parameters for different indicator combinations:

* **`bestParamByExhaustiveSearch.py`**: Implements a brute-force approach to iterate through all possible parameter combinations to find the global maximum.
* **`auto_tune_bb_kd.py`**: Specialized tuner for **Bollinger Bands (BB)** and **Stochastic Oscillator (KD)** strategy.
* **`auto_tune_atr_ema_macd.py`**: Specialized tuner for **ATR + EMA + MACD** trend-following strategy.
* **`tune_atr_ema_macd_fast.py`**: An optimized version of the tuning script, likely designed for faster execution (performance optimized).

### 3. Data
* **`public.csv`**: The dataset used for backtesting and training the parameters.

## 📊 Technical Indicators Used

The strategies explore combinations of the following indicators:
* **Trend Indicators:** EMA (Exponential Moving Average), MACD (Moving Average Convergence Divergence).
* **Volatility Indicators:** ATR (Average True Range), Bollinger Bands (BB).
* **Momentum Indicators:** KD (Stochastic Oscillator).

## 🛠️ Usage

### To Run the Strategy Evaluation
To see how the current strategy performs on the public dataset:

```bash
python rrEstimate.py
```
### To Run Parameter Tuning
To search for optimal parameters (Note: This may take time depending on the search space):

```bash
# Example: Tune BB and KD parameters
python auto_tune_bb_kd.py

# Example: Tune MACD/ATR parameters
python tune_atr_ema_macd_fast.py
```