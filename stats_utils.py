import requests
import json


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


# list -> decimal
# returning lowest ask from provided orderbook

def find_lowest_ask(orderbook):
    return 0


# returning highest bid from provided orderbook
def find_highest_bid(orderbook):
    return 0
