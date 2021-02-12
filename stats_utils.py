import sqlite3
import requests
import json
from decimal import Decimal
from datetime import datetime, timedelta
from collections import OrderedDict

# getting list of pairs with amount of swaps > 0 from db (list of tuples)
# string -> list (of base, rel tuples)
def get_availiable_pairs(path_to_db):
    conn = sqlite3.connect(path_to_db)
    sql_coursor = conn.cursor()
    sql_coursor.execute("SELECT DISTINCT maker_coin, taker_coin FROM stats_swaps;")
    available_pairs = sql_coursor.fetchall()
    conn.close()
    return available_pairs

# tuple, integer -> list (with swap status dicts)
# select from DB swap statuses for desired pair with timestamps > than provided
def get_swaps_since_timestamp_for_pair(sql_coursor, pair, timestamp):
    t = (timestamp,pair[0],pair[1],)
    sql_coursor.execute("SELECT * FROM stats_swaps WHERE started_at > ? AND maker_coin=? AND taker_coin=? AND is_success=1;", t)
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
    try:
        pair_volumes_and_prices["highest_price_24h"] = max(swap_prices.values())
    except ValueError:
        pair_volumes_and_prices["highest_price_24h"] = 0
    try:
        pair_volumes_and_prices["lowest_price_24h"] = min(swap_prices.values())
    except ValueError:
        pair_volumes_and_prices["lowest_price_24h"] = 0
    try:
        pair_volumes_and_prices["last_price"] = swap_prices[max(swap_prices.keys())]
    except ValueError:
        pair_volumes_and_prices["last_price"] = 0
    try:
        pair_volumes_and_prices["price_change_percent_24h"] = ( swap_prices[max(swap_prices.keys())] - swap_prices[min(swap_prices.keys())] ) / Decimal(100)
    except ValueError:
        pair_volumes_and_prices["price_change_percent_24h"] = 0

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
    try:
        for ask in orderbook["asks"]:
            if lowest_ask["price"] == "0":
                lowest_ask = ask
            elif Decimal(ask["price"]) < Decimal(lowest_ask["price"]):
                lowest_ask = ask
    except KeyError:
        return 0
    return lowest_ask["price"]


# list -> string
# returning highest bid from provided orderbook
def find_highest_bid(orderbook):
    highest_bid = {"price" : "0"}
    try:
        for bid in orderbook["bids"]:
            if Decimal(bid["price"]) > Decimal(highest_bid["price"]):
                highest_bid = bid
    except KeyError:
        return 0
    return highest_bid["price"]

def get_and_parse_orderbook(pair):
    orderbook = get_mm2_orderbook_for_pair(pair)
    bids_converted_list = []
    asks_converted_list = []
    for bid in orderbook["bids"]:
        converted_bid = []
        converted_bid.append(bid["price"])
        converted_bid.append(bid["maxvolume"])
        bids_converted_list.append(converted_bid)
    for ask in orderbook["asks"]:
        converted_ask = []
        converted_ask.append(ask["price"])
        converted_ask.append(ask["maxvolume"])
        asks_converted_list.append(converted_ask)
    return bids_converted_list, asks_converted_list

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

    conn.close()
    return pair_summary

# TICKER Endpoint
def ticker_for_pair(pair, path_to_db):
    conn = sqlite3.connect(path_to_db)
    conn.row_factory = sqlite3.Row
    sql_coursor = conn.cursor()
    pair_ticker = OrderedDict()
    timestamp_24h_ago = int((datetime.now() - timedelta(1)).strftime("%s"))
    swaps_for_pair_24h = get_swaps_since_timestamp_for_pair(sql_coursor, pair, timestamp_24h_ago)
    pair_24h_volumes_and_prices = count_volumes_and_prices(swaps_for_pair_24h)
    pair_ticker[pair[0] + "_" + pair[1]] = OrderedDict()
    pair_ticker[pair[0] + "_" + pair[1]]["last_price"] = "{:.10f}".format(pair_24h_volumes_and_prices["last_price"])
    pair_ticker[pair[0] + "_" + pair[1]]["quote_volume"] = "{:.10f}".format(pair_24h_volumes_and_prices["quote_volume"])
    pair_ticker[pair[0] + "_" + pair[1]]["base_volume"] = "{:.10f}".format(pair_24h_volumes_and_prices["base_volume"])
    pair_ticker[pair[0] + "_" + pair[1]]["isFrozen"] = "0"
    conn.close()
    return pair_ticker

# Orderbook Endpoint
def orderbook_for_pair(pair):
    pair = tuple(map(str, pair.split('_')))
    orderbook_data = OrderedDict()
    orderbook_data["timestamp"] = "{}".format(int(datetime.now().strftime("%s")))
    # TODO: maybe it'll be asked on API side? quite tricky to convert strings and sort the
    orderbook_data["bids"] = get_and_parse_orderbook(pair)[0]
    orderbook_data["asks"] = get_and_parse_orderbook(pair)[1]
    return orderbook_data

# Trades Endpoint
def trades_for_pair(pair, path_to_db):
    pair = tuple(map(str, pair.split('_')))
    conn = sqlite3.connect(path_to_db)
    conn.row_factory = sqlite3.Row
    sql_coursor = conn.cursor()
    timestamp_24h_ago = int((datetime.now() - timedelta(1)).strftime("%s"))
    swaps_for_pair_24h = get_swaps_since_timestamp_for_pair(sql_coursor, pair, timestamp_24h_ago)
    trades_info = []
    for swap_status in swaps_for_pair_24h:
        trade_info = OrderedDict()
        trade_info["trade_id"] = swap_status["uuid"]
        trade_info["price"] = "{:.10f}".format(Decimal(swap_status["taker_amount"]) / Decimal(swap_status["maker_amount"]))
        trade_info["base_volume"] = swap_status["maker_amount"]
        trade_info["quote_volume"] = swap_status["taker_amount"]
        trade_info["timestamp"] = swap_status["started_at"]
        trade_info["type"] = "buy"
        trades_info.append(trade_info)
    conn.close()
    return trades_info
