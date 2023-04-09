import os
import requests


from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import (create_engine, insert, text,
                        Table, MetaData, Column, Integer,
                        String, Date, Numeric)
from sqlalchemy.orm import sessionmaker

from financial.config import *


# Table Variables
db_id = 'id'
db_symbol = 'symbol'
db_date = 'date'
db_open_price = 'open_price'
db_close_price = 'close_price'
db_volume = 'volume'

# API Configs
symbol_list = ['IBM', 'AAPL']
url = ('https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY'
       '&symbol={0}&interval=60min&outputsize=full&apikey={1}'
       )
api_keyname_open = '1. open'
api_keyname_close = '4. close'
api_keyname_volume = '5. volume'


# Connect to db
engine = create_engine(API_CONNECT_DB_STR)

metadata = MetaData()
financial_data_tbl = Table(
    'financial_data', metadata,
    Column(db_id, Integer, primary_key=True, index=True),
    Column(db_symbol, String(10)),
    Column(db_date, Date),
    Column(db_open_price, Numeric(20, 2)),
    Column(db_close_price, Numeric(20, 2)),
    Column(db_volume, Integer),)
metadata.create_all(engine)


def process_data():
    """
    Bulk of the process to grab data from alphavantage
    """
    process_start_date = date.today() - timedelta(weeks=2)

    for symbol in symbol_list:
        sum_volume = 0
        open_price = 0.0
        close_price = 0.0
        current_datetime = None
        prev_date = None
        current_date = None
        close_time = None
        open_time = None
        insert_row = {}

        # Get data from the alphavantage api
        req = requests.get(url.format(symbol, API_KEY))
        data = req.json()

        # Check latest record and not print if date exists to avoid dupes
        latest_record = find_latest_record_by_symbol(symbol)

        for data_chunk in data:
            if data_chunk != 'Meta Data':
                with engine.connect() as conn:
                    for time_data, time_values in data[data_chunk].items():
                        # Data currently being processed
                        current_datetime = datetime.strptime(
                            time_data, '%Y-%m-%d %H:%M:%S')
                        current_date = current_datetime.date()

                        # Ignore data earlier than 2 weeks
                        if current_date < process_start_date:
                            continue

                        # Ignore duplicates
                        if latest_record is not None:
                            if current_date <= latest_record:
                                continue

                        if prev_date is None:
                            prev_date = current_date

                        # If current process data is different date, reset
                        if (current_date < prev_date):
                            conn.execute(
                                financial_data_tbl.insert(), insert_row)
                            conn.commit()
                            insert_row = {}
                            prev_date = current_date
                            close_time = None
                            open_time = None
                            sum_volume = 0

                        if close_time is None:
                            close_time = current_datetime.hour
                            close_price = Decimal(time_values[api_keyname_close])

                        if open_time is None:
                            open_time = current_datetime.hour

                        # If current data hour is earlier, pull new open
                        if current_datetime.hour < open_time:
                            open_time = current_datetime.hour
                            open_price = Decimal(time_values[api_keyname_open])

                        sum_volume += Decimal(time_values[api_keyname_volume])

                        insert_row = {db_symbol: str(symbol),
                                      db_date: str(current_date),
                                      db_open_price: open_price,
                                      db_close_price: close_price,
                                      db_volume: sum_volume
                                      }
                        print(insert_row)

                    if insert_row:
                        # Finish off inserting remaining data
                        conn.execute(financial_data_tbl.insert(), insert_row)
                        conn.commit()
        conn.close()


# Grab latest record by symbol
def find_latest_record_by_symbol(symbol):
    with engine.connect() as conn:
        stmt = ('SELECT `{0}` FROM `{1}` '
                'WHERE `{2}` = "{3}" ORDER BY `{0}` DESC LIMIT 1')
        stmt = stmt.format(db_date, DB_TABLE, db_symbol, symbol)
        results = conn.execute(text(stmt))
        results = [row[0] for row in results]

        if results:
            return results[0]
        return None


# Function we need to run for this project
process_data()
