from flask import Blueprint, jsonify, request
from oi_cache import get_oi
import time

tv_bp = Blueprint('tv', __name__)

# Словарь для хранения исторических значений OI для расчета изменений
historical_oi = {}

@tv_bp.route("/tv_data")
def tv_data():
    symbol = request.args.get("symbol", "NIFTY")
    current_oi = get_oi(symbol)
    
    if not current_oi:
        return jsonify({"error": "No OI data available"}), 404
    
    # Получаем текущее время и используем его как временную метку
    current_time = int(time.time())
    
    # Если это первый запрос для данного символа, инициализируем исторические данные
    if symbol not in historical_oi:
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
        # Если прошло больше времени, чем интервал, обновляем историческое значение
        if current_time - historical_oi[symbol][interval]["time"] >= seconds:
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
    
    return jsonify({
        "symbol": symbol,
        "current_oi": current_oi,
        "intervals": results
    }) 