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
    sorted_available_pairs = []
    for pair in available_pairs:
       sorted_available_pairs.append(tuple(sorted(pair)))
    conn.close()
    # removing duplicates
    return list(set(sorted_available_pairs))


# tuple, integer -> list (with swap status dicts)
# select from DB swap statuses for desired pair with timestamps > than provided
def get_swaps_since_timestamp_for_pair(sql_coursor, pair, timestamp):
    t = (timestamp,pair[0],pair[1],)
    sql_coursor.execute("SELECT * FROM stats_swaps WHERE started_at > ? AND maker_coin=? AND taker_coin=? AND is_success=1;", t)
    swap_statuses_a_b = [dict(row) for row in sql_coursor.fetchall()]
    for swap in swap_statuses_a_b:
        swap["trade_type"] = "buy"
    sql_coursor.execute("SELECT * FROM stats_swaps WHERE started_at > ? AND taker_coin=? AND maker_coin=? AND is_success=1;", t)
    swap_statuses_b_a = [dict(row) for row in sql_coursor.fetchall()]
    # should be enough to change amounts place = change direction
    for swap in swap_statuses_b_a:
        temp_maker_amount = swap["maker_amount"]
        swap["maker_amount"] = swap["taker_amount"]
        swap["taker_amount"] = temp_maker_amount
        swap["trade_type"] = "sell"
    swap_statuses = swap_statuses_a_b + swap_statuses_b_a
    return swap_statuses


def get_swaps_between_timestamps_for_pair(sql_coursor, pair, timestamp_a, timestamp_b):
    t = (timestamp_a,timestamp_b,pair[0],pair[1],)
    sql_coursor.execute("SELECT * FROM stats_swaps WHERE started_at > ? AND started_at < ? AND maker_coin=? AND taker_coin=? AND is_success=1;", t)
    swap_statuses_a_b = [dict(row) for row in sql_coursor.fetchall()]
    for swap in swap_statuses_a_b:
        swap["trade_type"] = "buy"
    sql_coursor.execute("SELECT * FROM stats_swaps WHERE started_at > ? AND started_at < ? AND taker_coin=? AND maker_coin=? AND is_success=1;", t)
    swap_statuses_b_a = [dict(row) for row in sql_coursor.fetchall()]
    # should be enough to change amounts place = change direction
    for swap in swap_statuses_b_a:
        temp_maker_amount = swap["maker_amount"]
        swap["maker_amount"] = swap["taker_amount"]
        swap["taker_amount"] = temp_maker_amount
        swap["trade_type"] = "sell"
    swap_statuses = swap_statuses_a_b + swap_statuses_b_a
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
    try:
        for bid in orderbook["bids"]:
            converted_bid = []
            converted_bid.append(bid["price"])
            converted_bid.append(bid["maxvolume"])
            bids_converted_list.append(converted_bid)
    except KeyError:
        pass
    try:
        for ask in orderbook["asks"]:
            converted_ask = []
            converted_ask.append(ask["price"])
            converted_ask.append(ask["maxvolume"])
            asks_converted_list.append(converted_ask)
    except KeyError:
        pass
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
def ticker_for_pair(pair, path_to_db, days_in_past=1):
    conn = sqlite3.connect(path_to_db)
    conn.row_factory = sqlite3.Row
    sql_coursor = conn.cursor()
    pair_ticker = OrderedDict()
    timestamp_24h_ago = int((datetime.now() - timedelta(days_in_past)).strftime("%s"))
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
    if len(pair) != 2 or not isinstance(pair[0], str) or not isinstance(pair[0], str):
        return {"error": "not valid pair"}
    orderbook_data = OrderedDict()
    orderbook_data["timestamp"] = "{}".format(int(datetime.now().strftime("%s")))
    # TODO: maybe it'll be asked on API side? quite tricky to convert strings and sort the
    orderbook_data["bids"] = get_and_parse_orderbook(pair)[0]
    orderbook_data["asks"] = get_and_parse_orderbook(pair)[1]
    return orderbook_data


