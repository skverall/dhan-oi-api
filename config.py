import os
import json
import csv
from datetime import datetime

CSV_FILE_PATH = "api-scrip-master.csv"

def find_security_id_from_csv(base_symbol: str, exchange_segment: str = "NSE_FNO") -> int | None:
    """Эта функция отключена, теперь ID должны быть указаны в config.json"""
    print(f"[i] Поиск в CSV отключен. Используйте security_id из config.json для {base_symbol}")
    return None

def get_config():
    # Приоритет: переменные окружения > config.json
    config = {}
    
    # 1. Чтение из файла config.json (базовые настройки)
    if os.path.exists("config.json"):
        try:
            with open("config.json") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[!] Ошибка чтения config.json: {e}")
        except Exception as e:
             print(f"[!] Не удалось прочитать config.json: {e}")
             
    # Убедимся, что tickers существует и является списком
    if 'tickers' not in config or not isinstance(config.get('tickers'), list):
        config['tickers'] = [] # Инициализируем пустым списком, если не существует или не список
        
    # 2. Переопределение из переменных окружения (высший приоритет)
    if os.environ.get("DHAN_TOKEN"):
        config["token"] = os.environ.get("DHAN_TOKEN")
    
    if os.environ.get("DHAN_CLIENT_ID"):
        config["client_id"] = os.environ.get("DHAN_CLIENT_ID")
    
    if os.environ.get("DHAN_AUTH_TYPE"):
        try:
            config["auth_type"] = int(os.environ.get("DHAN_AUTH_TYPE"))
        except ValueError:
             print(f"[!] Неверное значение для DHAN_AUTH_TYPE: {os.environ.get('DHAN_AUTH_TYPE')}")
             
    env_tickers_str = os.environ.get("DHAN_TICKERS")
    if env_tickers_str:
        tickers_from_env = []
        for ticker_str in env_tickers_str.split(","):
            parts = ticker_str.strip().split(":")
            if len(parts) == 3:
                try:
                   tickers_from_env.append({
                        "symbol": parts[0],
                        "exchange_segment": parts[1],
                        "security_id": int(parts[2])
                    })
                except ValueError:
                     print(f"[!] Неверный security_id в DHAN_TICKERS для {parts[0]}")
                except Exception as e:
                     print(f"[!] Ошибка парсинга DHAN_TICKERS: {ticker_str}, Ошибка: {e}")
            else:
                 print(f"[!] Неверный формат тикера в DHAN_TICKERS: {ticker_str}")
        # Если из окружения пришли тикеры, они заменяют все предыдущие
        if tickers_from_env:
            config["tickers"] = tickers_from_env
            print("[+] Используются тикеры из переменных окружения DHAN_TICKERS.")

    # 3. Валидация security_id
    updated_tickers = []
    for ticker_data in config.get('tickers', []):
        symbol = ticker_data.get('symbol', '')
        # Предупреждаем, если security_id отсутствует или равен null
        if ticker_data.get('security_id') is None:
            print(f"[!] Внимание: security_id не указан для {symbol}. Подписка на данные для этого тикера не будет работать.")
        # Добавляем тикер в обновленный список в любом случае
        updated_tickers.append(ticker_data)
    
    config['tickers'] = updated_tickers

    # Проверка наличия обязательных полей
    required_keys = ['token', 'client_id', 'auth_type']
    for key in required_keys:
        if key not in config or not config[key]:
             print(f"[!] Отсутствует обязательный параметр конфигурации: {key}")
             # Можно добавить обработку ошибки, например, выход из программы
             
    if not config.get('tickers'):
        print("[!] Список тикеров пуст. WebSocket не сможет подписаться на данные.")

    return config 