import uvicorn
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from stats_utils import get_availiable_pairs, summary_for_pair, ticker_for_pair, orderbook_for_pair, trades_for_pair, atomicdex_info, get_data_from_gecko

path_to_db = '/DB/43ec929fe30ee72be42c9162c56dde910a05e50d/MM2.db'
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
    try:
        with open('gecko_cache.json', 'w') as json_file:
            json_file.write(json.dumps(gecko_data))
    except Exception as e:
        print(e)
    print("saved gecko data to file")

@app.get('/api/v1/summary')
def summary():
    available_pairs = get_availiable_pairs(path_to_db)
    summary_data = []
    for pair in available_pairs:
        summary_data.append(summary_for_pair(pair, path_to_db))
    return summary_data


@app.get('/api/v1/ticker')
def ticker():
    available_pairs = get_availiable_pairs(path_to_db)
    ticker_data = []
    for pair in available_pairs:
        ticker_data.append(ticker_for_pair(pair, path_to_db))
    return ticker_data


@app.get('/api/v1/orderbook/{market_pair}')
def orderbook(market_pair="KMD_BTC"):
    orderbook_data = orderbook_for_pair(market_pair)
    return orderbook_data


@app.get('/api/v1/trades/{market_pair}')
def trades(market_pair="KMD_BTC"):
    trades_data = trades_for_pair(market_pair, path_to_db)
    return trades_data


@app.get('/api/v1/atomicdexio')
def atomicdex_info_api():
    data = atomicdex_info(path_to_db)
    return data

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
