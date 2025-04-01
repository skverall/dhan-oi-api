from flask import Blueprint, jsonify, request
from oi_cache import get_oi
import time
import random  # Для генерации тестовых данных

tv_bp = Blueprint('tv', __name__)

# Словарь для хранения исторических значений OI для расчета изменений
historical_oi = {}

def update_historical_oi(symbol, timeframes=None):
    """
    Функция для прямого обновления исторических данных OI
    Может вызываться из cron-скрипта или других частей приложения
    
    Args:
        symbol: Символ тикера для обновления
        timeframes: Список таймфреймов в минутах (строки или числа)
    
    Returns:
        dict: Словарь с обновленными данными
    """
    if timeframes is None:
        timeframes = ["15", "45", "75", "120", "240"]
        
    current_oi = get_oi(symbol)
    
    if not current_oi:
        return {"error": "No OI data available", "symbol": symbol}
    
    # Получаем текущее время и используем его как временную метку
    current_time = int(time.time())
    
    # Если это первый запрос для данного символа, инициализируем исторические данные
    if symbol not in historical_oi:
        historical_oi[symbol] = {}
        
    # Убедимся, что все необходимые интервалы инициализированы
    for tf in timeframes:
        interval_key = f"{tf}"  # Упрощаем ключ для соответствия с индикатором
        if interval_key not in historical_oi[symbol]:
            historical_oi[symbol][interval_key] = {"time": current_time, "oi": current_oi}
    
    # Обновляем исторические данные на основе прошедшего времени
    intervals = {}
    for tf in timeframes:
        tf_int = int(tf)
        interval_key = f"{tf}"  # Используем числовое значение как ключ
        intervals[interval_key] = tf_int * 60
    
    results = {}
    
    for interval, seconds in intervals.items():
        # Если прошло больше времени, чем интервал, обновляем историческое значение
        if interval in historical_oi[symbol] and current_time - historical_oi[symbol][interval]["time"] >= seconds:
            old_oi = historical_oi[symbol][interval]["oi"]
            oi_change_pct = ((current_oi - old_oi) / old_oi * 100) if old_oi else 0
            
            # Обновляем историческое значение
            historical_oi[symbol][interval] = {"time": current_time, "oi": current_oi}
        else:
            # Используем текущие исторические данные для расчета изменения
            old_oi = historical_oi[symbol][interval]["oi"]
            oi_change_pct = ((current_oi - old_oi) / old_oi * 100) if old_oi else 0
        
        # Генерируем тестовые данные для priceChange и rvol
        price_change = round(random.uniform(-1.5, 1.5), 2)
        rvol = round(random.uniform(0.5, 1.5), 2)
        
        results[interval] = {
            "priceChange": price_change, 
            "oiChange": round(oi_change_pct, 2),
            "rvol": rvol
        }
    
    # Возвращаем в формате, ожидаемом TradingView индикатором
    return {
        "symbol": symbol,
        "data": results,
        "oiAvailable": True  # Флаг для индикатора, что данные OI доступны
    }

@tv_bp.route("/tv_data")
def tv_data():
    symbol = request.args.get("symbol", "NIFTY")
    timeframes = request.args.get("timeframes", "15,45,75,120,240").split(",")
    
    # Используем общую функцию для обновления и получения данных
    result = update_historical_oi(symbol, timeframes)
    
    if "error" in result:
        return jsonify({
            "symbol": symbol,
            "data": {
                "15": {"priceChange": 0.5, "oiChange": -2.3, "rvol": 0.8},
                "45": {"priceChange": 0.7, "oiChange": 1.2, "rvol": 0.9},
                "75": {"priceChange": 0.3, "oiChange": -1.5, "rvol": 0.5},
                "120": {"priceChange": 0.8, "oiChange": 2.1, "rvol": 0.7},
                "240": {"priceChange": 1.2, "oiChange": 3.5, "rvol": 1.1}
            },
            "oiAvailable": False  # Указываем, что используются тестовые данные
        })
        
    return jsonify(result) 