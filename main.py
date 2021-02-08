import sqlite3

from datetime import timedelta
from datetime import datetime
from stats_utils import get_availiable_pairs, summary_for_pair

conn = sqlite3.connect('/DB/43ec929fe30ee72be42c9162c56dde910a05e50d/MM2.db')
conn.row_factory = sqlite3.Row
rpc_password = "123test"

mycur = conn.cursor()

available_pairs = get_availiable_pairs(mycur)

for pair in available_pairs:
    summary_for_pair(pair, rpc_password)