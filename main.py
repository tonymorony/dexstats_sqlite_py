import sqlite3

from datetime import timedelta
from datetime import datetime
from stats_utils import get_mm2_orderbook_for_pair

conn = sqlite3.connect('/DB/43ec929fe30ee72be42c9162c56dde910a05e50d/MM2.db')

mycur = conn.cursor()

# getting list of available pairs (list of tuples)
mycur.execute("SELECT DISTINCT maker_coin, taker_coin FROM stats_swaps;")
available_pairs = (mycur.fetchall())

# SUMMARY Endpoint
# tuple -> dictionary
# Receiving tuple with base and rel as an argument and producing CMC summary endpoint data


def summary_for_pair(pair):

    # TODO: calculate data
    pair_summary = {"traiding_pair": "", "last_price": 0, "lowest_ask": 0, "highest_bid": 0,
                    "base_volume": 0, "quote_volume": 0, "price_change_percent_24h": 0, "highest_price_24h": 0,
                    "lowest_price_24h": 0}

    pair_summary["trading_pair"] = pair[0] + "_" + pair[1]
    get_mm2_orderbook_for_pair(pair)
    return pair_summary


for pair in available_pairs:
    summary_for_pair(pair)

# # Last 24 hours data
#
# timestamp_right_now = int(datetime.now().strftime("%s"))
# timestamp_24h_ago = int((datetime.now() - timedelta(1)).strftime("%s"))
#
# swaps_last_24h