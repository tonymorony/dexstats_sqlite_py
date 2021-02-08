import sqlite3
import flask
from datetime import timedelta
from datetime import datetime
from stats_utils import get_availiable_pairs, summary_for_pair

app = flask.Flask(__name__)
rpc_password = "123test"

#available_pairs = get_availiable_pairs(mycur)

# for pair in available_pairs:
#     summary_for_pair(pair, rpc_password)

@app.route('/api/v1/summary', methods=['GET'])
def summary():
    print(summary_for_pair(("RICK", "MORTY"), rpc_password, '/DB/43ec929fe30ee72be42c9162c56dde910a05e50d/MM2.db'))
    return flask.jsonify(data)
