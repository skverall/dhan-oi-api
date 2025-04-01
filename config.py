import os
import json
import csv
from datetime import datetime

CSV_FILE_PATH = "api-scrip-master.csv"

def find_security_id_from_csv(base_symbol: str, exchange_segment: str = "NSE_FNO") -> int | None:
    """Ищет security_id для ближайшего фьючерса (индексного или на акцию) в CSV файле."""
    if not os.path.exists(CSV_FILE_PATH):
        print(f"[!] CSV файл не найден: {CSV_FILE_PATH}")
        return None

    nearest_expiry = None
    found_security_id = None
    now = datetime.now()
    # Определяем возможные типы инструментов для фьючерсов
    future_instrument_types = ['FUTIDX', 'FUTSTK'] # Фьючерс на индекс и на акцию

    try:
        with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Проверяем сегмент, тип инструмента и наличие базового символа в торговом символе
                    if (row.get('SEM_EXM_EXCH_ID') == exchange_segment and 
                        row.get('SEM_INSTRUMENT_NAME') in future_instrument_types and 
                        row.get('SEM_TRADING_SYMBOL') and 
                        base_symbol.upper() == row['SM_SYMBOL_NAME'].upper()): # Сверяем базовый символ напрямую
                        
                        expiry_str = row.get('SEM_EXPIRY_DATE')
                        if not expiry_str:
                            continue
                            
                        # Убираем миллисекунды, если они есть
                        if '.' in expiry_str:
                             expiry_str = expiry_str.split('.')[0]
                             
                        # Пробуем разные форматы даты
                        try:
                           expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                           try: 
                               # Попробуем без времени, если предыдущий формат не сработал
                               expiry_date = datetime.strptime(expiry_str.split(' ')[0], '%Y-%m-%d') 
                           except ValueError:
                               # print(f"[!] Не удалось распознать формат даты: {expiry_str} для {row['SEM_TRADING_SYMBOL']}")
                               continue # Пропускаем строки с непонятной датой
                               
                        # Ищем ближайшую дату экспирации в будущем
                        if expiry_date > now:
                            # Проверяем, что это действительно фьючерс (может быть избыточно, но для надежности)
                            is_future = False
                            if row.get('SEM_INSTRUMENT_NAME') in future_instrument_types:
                                is_future = True
                            # Можно добавить более строгую проверку по SEM_TRADING_SYMBOL, если нужно
                            # if not ('-FUT' in row['SEM_TRADING_SYMBOL'].upper() or ' FUT' in row['SEM_TRADING_SYMBOL'].upper()):
                            #    is_future = False 
                                
                            if is_future:
                                if nearest_expiry is None or expiry_date < nearest_expiry:
                                    nearest_expiry = expiry_date
                                    security_id_str = row.get('SEM_SMST_SECURITY_ID')
                                    if security_id_str:
                                        found_security_id = int(security_id_str)
                                    else:
                                        print(f"[!] Отсутствует SEM_SMST_SECURITY_ID для {row['SEM_TRADING_SYMBOL']}")
                                        found_security_id = None # Сбрасываем, если ID отсутствует
                                
                except Exception as e:
                    # Ловим ошибки в обработке конкретной строки
                    print(f"[!] Ошибка обработки строки CSV: {row}. Ошибка: {e}")
                    continue # Переходим к следующей строке
                    
    except FileNotFoundError:
        print(f"[!] CSV файл не найден: {CSV_FILE_PATH}")
        return None
    except Exception as e:
        print(f"[!] Ошибка чтения CSV файла {CSV_FILE_PATH}: {e}")
        return None

    if found_security_id:
         print(f"[+] Найден ID для фьючерса {base_symbol}: {found_security_id} (Экспирация: {nearest_expiry.strftime('%Y-%m-%d') if nearest_expiry else 'N/A'})")
    else:
         print(f"[!] Не найден подходящий фьючерс для {base_symbol} в {CSV_FILE_PATH}")
         
    return found_security_id

def get_config():
    # Приоритет: переменные окружения > config.json > CSV поиск
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

    # 3. Поиск ID в CSV, если не задан в окружении или config.json
    if not env_tickers_str: # Ищем в CSV только если не было DHAN_TICKERS
        updated_tickers = []
        symbols_to_find = {t['symbol']: t for t in config.get('tickers', [])} # Для быстрого поиска по символу
        
        if not symbols_to_find:
             print("[!] Список тикеров пуст. Нечего искать в CSV.")
        else: 
            print("[i] Поиск security_id в CSV...")
            for symbol, ticker_data in symbols_to_find.items():
                # Ищем ID только если он не задан или равен тестовому значению (e.g., 12345)
                current_id = ticker_data.get('security_id')
                needs_search = current_id is None or current_id == 12345 
                
                if needs_search:
                    found_id = find_security_id_from_csv(symbol, ticker_data.get("exchange_segment", "NSE_FNO"))
                    if found_id:
                        ticker_data['security_id'] = found_id
                    else:
                        print(f"[!] Не удалось найти security_id для {symbol} в CSV. Используется ID из config.json (если есть): {current_id}")
                        # Оставляем старый ID, если не нашли новый
                        ticker_data['security_id'] = current_id 
                else:
                     print(f"[i] Для {symbol} уже задан security_id: {current_id}. Пропуск поиска в CSV.")
                
                updated_tickers.append(ticker_data) # Добавляем обновленные или старые данные
            
            config['tickers'] = updated_tickers # Обновляем список тикеров в конфиге
            
    # Проверка наличия обязательных полей
    required_keys = ['token', 'client_id', 'auth_type']
    for key in required_keys:
        if key not in config or not config[key]:
             print(f"[!] Отсутствует обязательный параметр конфигурации: {key}")
             # Можно добавить обработку ошибки, например, выход из программы
             
    if not config.get('tickers'):
        print("[!] Список тикеров пуст. WebSocket не сможет подписаться на данные.")

    return config 