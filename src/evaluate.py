import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import psycopg
import json
import pprint
import mplfinance as mpf
import argparse

from typing import List
# Set initial capital (must be consistent with your simulation)
initial_capital = 100_000_000  # VND
parser = argparse.ArgumentParser(
    
)
parser.add_argument(
    "--optimize",
    action="store_true",
    help="Optimizing, do NOT print the AOT"
)
# Convert trades into a DataFrame (assuming the list "trades" is already available)
trades_df = pd.read_pickle("src/trades.pkl")

# Ensure trades are sorted by exit time
trades_df.sort_values(by="exit_time", inplace=True)

# Compute cumulative asset value over time
trades_df["capital_over_time"] = initial_capital + trades_df["profit_vnd"].cumsum()
trades_df["capital_over_time"] = trades_df["capital_over_time"].ffill()

args = parser.parse_args()
if args.optimize:
    # If optimizing, do not plot the asset curve
    pass
else:
    # Plot the asset curve (capital over time)
    plt.figure(figsize=(8, 4))
    plt.plot(trades_df["exit_time"], trades_df["capital_over_time"], label="Portfolio Value")
    plt.axhline(y=initial_capital, color="r", linestyle="--", label="Initial Capital")
    plt.title('Asset Over Time')
    plt.xlabel("Exit Time")
    plt.ylabel("Portfolio Value (VND)")
    plt.gca().spines[['top', 'right']].set_visible(False)
    plt.show()

# Example initial capital matching your simulation
initial_capital = 100_000_000

# Convert trades into a DataFrame if needed
trades_df = pd.read_pickle("src/trades.pkl")

# Sum of profits from all trades
total_profit = trades_df["profit_vnd"].sum() if not trades_df.empty else 0

# Compute final capital
final_capital = initial_capital + total_profit

# Compute Holding Period Return
HPR = ((final_capital - initial_capital) / initial_capital) * 100

print(f"Initial Capital: {initial_capital} VND")
print(f"Final Capital: {final_capital} VND")
print(f"Holding Period Return (HPR): {HPR:.2f}%")

import pandas as pd

# Example initial capital
initial_capital = 100_000_000

# Convert trades into a DataFrame if needed
trades_df = pd.read_pickle("src/trades.pkl")

# Sort by exit time to ensure chronological order
trades_df.sort_values(by="exit_time", inplace=True)

# Compute the capital over time by cumulatively adding profits
trades_df["capital_over_time"] = initial_capital + trades_df["profit_vnd"].cumsum()

# Calculate the running maximum (peak) of the portfolio
running_max = trades_df["capital_over_time"].cummax()

# Compute drawdown as the difference between the peak and the current capital
drawdown = running_max - trades_df["capital_over_time"]

# The maximum drawdown (MDD) is the largest drop from a peak
max_drawdown = drawdown.max()

# Convert to percentage by dividing by the maximum running peak
MDD_percentage = (max_drawdown / running_max.max()) * 100 if running_max.max() != 0 else 0

print(f"Maximum Drawdown (MDD): {MDD_percentage:.2f}%")


# Convert trade list to DataFrame
trades_df = pd.read_pickle("src/trades.pkl")
trades_df = trades_df.dropna(subset=["exit_time"]).copy()
trades_df.sort_values(by="exit_time", inplace=True)
trades_df.reset_index(drop=True, inplace=True)

# Set initial capital (consistent with simulation)
initial_capital = 100_000_000  # VND

# Cumulative sum of all profits (in VND) up to each trade
trades_df["cumulative_profit"] = trades_df["profit_vnd"].cumsum()

# The portfolio's capital at each trade exit
trades_df["capital"] = initial_capital + trades_df["cumulative_profit"]

# Create a daily timestamp column (floor exit_time to date)
trades_df["date"] = trades_df["exit_time"].dt.floor("D")

# Get the last capital value for each day
daily_equity = trades_df.groupby("date")["capital"].last()

# Reindex to a daily date range and forward-fill missing days
all_days = pd.date_range(start=daily_equity.index.min(),
                        end=daily_equity.index.max(),
                        freq="D")
daily_equity = daily_equity.reindex(all_days, method="ffill")

# Sharpe Ratio Calculation (daily-based)
risk_free_rate_annual = 0.03  # 3% annual risk-free rate
trading_days_per_year = 252
daily_returns = daily_equity.pct_change().fillna(0)
# Convert annual risk-free rate to daily
daily_rf = risk_free_rate_annual / trading_days_per_year

# Excess returns = daily returns minus the daily risk-free rate
excess_returns = daily_returns - daily_rf

mean_excess_return = excess_returns.mean()
std_excess_return = excess_returns.std()

sharpe_ratio = (mean_excess_return / std_excess_return) * np.sqrt(trading_days_per_year) \
    if std_excess_return != 0 else np.nan

print("Daily-based Sharpe Ratio:", sharpe_ratio)
