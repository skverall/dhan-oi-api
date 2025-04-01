from flask import Flask, request, jsonify
from oi_cache import get_oi, get_oi_age
from dhan_ws import start_ws
import os
import time
from tv_endpoint import tv_bp

app = Flask(__name__)
app.register_blueprint(tv_bp)

# Глобальный флаг, показывающий состояние WebSocket
websocket_status = {"connected": False, "last_attempt": 0, "error": None}

def init_websocket():
    global websocket_status
    try:
        websocket_status["last_attempt"] = time.time()
        start_ws()
        websocket_status["connected"] = True
        websocket_status["error"] = None
        print("[+] WebSocket подключение инициализировано")
    except Exception as e:
        websocket_status["connected"] = False
        websocket_status["error"] = str(e)
        print(f"[-] Ошибка при запуске WebSocket: {e}")

# Запускаем WebSocket при старте
init_websocket()

@app.route("/get_oi")
def get_oi_endpoint():
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "Ticker parameter is required"}), 400
    
    oi = get_oi(ticker)
    if oi is None:
        # Проверяем возраст данных
        age = get_oi_age(ticker)
        if age is not None:
            return jsonify({
                "error": f"OI data is stale (last update {int(age)} seconds ago)", 
                "symbol": ticker,
                "status": "error"
            }), 503
        else:
            return jsonify({
                "error": f"OI data not available for {ticker}",
                "symbol": ticker,
                "status": "error"
            }), 404
            
    return jsonify({"symbol": ticker, "open_interest": oi, "status": "success"})

@app.route("/")
def index():
    return jsonify({
        "status": "ok", 
        "message": "Dhan OI Server работает", 
        "websocket": websocket_status
    })

@app.route("/status")
def status():
    # Проверяем наличие данных для всех тикеров
    from config import get_config
    config = get_config()
    
    status_data = {
        "server": "running",
        "websocket": websocket_status,
        "tickers": {}
    }
    
    for ticker in config.get("tickers", []):
        symbol = ticker.get("symbol")
        oi = get_oi(symbol)
        age = get_oi_age(symbol)
        
        status_data["tickers"][symbol] = {
            "has_data": oi is not None,
            "last_update_age": int(age) if age is not None else None,
            "data_fresh": age is not None and age < 60 if age is not None else False
        }
    
    return jsonify(status_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
