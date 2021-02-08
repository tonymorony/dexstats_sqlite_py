import unittest
import sys
sys.path.append("..")
import stats_utils
import json


class FindLowestAskTest(unittest.TestCase):

    def test(self):
        with open("fixtures/orderbook_btc_kmd.json") as orderbook_json:
            orderbook_fixture = json.load(orderbook_json)
        lowest_ask = stats_utils.find_lowest_ask(orderbook_fixture)
        self.assertEqual(lowest_ask, "48626.15089487")


class FindHighestBidTest(unittest.TestCase):

    def test(self):
        with open("fixtures/orderbook_btc_kmd.json") as orderbook_json:
            orderbook_fixture = json.load(orderbook_json)
        highest_bid = stats_utils.find_highest_bid(orderbook_fixture)
        self.assertEqual(highest_bid, "44984.25551057130004498425551057130004498425551057130004498425551057130004498425551057130004498425551")


if __name__ == '__main__':
    unittest.main()