# Trades Endpoint
def trades_for_pair(pair, path_to_db, days_in_past):
    pair = tuple(map(str, pair.split('_')))
    if len(pair) != 2 or not isinstance(pair[0], str) or not isinstance(pair[0], str):
        return {"error": "not valid pair"}
    conn = sqlite3.connect(path_to_db)
    conn.row_factory = sqlite3.Row
    sql_coursor = conn.cursor()
    timestamp_since = int((datetime.now() - timedelta(days_in_past)).strftime("%s"))
    swaps_for_pair_since_timestamp = get_swaps_since_timestamp_for_pair(sql_coursor, pair, timestamp_since)
    trades_info = []
    for swap_status in swaps_for_pair_since_timestamp:
        trade_info = OrderedDict()
        trade_info["trade_id"] = swap_status["uuid"]
        trade_info["price"] = "{:.10f}".format(Decimal(swap_status["taker_amount"]) / Decimal(swap_status["maker_amount"]))
        trade_info["base_volume"] = swap_status["maker_amount"]
        trade_info["quote_volume"] = swap_status["taker_amount"]
        trade_info["timestamp"] = swap_status["started_at"]
        trade_info["type"] = swap_status["trade_type"]
        trades_info.append(trade_info)
    conn.close()
    return trades_info


# Data for atomicdex.io website
def atomicdex_info(path_to_db):
    timestamp_24h_ago = int((datetime.now() - timedelta(1)).strftime("%s"))
    timestamp_30d_ago = int((datetime.now() - timedelta(30)).strftime("%s"))
    conn = sqlite3.connect(path_to_db)
    sql_coursor = conn.cursor()
    sql_coursor.execute("SELECT * FROM stats_swaps WHERE is_success=1;")
    swaps_all_time = len(sql_coursor.fetchall())
    sql_coursor.execute("SELECT * FROM stats_swaps WHERE started_at > ? AND is_success=1;", (timestamp_24h_ago,))
    swaps_24h = len(sql_coursor.fetchall())
    sql_coursor.execute("SELECT * FROM stats_swaps WHERE started_at > ? AND is_success=1;", (timestamp_30d_ago,))
    swaps_30d = len(sql_coursor.fetchall())
    conn.close()
    return {
        "swaps_all_time" : swaps_all_time,
        "swaps_30d" : swaps_30d,
        "swaps_24h" : swaps_24h
    }


def reverse_string_number(string_number):
    if Decimal(string_number) != 0:
        return "{:.10f}".format(1 / Decimal(string_number))
    else:
        return string_number


def get_data_from_gecko():
    coin_ids_dict = {}
    with open("0.4.0-coins.json", "r") as coins_json:
        json_data = json.load(coins_json)
        for coin in json_data:
            try:
                coin_ids_dict[coin] = {}
                coin_ids_dict[coin]["coingecko_id"] = json_data[coin]["coingecko_id"]
            except KeyError as e:
                 print(e)
                 coin_ids_dict[coin]["coingecko_id"] = "na"
    coin_ids = ""
    for coin in coin_ids_dict:
        coin_id = coin_ids_dict[coin]["coingecko_id"]
        if coin_id != "na" and coin_id != "test-coin":
            coin_ids += coin_id
            coin_ids += ","
    r = ""
    try:
        r = requests.get('https://api.coingecko.com/api/v3/simple/price?ids=' + coin_ids + '&vs_currencies=usd')
    except Exception as e:
        return {"error": "https://api.coingecko.com/api/v3/simple/price?ids= is not available"}
    gecko_data = r.json()
    try:
        for coin in coin_ids_dict:
            coin_id = coin_ids_dict[coin]["coingecko_id"]
            print(coin_id)
            if coin_id != "na" and coin_id != "test-coin":
                coin_ids_dict[coin]["usd_price"] = gecko_data[coin_id]["usd"]
            else:
                coin_ids_dict[coin]["usd_price"] = 0
    except Exception as e:
        print(coingecko_id)
        print(e)
        pass
    return coin_ids_dict


def summary_for_ticker(ticker_summary, path_to_db):
    available_pairs_summary_ticker = get_availiable_pairs(path_to_db)
    summary_data = []
    for pair in available_pairs_summary_ticker:
        if ticker_summary in pair:
            summary_data.append(summary_for_pair(pair, path_to_db))
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


def ticker_for_ticker(ticker_ticker, path_to_db, days_in_past=1):
    available_pairs_ticker = get_availiable_pairs(path_to_db)
    ticker_data = []
    for pair in available_pairs_ticker:
        if ticker_ticker in pair:
            ticker_data.append(ticker_for_pair(pair, path_to_db, days_in_past))
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


def volume_for_ticker(ticker, path_to_db, days):
    ticker_data = ticker_for_ticker(ticker, path_to_db, 1)
    overall_volume = 0
    for pair in ticker_data:
        overall_volume += Decimal(pair[list(pair.keys())[0]]["base_volume"])
    return overall_volume
