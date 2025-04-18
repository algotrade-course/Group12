
import pandas as pd
import numpy as np
import psycopg
import json
import pprint
import mplfinance as mpf

from typing import List
from matplotlib import pyplot as plt
from numpy.testing import assert_almost_equal, assert_equal
import matplotlib.pyplot as plt

df = pd.read_csv('src/ticks.csv', parse_dates=['datetime'])
dataset = list(df.itertuples(index=False, name=None))

# Devide data into in-sample and out-sample
in_sample_dataset = dataset[:int(len(dataset)*0.7)]
out_sample_dataset = dataset[int(len(dataset)*0.3):]

# Chuyển dữ liệu sang DataFrame của in_sample_data
in_sample_candle = pd.DataFrame(in_sample_dataset, columns=['datetime', 'tickersymbol', 'price'])
in_sample_candle['price'] = pd.to_numeric(in_sample_candle['price'], errors='coerce')

# Chuyển đổi cột datetime về kiểu datetime
in_sample_candle['datetime'] = pd.to_datetime(in_sample_candle['datetime'])
in_sample_candle.set_index('datetime', inplace=True)
in_sample_candle['ticker_month'] = in_sample_candle['tickersymbol'].str[-2:].astype(int)

# Create a boolean mask: keep rows if ticker_month <= (datetime month + 1)
mask = in_sample_candle['ticker_month'] <= (in_sample_candle.index.month + 1)

# Filter the DataFrame using the mask
in_sample_candle = in_sample_candle[mask]

# (Optional) Remove the temporary column if no longer needed
in_sample_candle.drop(columns='ticker_month', inplace=True)

# Sort by datetime
in_sample_candle.sort_index(inplace=True)

# Resample dữ liệu theo khung 1 giờ (1h)
in_sample_candle_ohlc = in_sample_candle['price'].resample('1T').ohlc()
in_sample_candle_ohlc = (
    in_sample_candle
    .groupby('tickersymbol')
    .resample('1T')['price']
    .ohlc()
    .reset_index()
)
in_sample_candle_ohlc.set_index('datetime', inplace=True)

# Vẽ biểu đồ nến
mpf.plot(in_sample_candle_ohlc[50:200], type='candle', style='charles',
        title=" In sample data VN30F2311 Candlestick Chart (1m)", ylabel="Price")

# Chuyển dữ liệu sang DataFrame của out_sample_data
out_sample_candle = pd.DataFrame(out_sample_dataset, columns=['datetime', 'tickersymbol', 'price'])
out_sample_candle['price'] = pd.to_numeric(out_sample_candle['price'], errors='coerce')

# Chuyển đổi cột datetime về kiểu datetime
out_sample_candle['datetime'] = pd.to_datetime(out_sample_candle['datetime'])
out_sample_candle.set_index('datetime', inplace=True)
out_sample_candle['ticker_month'] = out_sample_candle['tickersymbol'].str[-2:].astype(int)

# Filter the DataFrame using the mask
out_sample_candle = out_sample_candle[out_sample_candle['ticker_month'] <= (out_sample_candle.index.month + 1)]

# (Optional) Remove the temporary column if no longer needed
out_sample_candle.drop(columns='ticker_month', inplace=True)

# Sort by datetime
out_sample_candle.sort_index(inplace=True)

# Resample dữ liệu theo khung 1 giờ (1h)
out_sample_candle_ohlc = out_sample_candle['price'].resample('1T').ohlc()
out_sample_candle_ohlc = (
    out_sample_candle
    .groupby('tickersymbol')
    .resample('1T')['price']
    .ohlc()
    .reset_index()
)
out_sample_candle_ohlc.set_index('datetime', inplace=True)

# Vẽ biểu đồ nến
mpf.plot(out_sample_candle_ohlc[50:200], type='candle', style='charles',
        title=" Out sample data VN30F2311 Candlestick Chart (1m)", ylabel="Price")

# --- Prepare Data ---
# Assume in_sample_candle_ohlc is a DataFrame with a DateTimeIndex.
df = in_sample_candle_ohlc.copy()
df['SMA50'] = df['close'].rolling(window=50, min_periods=50).mean()

# Reset the index so that the datetime becomes a column.
df.reset_index(inplace=True)
df.rename(columns={'index': 'datetime'}, inplace=True)

# Convert DataFrame to list of dictionaries for faster common indexing
df_list = df.to_dict('records')
# Save df_list to a JSON file
with open('src/in-sample.json', 'w') as f:
    json.dump(df_list, f, default=str, indent=4)

df = out_sample_candle_ohlc.copy()
df['SMA50'] = df['close'].rolling(window=50, min_periods=50).mean()
# Reset the index so that the datetime becomes a column.
df.reset_index(inplace=True)
df.rename(columns={'index': 'datetime'}, inplace=True)

# Convert DataFrame to list of dictionaries for faster common indexing
df_list = df.to_dict('records')
# Save df_list to a JSON file
with open('src/out-sample.json', 'w') as f:
    json.dump(df_list, f, default=str, indent=4)
