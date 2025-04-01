import time

oi_data = {}
last_update = {}
MAX_AGE_SECONDS = 60  # Максимальное время актуальности данных (1 минута)

def set_oi(symbol, value):
    oi_data[symbol] = value
    last_update[symbol] = time.time()

def get_oi(symbol):
    # Проверка наличия данных в кэше
    if symbol not in oi_data:
        print(f"[-] Нет данных OI для {symbol}")
        return None
    
    # Проверка свежести данных
    if symbol in last_update:
        age = time.time() - last_update[symbol]
        if age > MAX_AGE_SECONDS:
            print(f"[-] Данные OI для {symbol} устарели ({int(age)} сек)")
            return None
    
    return oi_data.get(symbol, None)

def get_oi_age(symbol):
    """Возвращает возраст данных в секундах или None, если данных нет"""
    if symbol in last_update:
        return time.time() - last_update[symbol]
    return None
