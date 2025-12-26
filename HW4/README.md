# HW4: Multi-Asset Portfolio Selection Strategy

This project implements a stock selection strategy that manages a portfolio of multiple stocks. Unlike single-asset trading, this algorithm analyzes a matrix of stock prices to rank and select the best candidates for the daily portfolio.

## 🚀 Project Overview

The goal is to allocate capital efficiently among a pool of stocks to maximize the total return. The system simulates an **Open-Price Trading** environment where decisions made today are executed at the next day's opening price.

* **Data:** `priceMat0992.txt` (Matrix of Open, High, Low, Close prices for multiple stocks).
* **Objective:** Select a subset of $K$ stocks to hold each day.
* **Mechanism:** Daily rebalancing based on historical price momentum/reversion.

## 📂 File Description

* **`myAction.py`**: The user-defined strategy.
    * Input: A matrix of past prices (`priceMat`) and transaction fee rate.
    * Output: A list of indices representing the stocks to hold.
    * **Logic:** Implements a ranking mechanism (likely based on Rate of Change or Mean Reversion) to pick top-performing or oversold candidates.
* **`rrEstimateOpen.py`**: The backtesting engine.
    * Simulates the market day-by-day.
    * Calculates the Return on Investment (ROI) accounting for transaction fees.
* **`priceMat0992.txt`**: The dataset containing historical price data for the stock pool.

## 🧠 Strategy Logic

The `myAction` function operates on the following principle:

1.  **Window Analysis:** It looks back at the past $N$ days of price history.
2.  **Performance Ranking:** Calculates the percentage change (or other metrics) for every stock in the pool.
3.  **Selection:** * Sorts the stocks based on the calculated metric.
    * Selects the top $K$ stocks (e.g., buying the "winners" for momentum or "losers" for mean reversion).
4.  **Rebalancing:** Updates the portfolio composition daily.

## 🛠️ Usage

To run the backtest and see the annualized return:

```bash
python rrEstimateOpen.py