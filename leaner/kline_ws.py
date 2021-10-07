# -*- coding: utf-8 -*-

import requests
import time
import hmac
import hashlib
import ujson
import random
import asyncio
import uvloop
import json
import datetime
from elasticsearch import Elasticsearch
import websocket
try:
    import thread
except ImportError:
    import _thread as thread


# host = "https://api.hoo.co"
api_host = "https://api.hoo.co"
host = "wss://api.hoo.co/ws"
client_id = "xNfLx7zAXHs2kC3iY34cWhLnmoR1QU"
client_key = "erQkeAVBqEp186bLLzMSnTFN8D7UGK7sojrPdYf92m5qSRK3Aw"

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

def login():
    ts = int(time.time())
    nonce = "abcdefg"
    obj = {"ts": ts, "nonce": nonce, "sign": "", "client_id": client_id, "op": "apilogin"}
    s = "client_id=%s&nonce=%s&ts=%s" % (client_id, nonce, ts)
    v = hmac.new(client_key.encode(), s.encode(), digestmod=hashlib.sha256)
    obj["sign"] = v.hexdigest()
    return obj

def gen_sign(client_id, client_key):
    ts = int(time.time())
    nonce = "abcdefg"
    obj = {"ts": ts, "nonce": nonce, "sign": "", "client_id": client_id}
    s = "client_id=%s&nonce=%s&ts=%s" % (client_id, nonce, ts)
    v = hmac.new(client_key.encode(), s.encode(), digestmod=hashlib.sha256)
    obj["sign"] = v.hexdigest()
    return obj

def fetch_tickers():
    print("> 获取所有交易对")
    path = "/open/v1/tickers"
    obj = gen_sign(client_id, client_key)
    res = requests.get(api_host + path, params=obj)
    content = ujson.loads(res.content)
    return list(map(lambda x: x['symbol'], sorted(content['data'], key=lambda x: float(x['amount']) if x['amount'] else 0, reverse = True)))
    # return 'BTC-USDT'

def sub_topic(ws):
    # tickers = fetch_tickers()[0:100]
    tickers = fetch_tickers()
    print(tickers)
    for ticker in tickers:
        ws.send(json.dumps({"op": "sub", "topic": 'kline:30Min:' + ticker}))

def save_data(data):
    print(data)
    message_json = json.loads(data)
    if 'op' in message_json: return

    message_json["@timestamp"]=datetime.datetime.fromtimestamp((message_json["timestamp"]-8*60*60*1000)/1000).isoformat()
    message_json['ticks'][0]['close'] = float(message_json['ticks'][0]['close'])
    message_json['ticks'][0]['high'] = float(message_json['ticks'][0]['high'])
    message_json['ticks'][0]['low'] = float(message_json['ticks'][0]['low'])
    message_json['ticks'][0]['open'] = float(message_json['ticks'][0]['open'])
    message_json['ticks'][0]['volume'] = float(message_json['ticks'][0]['volume'])
    message_json['ticks'][0]['turnover'] = float(message_json['ticks'][0]['turnover'])
    message_json['ticks'][0]['timestamp'] = datetime.datetime.fromtimestamp((message_json['ticks'][0]['timestamp']-8*60*60*1000)/1000).isoformat()
    message_json["type"]=int(message_json["type"])
    message_json["tpp"]=int(message_json["tpp"])

    res = es.index(index="kline_30m_hoo", body=message_json)
    # print(res)

def on_open(ws):
    def run(*args):
        obj = login()
        ws.send(json.dumps(obj))
        sub_topic(ws)
        #time.sleep(1)
        #ws.close()
        # print("thread terminating...")
    thread.start_new_thread(run, ())


def on_message(ws, message):
    # print(ws)
    # print(message)
    save_data(message)


def on_error(ws, error):
    print(ws)
    print(error)


def on_close(ws):
    print(ws)
    print("### closed ###")


websocket.enableTrace(True)
ws = websocket.WebSocketApp(host,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)

ws.on_open = on_open
ws.run_forever()
