import pandas as pd
import numpy as np
import psycopg
import json
import pprint
import mplfinance as mpf
import argparse

from typing import List
from matplotlib import pyplot as plt
from numpy.testing import assert_almost_equal, assert_equal
import matplotlib.pyplot as plt

# --- Constants ---
multiplier = 100000
margin_ratio = 0.175
AR = 0.8
fee_points = 0.47

# Initialize asset variables
total_asset = 100_000_000  # Total asset in VND
available_asset = total_asset  # Funds available for trading

# --- Trade State ---
open_positions = []  # List of currently open positions
trades = []          # List to record completed trades

def open_position(position_type, entry_price, entry_time):
    global available_asset
    deposit = (entry_price * multiplier * margin_ratio) / AR
    if available_asset < deposit:
        print(f"Insufficient funds to open {position_type} trade at {entry_time}. Required deposit: {deposit}, available: {available_asset}")
        return
    available_asset -= deposit  # Lock the deposit
    new_position = {
        'type': position_type,  # 'long' or 'short'
        'entry_price': entry_price,
        'entry_time': entry_time,
        'deposit': deposit
    }
    open_positions.append(new_position)
    #print(f"Opened {position_type} position at {entry_price} on {entry_time} with deposit {deposit}")

def close_position(position, exit_price, exit_time):
    global available_asset, total_asset
    entry_price = position['entry_price']
    deposit = position['deposit']
    if position['type'] == 'long':
        raw_points = exit_price - entry_price
    else:  # For a short position:
        raw_points = entry_price - exit_price
    net_points = raw_points - fee_points
    profit_vnd = net_points * multiplier
    available_asset += deposit + profit_vnd  # Return deposit and profit
    total_asset += profit_vnd  # Update overall asset value
    # Record the trade details.
    trade = position.copy()
    trade['exit_price'] = exit_price
    trade['exit_time'] = exit_time
    trade['raw_points'] = raw_points
    trade['net_points'] = net_points
    trade['profit_vnd'] = profit_vnd
    trade['profit_pct'] = profit_vnd / deposit
    if pd.isna(exit_time):
        return
    trades.append(trade)
    #print(f"Closed {position['type']} position opened on {position['entry_time']} at {exit_price} on {exit_time} with profit {profit_vnd} VND, return {trade['profit_pct']*100:.2f}%")

def close_all_positions(exit_price, exit_time):
    # Close each open position.
    for pos in open_positions.copy():
        close_position(pos, exit_price, exit_time)
        open_positions.remove(pos)
        
# --- Main Script ---
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Backtesting script with input JSON file.")
    parser.add_argument("input_file", type=str, help="Path to the input JSON file (e.g., src/in-sample.json)")
    parser.add_argument("--log", action="store_true", help="Log the trade details")
    args = parser.parse_args()

    # Load df_list back from the JSON file
    with open("src/" + args.input_file, 'r') as f:
        df_list = json.load(f)

    # Convert datetime strings back to pandas Timestamps
    for record in df_list:
        record['datetime'] = pd.Timestamp(record['datetime'])
    # --- Backtesting Loop Using df_list ---
    n = len(df_list)
    for i in range(n):
        current_candle = df_list[i]
        current_time = current_candle['datetime']
        
        # --- Overnight Position Closing ---
        if i > 0:
            prev_time = df_list[i-1]['datetime']
            if current_time.date() != prev_time.date():
                # Close all open positions at the previous candle's close.
                close_all_positions(df_list[i-1]['close'], prev_time)
        
        # --- Check Exit Conditions for Each Open Position ---
        for pos in open_positions.copy():
            if pos['type'] == 'long':
                unrealized_points = current_candle['close'] - pos['entry_price']
            else:
                unrealized_points = pos['entry_price'] - current_candle['close']
            # Exit if take profit (>= 3 points) or stop loss (<= -1 point) is reached.
            if unrealized_points >= 3 or unrealized_points <= -1:
                close_position(pos, current_candle['close'], current_time)
                open_positions.remove(pos)
        
        # --- Check for Entry Signals ---
        if i >= 3:
            # Check if the previous 3 candles are consecutive (1 minute apart)
            if ((current_time - df_list[i-1]['datetime'] == pd.Timedelta(minutes=1)) and
                (df_list[i-1]['datetime'] - df_list[i-2]['datetime'] == pd.Timedelta(minutes=1)) and
                (df_list[i-2]['datetime'] - df_list[i-3]['datetime'] == pd.Timedelta(minutes=1)) and
                (current_candle['tickersymbol'] == df_list[i-1]['tickersymbol'] ==
                df_list[i-2]['tickersymbol'] == df_list[i-3]['tickersymbol'])):
                
                # Get the previous three candles
                prev_candles = df_list[i-3:i]
                # Define patterns: bearish if close < open, bullish if close > open.
                bearish_pattern = all(candle['close'] < candle['open'] for candle in prev_candles)
                bullish_pattern = all(candle['close'] > candle['open'] for candle in prev_candles)
                # Ensure SMA50 is available.
                if np.isnan(current_candle['SMA50']):
                    continue
                
                # Entry Signal for LONG: previous 3 candles are bearish, previous candle’s high is below current candle’s close,
                # and current candle’s close is above its SMA50.
                if bearish_pattern and (df_list[i-1]['high'] < current_candle['close']) and (current_candle['SMA50'] < current_candle['close']):
                    open_position('long', current_candle['close'], current_time)
                # Entry Signal for SHORT can be added similarly if desired.
                if bullish_pattern and (df_list[i-1]['low'] > current_candle['close']) and (current_candle['SMA50'] > current_candle['close']):
                    open_position('short', current_candle['close'], current_time)
        
    # --- End of Backtesting Loop ---
    if open_positions:
        close_all_positions(df_list[-1]['close'], df_list[-1]['datetime'])

    # --- Trade Summary ---
    trades_df = pd.DataFrame(trades)
    print("\nBacktesting completed. Trade summary:")
    if args.log:
        print(trades_df)
    total_profit = trades_df['profit_vnd'].sum() if not trades_df.empty else 0
    print(f"Total Profit: {total_profit} VND")
