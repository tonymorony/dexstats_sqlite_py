import unittest
import sys
sys.path.append("..")
import stats_utils


class FindLowestAskTest(unittest.TestCase):

    def test(self):
        orderbook = {}
        lowest_ask = stats_utils.find_lowest_ask(orderbook)
        self.assertEqual(lowest_ask, 0)


class FindHighestBidTest(unittest.TestCase):

    def test(self):
        orderbook = {}
        highest_bid = stats_utils.find_highest_bid(orderbook)
        self.assertEqual(highest_bid, 0)


if __name__ == '__main__':
    unittest.main()
