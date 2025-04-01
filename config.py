import os
import json
import csv
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s [%(levelname)s] %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')

CSV_FILE_PATH = "api-scrip-master.csv"

# Путь к конфигурационному файлу
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# Путь к файлу со списком тикеров и их Security ID
TICKER_SECURITY_ID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Cleaned_Ticker_Security_ID_List.csv')

def find_security_id_from_csv(base_symbol: str, exchange_segment: str = "NSE_FNO") -> int | None:
    """Эта функция отключена, теперь ID должны быть указаны в config.json"""
    print(f"[i] Поиск в CSV отключен. Используйте security_id из config.json для {base_symbol}")
    return None

def get_config():
    """
    Загружает конфигурацию из файла config.json и возвращает словарь.
    """
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logging.error(f"Конфигурационный файл не найден: {CONFIG_FILE}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка декодирования JSON: {e}")
        return {}
    except Exception as e:
        logging.error(f"Неизвестная ошибка при загрузке конфигурации: {e}")
        return {}

def find_security_id(symbol):
    """
    Ищет Security ID для заданного символа в файле TICKER_SECURITY_ID_FILE.
    
    Args:
        symbol (str): Символ тикера для поиска
        
    Returns:
        str: Security ID или None, если не найден
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(TICKER_SECURITY_ID_FILE):
            logging.error(f"Файл со списком тикеров не найден: {TICKER_SECURITY_ID_FILE}")
            return None
        
        # Поиск символа в файле
        with open(TICKER_SECURITY_ID_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Пропускаем заголовок
            
            # Ищем точное соответствие символу
            for row in reader:
                if len(row) >= 3 and row[1].strip() == symbol:
                    security_id = row[2].strip()
                    logging.info(f"Найден Security ID для {symbol}: {security_id}")
                    return security_id
        
        logging.warning(f"Security ID для символа {symbol} не найден")
        return None
    except Exception as e:
        logging.error(f"Ошибка при поиске Security ID для {symbol}: {e}")
        return None

def update_security_ids():
    """
    Обновляет Security ID для всех тикеров в конфигурационном файле.
    """
    try:
        # Загружаем текущую конфигурацию
        config = get_config()
        if not config or 'tickers' not in config:
            logging.error("Конфигурация не содержит список тикеров")
            return False
        
        # Обновляем Security ID для каждого тикера
        updated_count = 0
        for ticker in config['tickers']:
            symbol = ticker.get('symbol')
            if not symbol:
                continue
                
            security_id = find_security_id(symbol)
            if security_id:
                old_id = ticker.get('security_id', 'None')
                ticker['security_id'] = security_id
                logging.info(f"Обновлен Security ID для {symbol}: {old_id} -> {security_id}")
                updated_count += 1
        
        # Сохраняем обновленную конфигурацию
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logging.info(f"Обновлено {updated_count} Security ID в файле конфигурации")
        return True
    except Exception as e:
        logging.error(f"Ошибка при обновлении Security ID: {e}")
        return False

def update_config():
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