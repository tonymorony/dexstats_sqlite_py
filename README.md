# dexstats_sqlite_py

![image](https://user-images.githubusercontent.com/24797699/109954887-7030db00-7d14-11eb-9b4d-b384082c0705.png)

The goal of this project is to provide all required data from AtomicDEX network to match [CMC "Ideal endpoint"](https://docs.google.com/document/d/1S4urpzUnO2t7DmS_1dc4EL4tgnnbTObPYXvDeBnukCg/edit#) criteria. python3.7+ and pip requirements from `requirements.txt` needed.

As data source using AtomicDEX-API SQLite (https://github.com/KomodoPlatform/atomicDEX-API/pull/796). 

It also requires https://github.com/KomodoPlatform/atomicDEX-API running on the same host for orderbooks retreiving (supposed to work on seednode which collecting swap statuses). For remote connection tweak `mm2_host` in `stats_utils.py`

Currrent production URL: https://stats-api.atomicdex.io/docs#/
