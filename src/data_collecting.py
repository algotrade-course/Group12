import pandas as pd
import numpy as np
import psycopg
import json
import pprint
import mplfinance as mpf

from typing import List
from matplotlib import pyplot as plt
from numpy.testing import assert_almost_equal, assert_equal

# Load data
with open('src/database.json', 'rb') as fb:
    db_info = json.load(fb)
conn = psycopg.connect(
    host=db_info['host'],
    port=db_info['port'],
    dbname=db_info['database'],
    user=db_info['user'],
    password=db_info['password']
)
with psycopg.connect(
    host=db_info['host'],
    port=db_info['port'],
    dbname=db_info['database'],
    user=db_info['user'],
    password=db_info['password']
) as conn:
    # Open a cursor to perform database operations
    with conn.cursor() as data:
        
        # Execute a query
        data.execute("""
            SELECT m.datetime, m.tickersymbol, m.price
            FROM "quote"."matched" m
            WHERE m.tickersymbol LIKE 'VN30F23%'
            and m.datetime >= '2023-01-01 00:00:00'
        """)

        # Use fetchall() to get all the data of the query.
        # Note: fetchall() can be costly and inefficient.
        # Other efficient ways have been discussed extensively on the Internet. Or you can ask ChatGPT ;)
        dataset = data.fetchall()
        df = pd.DataFrame(dataset, columns=['datetime', 'tickersymbol', 'price'])
        df.to_csv('src/ticks.csv', index=False)

        # Print the total number of ticks of that day
        print(f'Total number of tick: {len(dataset)}')