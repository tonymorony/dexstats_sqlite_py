import uvicorn
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from stats_utils import get_availiable_pairs, summary_for_pair, ticker_for_pair, orderbook_for_pair, trades_for_pair,\
    atomicdex_info, reverse_string_number, get_data_from_gecko, summary_for_ticker, ticker_for_ticker, volume_for_ticker
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
    return summary_for_ticker(ticker_summary, path_to_db)


@app.get('/api/v1/ticker')
def ticker():
    available_pairs_ticker = get_availiable_pairs(path_to_db)
    ticker_data = []
    for pair in available_pairs_ticker:
        ticker_data.append(ticker_for_pair(pair, path_to_db, 1))
    return ticker_data


@app.get('/api/v1/ticker_for_ticker/{ticker_ticker}')
def ticker(ticker_ticker="KMD"):
    return ticker_for_ticker(ticker_ticker, path_to_db, 1)


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


@app.get('/api/v1/fiat_rates')
def fiat_rates():
    with open('gecko_cache.json', 'r') as json_file:
        gecko_cached_data = json.load(json_file)
    return gecko_cached_data


# TODO: get volumes for x days for ticker
@app.get("api/v1/volumes_ticker/{ticker_vol}/{days_in_past}")
def volumes_history_ticker(ticker_vol="KMD", days_in_past=1):
    return volume_for_ticker(ticker_vol, path_to_db, days_in_past)


# TODO: get volumes for x days for pair
@app.get("api/v1/volumes_pair/{pair}/{days_in_past}")
def volumes_history_ticker():
    return ""


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
