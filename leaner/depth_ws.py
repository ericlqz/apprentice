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
    # tickers = fetch_tickers()
    # print(tickers)
    # for ticker in tickers:
    #     ws.send(json.dumps({"op": "sub", "topic": 'depth:0:' + ticker}))
    ws.send(json.dumps({"op": "sub", "topic": 'depth:0:AKRO-USDT'}))
    ws.send(json.dumps({"op": "sub", "topic": 'depth:0:NSURE-USDT'}))
    ws.send(json.dumps({"op": "sub", "topic": 'depth:0:BTC-USDT'}))
    ws.send(json.dumps({"op": "sub", "topic": 'depth:0:XSUTER-USDT'}))

def save_data(data):
    # print(data)
    message_json = json.loads(data)
    if not ('asks' in message_json or 'bids' in message_json): return

    data = {}
    data["@timestamp"]=datetime.datetime.fromtimestamp((message_json["timestamp"]-8*60*60*1000)/1000).isoformat()
    data["tpp"]=int(message_json["tpp"])
    data['symbol']=message_json['symbol']
    data['topic']=message_json['topic']
    data['ask_price_1']=float(message_json['asks'][0]['price']) if 'asks' in message_json else 0.0
    data['ask_quantity_1']=float(message_json['asks'][0]['quantity']) if 'asks' in message_json else 0.0
    data['bid_price_1']=float(message_json['bids'][0]['price']) if 'bids' in message_json else 0.0
    data['bid_quantity_1']=float(message_json['bids'][0]['quantity']) if 'bids' in message_json else 0.0

    print(data)
    res = es.index(index="depth_hoo", body=data)

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
