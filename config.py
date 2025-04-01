import os
import json

def get_config():
    # Приоритет: переменные окружения > config.json
    config = {}
    
    # Чтение из файла config.json
    if os.path.exists("config.json"):
        with open("config.json") as f:
            config = json.load(f)
    
    # Переопределение из переменных окружения
    if os.environ.get("DHAN_TOKEN"):
        config["token"] = os.environ.get("DHAN_TOKEN")
    
    if os.environ.get("DHAN_CLIENT_ID"):
        config["client_id"] = os.environ.get("DHAN_CLIENT_ID")
    
    if os.environ.get("DHAN_AUTH_TYPE"):
        config["auth_type"] = int(os.environ.get("DHAN_AUTH_TYPE"))
    
    # Настройка тикеров через переменные окружения (формат: SYMBOL:EXCHANGE:SECURITY_ID,...)
    if os.environ.get("DHAN_TICKERS"):
        tickers = []
        for ticker_str in os.environ.get("DHAN_TICKERS").split(","):
            parts = ticker_str.split(":")
            if len(parts) == 3:
                tickers.append({
                    "symbol": parts[0],
                    "exchange_segment": parts[1],
                    "security_id": int(parts[2])
                })
        if tickers:
            config["tickers"] = tickers
    
    return config 