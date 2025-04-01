import websocket
import threading
import json
import struct
import time
from oi_cache import set_oi
from config import get_config

config = get_config()

def on_message(ws, message):
    for ticker in config["tickers"]:
        symbol = ticker["symbol"]
        try:
            oi_bytes = message[35:39]
            oi = struct.unpack('>I', oi_bytes)[0]
            set_oi(symbol, oi)
            print(f"[+] Updated OI for {symbol}: {oi}")
        except Exception as e:
            print(f"[-] Error parsing OI: {e}")

def on_error(ws, error):
    print(f"[-] WebSocket ошибка: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[-] WebSocket закрыт: {close_status_code} - {close_msg}")
    print("[*] Попытка переподключения через 5 секунд...")
    time.sleep(5)
    start_ws()

def on_open(ws):
    print("[+] WebSocket connected, subscribing...")
    sub_msg = {
        "RequestCode": 15,
        "InstrumentCount": len(config["tickers"]),
        "InstrumentList": [
            {
                "ExchangeSegment": ticker["exchange_segment"],
                "SecurityId": ticker["security_id"]
            } for ticker in config["tickers"]
        ]
    }
    ws.send(json.dumps(sub_msg))

def start_ws():
    url = f"wss://api-feed.dhan.co?version=2&token={config['token']}&clientId={config['client_id']}&authType={config['auth_type']}"
    ws = websocket.WebSocketApp(url, 
                               on_open=on_open, 
                               on_message=on_message,
                               on_error=on_error,
                               on_close=on_close)
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    return ws
