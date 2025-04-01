from flask import Flask, request, jsonify
from oi_cache import get_oi
from dhan_ws import start_ws
import os

app = Flask(__name__)

try:
    start_ws()
    print("[+] WebSocket подключение инициализировано")
except Exception as e:
    print(f"[-] Ошибка при запуске WebSocket: {e}")
    # Продолжаем работу API даже если веб-сокет не запустился

@app.route("/get_oi")
def get_oi_endpoint():
    ticker = request.args.get("ticker")
    oi = get_oi(ticker)
    if oi is None:
        return jsonify({"error": "OI not available"}), 404
    return jsonify({"symbol": ticker, "open_interest": oi})

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "Dhan OI Server работает"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
