import sqlite3
import requests
import json
from decimal import Decimal
from datetime import datetime, timedelta
from collections import OrderedDict 

# getting list of pairs with amount of swaps > 0 from db (list of tuples)
# sql_coursor -> list (of base, rel tuples)
def get_availiable_pairs(sql_coursor):
    sql_coursor.execute("SELECT DISTINCT maker_coin, taker_coin FROM stats_swaps;")
    available_pairs = sql_coursor.fetchall()
    return available_pairs

# tuple, integer -> list (with swap status dicts)
# select from DB swap statuses for desired pair with timestamps > than provided
def get_swaps_since_timestamp_for_pair(sql_coursor, pair, timestamp):
    sql_coursor.execute("SELECT * FROM stats_swaps WHERE started_at > {} AND maker_coin='{}' AND taker_coin='{}' AND is_success=1;".format(timestamp,pair[0],pair[1]))
    swap_statuses = [dict(row) for row in sql_coursor.fetchall()]
    return swap_statuses

# list (with swaps statuses) -> dict 
# iterating over the list of swaps and counting data for CMC summary call
# last_price, base_volume, quote_volume, highest_price_24h, lowest_price_24h, price_change_percent_24h
def count_volumes_and_prices(swap_statuses):
    pair_volumes_and_prices = {}
    base_volume = 0
    quote_volume = 0
    swap_prices = {}
    for swap_status in swap_statuses:
        base_volume += swap_status["maker_amount"]
        quote_volume += swap_status["taker_amount"]
        swap_price = Decimal(swap_status["taker_amount"]) / Decimal(swap_status["maker_amount"])
        swap_prices[swap_status["started_at"]] = swap_price

    pair_volumes_and_prices["base_volume"] = base_volume
    pair_volumes_and_prices["quote_volume"] = quote_volume
    pair_volumes_and_prices["highest_price_24h"] = max(swap_prices.values())
    pair_volumes_and_prices["lowest_price_24h"] = min(swap_prices.values())
    pair_volumes_and_prices["last_price"] = swap_prices[max(swap_prices.keys())]
    pair_volumes_and_prices["price_change_percent_24h"] = ( swap_prices[max(swap_prices.keys())] - swap_prices[min(swap_prices.keys())] ) / Decimal(100)

    return pair_volumes_and_prices

# tuple, string, string -> list
# returning orderbook for given trading pair
def get_mm2_orderbook_for_pair(pair):
    mm2_host = "http://127.0.0.1:7783"
    params = {
              'method': 'orderbook',
              'base': pair[0],
              'rel': pair[1]
             }
    r = requests.post(mm2_host, json=params)
    return json.loads(r.text)


# list -> string
# returning lowest ask from provided orderbook

def find_lowest_ask(orderbook):
    lowest_ask = {"price" : "0"}
    for ask in orderbook["asks"]:
        if lowest_ask["price"] == "0":
            lowest_ask = ask
        elif Decimal(ask["price"]) < Decimal(lowest_ask["price"]):
            lowest_ask = ask
    return lowest_ask["price"]


# list -> string
# returning highest bid from provided orderbook
def find_highest_bid(orderbook):
    highest_bid = {"price" : "0"}
    for bid in orderbook["bids"]:
        if Decimal(bid["price"]) > Decimal(highest_bid["price"]):
            highest_bid = bid
    return highest_bid["price"]

# SUMMARY Endpoint
# tuple, string -> dictionary
# Receiving tuple with base and rel as an argument and producing CMC summary endpoint data, requires mm2 rpc password and sql db connection
def summary_for_pair(pair, path_to_db):
    conn = sqlite3.connect(path_to_db)
    conn.row_factory = sqlite3.Row
    sql_coursor = conn.cursor()
    pair_summary = OrderedDict()
    timestamp_24h_ago = int((datetime.now() - timedelta(1)).strftime("%s"))
    swaps_for_pair_24h = get_swaps_since_timestamp_for_pair(sql_coursor, pair, timestamp_24h_ago)
    pair_24h_volumes_and_prices = count_volumes_and_prices(swaps_for_pair_24h)

    pair_summary["trading_pair"] = pair[0] + "_" + pair[1]
    pair_summary["last_price"] = "{:.10f}".format(pair_24h_volumes_and_prices["last_price"])
    orderbook = get_mm2_orderbook_for_pair(pair)
    pair_summary["lowest_ask"] = "{:.10f}".format(Decimal(find_lowest_ask(orderbook)))
    pair_summary["highest_bid"] = "{:.10f}".format(Decimal(find_highest_bid(orderbook)))
    pair_summary["base_currency"] = pair[0]
    pair_summary["base_volume"] = "{:.10f}".format(pair_24h_volumes_and_prices["base_volume"])
    pair_summary["quote_currency"] = pair[1]
    pair_summary["quote_volume"] = "{:.10f}".format(pair_24h_volumes_and_prices["quote_volume"])
    pair_summary["price_change_percent_24h"] = "{:.10f}".format(pair_24h_volumes_and_prices["price_change_percent_24h"])
    pair_summary["highest_price_24h"] = "{:.10f}".format(pair_24h_volumes_and_prices["highest_price_24h"])
    pair_summary["lowest_price_24h"] = "{:.10f}".format(pair_24h_volumes_and_prices["lowest_price_24h"])

    return pair_summary
