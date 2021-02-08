import requests
import json
from decimal import Decimal


# tuple, string, string -> list
# returning orderbook for given trading pair
def get_mm2_orderbook_for_pair(pair, mm2_rpc_password):
    mm2_host = "http://127.0.0.1:7783"
    params = {
              'userpass': mm2_rpc_password,
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
