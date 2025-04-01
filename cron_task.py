import requests
import time
import logging
from oi_cache import get_oi, set_oi
from config import get_config
import random

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_historical_data():
    """
    Функция для периодического обновления исторических данных OI
    Она будет имитировать запросы TradingView к нашему API
    """
    try:
        config = get_config()
        
        # Перебираем все настроенные тикеры
        for ticker in config["tickers"]:
            symbol = ticker["symbol"]
            
            # Получаем текущий OI
            current_oi = get_oi(symbol)
            
            if current_oi is None:
                logger.warning(f"OI для {symbol} недоступен")
                continue
                
            logger.info(f"Обновляем исторические данные для {symbol}, текущий OI: {current_oi}")
            
            # Обращаемся к нашему собственному API endpoint, как это делал бы TradingView
            # Это обновит исторические данные для расчета изменений OI
            timeframes = ["15", "45", "75", "120", "240"]  # Соответствуют настройкам в индикаторе
            url = f"http://localhost:5000/tv_data?symbol={symbol}&timeframes={','.join(timeframes)}"
            
            try:
                # В локальной разработке используем localhost
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Данные успешно обновлены для {symbol}")
                    logger.debug(response.json())
                else:
                    logger.error(f"Ошибка при обновлении данных: {response.status_code}")
            except requests.RequestException as e:
                # В production, когда скрипт запускается на том же сервере что и API,
                # Мы можем напрямую вызвать соответствующую функцию
                logger.info(f"Локальный запрос не удался, пробуем прямой вызов API функций: {e}")
                from tv_endpoint import update_historical_oi
                update_historical_oi(symbol, timeframes)
                logger.info(f"Прямой вызов API функции выполнен для {symbol}")
                
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных: {e}")

if __name__ == "__main__":
    logger.info("Запуск скрипта обновления исторических данных OI")
    
    # Бесконечный цикл для регулярного обновления
    while True:
        update_historical_data()
        # Пауза между обновлениями (1 минута)
        logger.info("Ожидание до следующего обновления...")
        time.sleep(60) 