import uvicorn
from fastapi import FastAPI
from stats_utils import get_availiable_pairs, summary_for_pair, ticker_for_pair, orderbook_for_pair, trades_for_pair, atomicdex_info
from decimal import Decimal

path_to_db = 'MM2.db'
app = FastAPI()
available_pairs = get_availiable_pairs(path_to_db)


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
    return summary_data


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
    # TODO: move me to utils
    ticker_data_unified = []
    for data_sample in ticker_data:
        base_ticker = list(data_sample.keys())[0].split("_")[0]
        rel_ticker = list(data_sample.keys())[0].split("_")[1]
        data_sample_unified = {}
        if base_ticker != ticker_ticker:
            data_sample_unified[ticker_ticker + "_" + rel_ticker] = {
                "last_price": "{:.10f}".format(1 / Decimal(list(data_sample.keys())[0]["last_price"])),
                "quote_volume": list(data_sample.keys())[0]["base_volume"],
                "base_volume": list(data_sample.keys())[0]["quote_volume"],
                "isFrozen": "0"
            }
            ticker_data_unified.append(data_sample_unified)
        else:
            ticker_data_unified.append(data_sample)
    return ticker_data


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
