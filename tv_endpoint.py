from flask import Blueprint, jsonify, request
from oi_cache import get_oi
import time

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
        interval_key = f"{tf}min" if int(tf) < 60 else f"{int(tf)//60}hours"
        if interval_key not in historical_oi[symbol]:
            historical_oi[symbol][interval_key] = {"time": current_time, "oi": current_oi}
    
    # Обновляем исторические данные на основе прошедшего времени
    intervals = {}
    for tf in timeframes:
        tf_int = int(tf)
        if tf_int < 60:
            interval_key = f"{tf}min"
            intervals[interval_key] = tf_int * 60
        else:
            interval_key = f"{tf_int//60}hours"
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
        
        results[interval] = {
            "oi": current_oi,
            "oi_change_pct": round(oi_change_pct, 2)
        }
    
    return {
        "symbol": symbol,
        "current_oi": current_oi,
        "intervals": results
    }

@tv_bp.route("/tv_data")
def tv_data():
    symbol = request.args.get("symbol", "NIFTY")
    timeframes = request.args.get("timeframes", "15,45,75,120,240").split(",")
    
    # Используем общую функцию для обновления и получения данных
    result = update_historical_oi(symbol, timeframes)
    
    if "error" in result:
        return jsonify(result), 404
        
    return jsonify(result) 