import flask
from stats_utils import get_availiable_pairs, summary_for_pair, ticker_for_pair

app = flask.Flask(__name__)

#available_pairs = get_availiable_pairs(mycur)

# for pair in available_pairs:
#     summary_for_pair(pair, rpc_password)

@app.route('/api/v1/summary', methods=['GET'])
def summary():
    # TODO: get data for all pairs - have to activate all coins first :)
    summary_data = summary_for_pair(("RICK", "MORTY"), '/DB/43ec929fe30ee72be42c9162c56dde910a05e50d/MM2.db')
    return flask.jsonify(summary_data)


@app.route('/api/v1/ticker', methods=['GET'])
def ticker():
    # TODO: get data for all pairs - have to activate all coins first :)
    ticker_data = ticker_for_pair(("RICK", "MORTY"), '/DB/43ec929fe30ee72be42c9162c56dde910a05e50d/MM2.db')
    return flask.jsonify(ticker_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
