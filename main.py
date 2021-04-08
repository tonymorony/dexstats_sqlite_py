import uvicorn
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from stats_utils import get_availiable_pairs, summary_for_pair, ticker_for_pair, orderbook_for_pair, trades_for_pair, atomicdex_info, reverse_string_number, get_data_from_gecko
from decimal import Decimal

path_to_db = 'MM2.db'
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

available_pairs = get_availiable_pairs(path_to_db)


@app.on_event("startup")
@repeat_every(seconds=60)  # caching data every minute
def cache_gecko_data():
    gecko_data = get_data_from_gecko()
    print(gecko_data)
    with open('gecko_cache.json', 'w+') as json_file:
        json.dump(gecko_data, json_file)
    print("saved gecko data to file")


@app.get('/api/v1/summary')
def summary():
    available_pairs_summary = get_availiable_pairs(path_to_db)
    summary_data = []
    for pair in available_pairs_summary:
        summary_data.append(summary_for_pair(pair, path_to_db))
    return summary_data


@app.get('/api/v1/summary_for_ticker/{ticker_summary}')
def summary(ticker_summary="KMD"):
    available_pairs_summary_ticker = get_availiable_pairs(path_to_db)
    summary_data = []
    for pair in available_pairs_summary_ticker:
        if ticker_summary in pair:
            summary_data.append(summary_for_pair(pair, path_to_db))
    # TODO: move me to utils function
    summary_data_modified = []
    for summary_sample in summary_data:
        # filtering empty data
        if Decimal(summary_sample["base_volume"]) != 0 and Decimal(summary_sample["quote_volume"]) != 0:
            if summary_sample["base_currency"] == ticker_summary:
                summary_data_modified.append(summary_sample)
            else:
                summary_sample_modified = {
                    "trading_pair": summary_sample["quote_currency"] + "_" + summary_sample["base_currency"],
                    "last_price": reverse_string_number(summary_sample["last_price"]),
                    "lowest_ask": reverse_string_number(summary_sample["lowest_ask"]),
                    "highest_bid": reverse_string_number(summary_sample["highest_bid"]),
                    "base_currency": summary_sample["quote_currency"],
                    "base_volume": summary_sample["quote_volume"],
                    "quote_currency": summary_sample["base_currency"],
                    "quote_volume": summary_sample["base_volume"],
                    "price_change_percent_24h": summary_sample["price_change_percent_24h"],
                    "highest_price_24h": reverse_string_number(summary_sample["lowest_price_24h"]),
                    "lowest_price_24h": reverse_string_number(summary_sample["highest_price_24h"])
                }
                summary_data_modified.append(summary_sample_modified)
    return summary_data_modified


@app.get('/api/v1/ticker')
def ticker():
    available_pairs_ticker = get_availiable_pairs(path_to_db)
    ticker_data = []
    for pair in available_pairs_ticker:
        ticker_data.append(ticker_for_pair(pair, path_to_db))
    return ticker_data


@app.get('/api/v1/ticker_for_ticker/{ticker_ticker}')
def ticker(ticker_ticker="KMD"):
    available_pairs_ticker = get_availiable_pairs(path_to_db)
    ticker_data = []
    for pair in available_pairs_ticker:
        if ticker_ticker in pair:
            ticker_data.append(ticker_for_pair(pair, path_to_db))
    # TODO: move me to utils function
    ticker_data_unified = []
    for data_sample in ticker_data:
        # not adding zero volumes data
        first_key = list(data_sample.keys())[0]
        if Decimal(data_sample[first_key]["last_price"]) != 0:
            base_ticker = first_key.split("_")[0]
            rel_ticker = first_key.split("_")[1]
            data_sample_unified = {}
            if base_ticker != ticker_ticker:
                last_price_reversed = reverse_string_number(data_sample[first_key]["last_price"])
                data_sample_unified[ticker_ticker + "_" + base_ticker] = {
                    "last_price": last_price_reversed,
                    "quote_volume": data_sample[first_key]["base_volume"],
                    "base_volume": data_sample[first_key]["quote_volume"],
                    "isFrozen": "0"
                }
                ticker_data_unified.append(data_sample_unified)
            else:
                ticker_data_unified.append(data_sample)
    return ticker_data_unified


@app.get('/api/v1/orderbook/{market_pair}')
def orderbook(market_pair="KMD_BTC"):
    orderbook_data = orderbook_for_pair(market_pair)
    return orderbook_data


@app.get('/api/v1/trades/{market_pair}/{days_in_past}')
def trades(market_pair="KMD_BTC", days_in_past=1):
    trades_data = trades_for_pair(market_pair, path_to_db, int(days_in_past))
    return trades_data


@app.get('/api/v1/atomicdexio')
def atomicdex_info_api():
    data = atomicdex_info(path_to_db)
    return data


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
