from flask import Blueprint, jsonify, request
from oi_cache import get_oi, get_oi_age
import time
import logging
import json
import os
from config import get_config, find_security_id

# Настраиваем логирование (будет использовать конфигурацию из app.py)
logger = logging.getLogger(__name__)

tv_bp = Blueprint('tv', __name__)

# Словарь для хранения исторических значений OI для расчета изменений
historical_oi = {}

# Путь к конфигурационному файлу
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# Кэш для хранения найденных security_id (чтобы не искать повторно)
security_id_cache = {}

@tv_bp.route("/tv_data")
def tv_data():
    try:
        symbol = request.args.get("symbol", "NIFTY")
        logger.info(f"Запрос данных для TradingView: {symbol}")
        
        # Проверяем наличие тикера в настройках
        config = get_config()
        ticker_config = next((ticker for ticker in config.get('tickers', []) 
                        if ticker.get('symbol') == symbol), None)
        
        # Если тикера нет в конфигурации - автоматически находим его Security ID
        if not ticker_config:
            logger.info(f"Тикер {symbol} не найден в конфигурации. Выполняем автоматический поиск Security ID...")
            
            # Проверяем кэш сначала
            if symbol in security_id_cache:
                security_id = security_id_cache[symbol]
                logger.info(f"Найден Security ID для {symbol} в кэше: {security_id}")
            else:
                # Ищем Security ID в файле
                security_id = find_security_id(symbol)
                
                if security_id:
                    # Сохраняем в кэш для будущих запросов
                    security_id_cache[symbol] = security_id
                    
                    # Добавляем новый тикер в конфигурацию
                    new_ticker = {
                        "symbol": symbol,
                        "exchange_segment": "NSE_FNO",
                        "security_id": security_id
                    }
                    
                    # Добавляем новый тикер в список
                    config['tickers'].append(new_ticker)
                    
                    # Сохраняем обновленную конфигурацию
                    try:
                        with open(CONFIG_FILE, 'w') as f:
                            json.dump(config, f, indent=2)
                        logger.info(f"Конфигурация обновлена: добавлен новый тикер {symbol} с Security ID {security_id}")
                        
                        # Перезапускаем WebSocket для подписки на новый тикер
                        from dhan_ws import restart_ws
                        restart_ws()
                        logger.info(f"WebSocket перезапущен для подписки на тикер {symbol}")
                    except Exception as e:
                        logger.error(f"Ошибка при сохранении конфигурации: {e}")
                else:
                    logger.warning(f"Security ID для тикера {symbol} не найден")
        
        # Получаем данные OI
        current_oi = get_oi(symbol)
        
        # Улучшенная обработка ошибок
        if not current_oi:
            # Проверяем возраст данных для более информативного сообщения
            age = get_oi_age(symbol)
            if age is not None:
                error_msg = f"OI data is stale (last update {int(age)} seconds ago)"
                logger.warning(f"{error_msg} для {symbol}")
                return jsonify({
                    "error": error_msg, 
                    "symbol": symbol,
                    "status": "error",
                    "error_code": "STALE_DATA"
                }), 503  # Service Unavailable
            else:
                error_msg = f"No OI data available for {symbol}"
                logger.warning(error_msg)
                return jsonify({
                    "error": error_msg, 
                    "symbol": symbol,
                    "status": "error",
                    "error_code": "NO_DATA"
                }), 404  # Not Found
        
        # Получаем текущее время и используем его как временную метку
        current_time = int(time.time())
        
        # Если это первый запрос для данного символа, инициализируем исторические данные
        if symbol not in historical_oi:
            logger.info(f"Инициализация исторических данных для {symbol}")
            historical_oi[symbol] = {
                "15min": {"time": current_time, "oi": current_oi},
                "45min": {"time": current_time, "oi": current_oi},
                "75min": {"time": current_time, "oi": current_oi},
                "2hours": {"time": current_time, "oi": current_oi},
                "4hours": {"time": current_time, "oi": current_oi}
            }
        
        # Обновляем исторические данные на основе прошедшего времени
        intervals = {
            "15min": 15 * 60,
            "45min": 45 * 60,
            "75min": 75 * 60,
            "2hours": 2 * 60 * 60,
            "4hours": 4 * 60 * 60
        }
        
        results = {}
        
        for interval, seconds in intervals.items():
            try:
                # Если прошло больше времени, чем интервал, обновляем историческое значение
                if current_time - historical_oi[symbol][interval]["time"] >= seconds:
                    old_oi = historical_oi[symbol][interval]["oi"]
                    oi_change_pct = ((current_oi - old_oi) / old_oi * 100) if old_oi else 0
                    logger.debug(f"Обновление интервала {interval} для {symbol}: изменение OI {oi_change_pct:.2f}%")
                    
                    # Обновляем историческое значение
                    historical_oi[symbol][interval] = {"time": current_time, "oi": current_oi}
                else:
                    # Используем текущие исторические данные для расчета изменения
                    old_oi = historical_oi[symbol][interval]["oi"]
                    oi_change_pct = ((current_oi - old_oi) / old_oi * 100) if old_oi else 0
                
                results[interval] = {
                    "oi": current_oi,
                    "oi_change_pct": round(oi_change_pct, 2)
                }
            except Exception as e:
                logger.error(f"Ошибка при расчете изменения OI для {symbol} в интервале {interval}: {e}")
                results[interval] = {
                    "oi": current_oi,
                    "oi_change_pct": 0.0  # По умолчанию, если произошла ошибка
                }
        
        response_data = {
            "symbol": symbol,
            "current_oi": current_oi,
            "intervals": results,
            "status": "success",
            "last_update": current_time
        }
        
        logger.info(f"Успешно отправлены данные для {symbol}")
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Необработанная ошибка в tv_data для {request.args.get('symbol', 'Unknown')}: {e}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}", 
            "symbol": request.args.get("symbol", "Unknown"),
            "status": "error",
            "error_code": "SERVER_ERROR"
        }), 500 