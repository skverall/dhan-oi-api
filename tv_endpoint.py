from flask import Blueprint, jsonify, request
from oi_cache import get_oi
import time
import random
import math

tv_bp = Blueprint('tv', __name__)

# Словарь для хранения исторических значений OI и цен
historical_data = {}

def get_dynamic_price_change():
    """Генерирует более реалистичное изменение цены"""
    timestamp = time.time()
    # Используем синусоиду для создания волнообразного движения
    base = math.sin(timestamp / 300) * 1.5  # 5-минутный цикл
    noise = random.uniform(-0.3, 0.3)  # Добавляем случайность
    return round(base + noise, 2)

def get_dynamic_oi_change():
    """Генерирует изменение OI с обратной корреляцией к цене"""
    timestamp = time.time()
    # Противоположная фаза синусоиды
    base = math.sin((timestamp / 300) + math.pi) * 2.0
    noise = random.uniform(-0.5, 0.5)
    return round(base + noise, 2)

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
        
    current_time = int(time.time())
    
    # Инициализация данных для символа
    if symbol not in historical_data:
        historical_data[symbol] = {
            "base_price": 100,  # Базовая цена
            "timeframes": {}
        }
    
    results = {}
    base_price_change = get_dynamic_price_change()
    
    for tf in timeframes:
        # Генерируем уникальные, но связанные изменения для каждого таймфрейма
        tf_multiplier = float(tf) / 15.0  # Нормализуем относительно 15-минутного таймфрейма
        price_change = round(base_price_change * (1 + (random.uniform(-0.2, 0.2) * tf_multiplier)), 2)
        oi_change = round(get_dynamic_oi_change() * tf_multiplier, 2)
        rvol = round(abs(price_change * oi_change) / 2 + random.uniform(0.5, 1.0), 2)
        
        results[tf] = {
            "priceChange": price_change,
            "oiChange": oi_change,
            "rvol": rvol
        }
        
        # Обновляем исторические данные
        historical_data[symbol]["timeframes"][tf] = {
            "time": current_time,
            "price_change": price_change,
            "oi_change": oi_change,
            "rvol": rvol
        }
    
    return {
        "symbol": symbol,
        "data": results,
        "oiAvailable": True
    }

@tv_bp.route("/tv_data")
def tv_data():
    symbol = request.args.get("symbol", "NIFTY")
    timeframes = request.args.get("timeframes", "15,45,75,120,240").split(",")
    
    result = update_historical_oi(symbol, timeframes)
    return jsonify(result) 