import sys
import numpy as np
import pandas as pd

# Global variables to store MACD history
macd_history = []

# Decision of the current day by the current price, with MACD parameters
def myStrategy(pastPriceVec, currentPrice, fast_period, slow_period, signal_period):
    global macd_history
    
    # Reset MACD history if starting fresh (dataLen = 0)
    if len(pastPriceVec) == 0:
        macd_history = []
    
    action = 0  # action=1(buy), -1(sell), 0(hold), with 0 as the default action
    dataLen = len(pastPriceVec)
    
    if dataLen < slow_period:
        return action
    
    # Calculate EMA function
    def calculate_ema(data, period):
        if len(data) < period:
            return np.mean(data) if len(data) > 0 else 0
        
        alpha = 2 / (period + 1)
        ema = data[0]  # Initialize with first value
        for price in data[1:]:
            ema = alpha * price + (1 - alpha) * ema
        return ema
    
    # Calculate current MACD
    prices = np.append(pastPriceVec, currentPrice)
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)
    macd_line = fast_ema - slow_ema
    
    # Update MACD history
    macd_history.append(macd_line)
    
    # Need at least signal_period MACD values to calculate signal line
    if len(macd_history) < signal_period:
        return action
    
    # Calculate signal line (EMA of MACD)
    signal_line = calculate_ema(macd_history, signal_period)
    
    # Get previous values for crossover detection
    if len(macd_history) >= signal_period + 1:
        prev_signal_line = calculate_ema(macd_history[:-1], signal_period)
        prev_macd_line = macd_history[-2]
        
        # Standard MACD crossover strategy
        # Buy when MACD crosses above signal line
        if macd_line > signal_line and prev_macd_line <= prev_signal_line:
            action = 1
        # Sell when MACD crosses below signal line
        elif macd_line < signal_line and prev_macd_line >= prev_signal_line:
            action = -1
    
    return action

# Compute return rate over a given price vector, with MACD parameters
def computeReturnRate(priceVec, fast_period, slow_period, signal_period):
    global macd_history
    macd_history = []  # Reset for each test
    
    capital = 1000  # Initial available capital
    capitalOrig = capital  # original capital
    dataCount = len(priceVec)  # day size
    suggestedAction = np.zeros((dataCount, 1))  # Vec of suggested actions
    stockHolding = np.zeros((dataCount, 1))  # Vec of stock holdings
    total = np.zeros((dataCount, 1))  # Vec of total asset
    realAction = np.zeros((dataCount, 1))  # Real action
    
    # Run through each day
    for ic in range(dataCount):
        currentPrice = priceVec[ic]  # current price
        suggestedAction[ic] = myStrategy(priceVec[0:ic], currentPrice, fast_period, slow_period, signal_period)
        
        # get real action by suggested action
        if ic > 0:
            stockHolding[ic] = stockHolding[ic-1]  # The stock holding from the previous day
        
        if suggestedAction[ic] == 1:  # Suggested action is "buy"
            if stockHolding[ic] == 0:  # "buy" only if you don't have stock holding
                stockHolding[ic] = capital / currentPrice  # Buy stock using cash
                capital = 0  # Cash
                realAction[ic] = 1
        elif suggestedAction[ic] == -1:  # Suggested action is "sell"
            if stockHolding[ic] > 0:  # "sell" only if you have stock holding
                capital = stockHolding[ic] * currentPrice  # Sell stock to have cash
                stockHolding[ic] = 0  # Stock holding
                realAction[ic] = -1
        elif suggestedAction[ic] == 0:  # No action
            realAction[ic] = 0
        else:
            assert False
        
        total[ic] = capital + stockHolding[ic] * currentPrice  # Total asset
    
    returnRate = (total[-1].item() - capitalOrig) / capitalOrig  # Return rate
    return returnRate

if __name__ == '__main__':
    returnRateBest = -1.00  # Initial best return rate
    df = pd.read_csv(sys.argv[1])  # read stock file
    adjClose = df["Adj Close"].values  # get adj close as the price vector
    
    # Parameter ranges for MACD - try more traditional values
    fast_periods = [8, 10, 12]  # Traditional: 12
    slow_periods = [20, 24, 26]  # Traditional: 26
    signal_periods = [5, 7, 9]  # Traditional: 9
    
    # Start exhaustive search
    for fast_period in fast_periods:
        print("fast_period=%d" % (fast_period))
        for slow_period in slow_periods:
            print("\tslow_period=%d" % (slow_period))
            for signal_period in signal_periods:
                print("\t\tsignal_period=%d" % (signal_period), end="")
                returnRate = computeReturnRate(adjClose, fast_period, slow_period, signal_period)
                print(" ==> returnRate=%f " % (returnRate))
                if returnRate > returnRateBest:  # Keep the best parameters
                    fastPeriodBest = fast_period
                    slowPeriodBest = slow_period
                    signalPeriodBest = signal_period
                    returnRateBest = returnRate
    
    print("Best settings: fast_period=%d, slow_period=%d, signal_period=%d ==> returnRate=%f" % 
          (fastPeriodBest, slowPeriodBest, signalPeriodBest, returnRateBest))