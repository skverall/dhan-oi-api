import websocket
import threading
import json
import struct
import time
import logging
from oi_cache import set_oi
from config import get_config

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s [%(levelname)s] %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')

# Загружаем конфигурацию
try:
    config = get_config()
except Exception as e:
    logging.critical(f"Не удалось загрузить конфигурацию: {e}")
    config = {"tickers": []}

# Глобальная переменная для хранения экземпляра WebSocket
ws_instance = None
reconnect_attempt = 0
MAX_RECONNECT_ATTEMPTS = 10
reconnect_delay = 5  # начальная задержка в секундах

def on_message(ws, message):
    global reconnect_attempt
    reconnect_attempt = 0  # Сбрасываем счетчик при успешном получении сообщения
    
    if len(config["tickers"]) == 0:
        logging.warning("Список тикеров пуст, нет данных для обработки")
        return
    
    for ticker in config["tickers"]:
        symbol = ticker["symbol"]
        try:
            # Проверка длины сообщения
            if len(message) < 39:
                logging.warning(f"Полученное сообщение слишком короткое: {len(message)} байт")
                continue
                
            oi_bytes = message[35:39]
            oi = struct.unpack('>I', oi_bytes)[0]
            set_oi(symbol, oi)
            logging.info(f"Обновлен OI для {symbol}: {oi}")
        except Exception as e:
            logging.error(f"Ошибка при парсинге OI для {symbol}: {e}")

def on_error(ws, error):
    logging.error(f"WebSocket ошибка: {error}")

def on_close(ws, close_status_code, close_msg):
    global reconnect_attempt, reconnect_delay
    
    logging.warning(f"WebSocket закрыт: {close_status_code} - {close_msg}")
    
    # Увеличиваем счетчик попыток и задержку между попытками (экспоненциальный backoff)
    reconnect_attempt += 1
    current_delay = min(reconnect_delay * (2 ** (reconnect_attempt - 1)), 300)  # максимум 5 минут
    
    if reconnect_attempt <= MAX_RECONNECT_ATTEMPTS:
        logging.info(f"Попытка переподключения {reconnect_attempt}/{MAX_RECONNECT_ATTEMPTS} через {current_delay} секунд...")
        time.sleep(current_delay)
        start_ws()
    else:
        logging.critical(f"Достигнуто максимальное количество попыток подключения ({MAX_RECONNECT_ATTEMPTS}). Прекращаем попытки.")

def on_open(ws):
    global reconnect_attempt
    reconnect_attempt = 0  # Сбрасываем счетчик при успешном подключении
    
    logging.info("WebSocket соединение установлено, подписываемся на данные...")
    
    if len(config["tickers"]) == 0:
        logging.warning("Список тикеров пуст, невозможно подписаться на данные")
        return
        
    # Проверяем наличие security_id для всех тикеров
    valid_tickers = []
    for ticker in config["tickers"]:
        if ticker.get("security_id") is not None:
            valid_tickers.append(ticker)
        else:
            logging.warning(f"Тикер {ticker.get('symbol')} не имеет security_id, пропускаем")
    
    if len(valid_tickers) == 0:
        logging.warning("Нет валидных тикеров с security_id, невозможно подписаться на данные")
        return
        
    try:
        sub_msg = {
            "RequestCode": 15,
            "InstrumentCount": len(valid_tickers),
            "InstrumentList": [
                {
                    "ExchangeSegment": ticker["exchange_segment"],
                    "SecurityId": ticker["security_id"]
                } for ticker in valid_tickers
            ]
        }
        ws.send(json.dumps(sub_msg))
        logging.info(f"Отправлен запрос на подписку для {len(valid_tickers)} тикеров")
    except Exception as e:
        logging.error(f"Ошибка при отправке запроса на подписку: {e}")

def start_ws():
    global ws_instance
    
    try:
        if not config.get("token") or not config.get("client_id") or not config.get("auth_type"):
            logging.critical("Отсутствуют обязательные параметры аутентификации (token, client_id, auth_type)")
            return None
            
        url = f"wss://api-feed.dhan.co?version=2&token={config['token']}&clientId={config['client_id']}&authType={config['auth_type']}"
        
        # Закрываем предыдущее соединение, если оно существует
        if ws_instance:
            try:
                ws_instance.close()
                logging.info("Закрыто предыдущее WebSocket соединение")
            except:
                pass
        
        ws = websocket.WebSocketApp(url, 
                                   on_open=on_open, 
                                   on_message=on_message,
                                   on_error=on_error,
                                   on_close=on_close)
        
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        ws_instance = ws
        logging.info("WebSocket соединение запущено в отдельном потоке")
        return ws
    except Exception as e:
        logging.critical(f"Критическая ошибка при запуске WebSocket: {e}")
        return None
