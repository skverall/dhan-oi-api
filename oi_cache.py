oi_data = {}

def set_oi(symbol, value):
    oi_data[symbol] = value

def get_oi(symbol):
    return oi_data.get(symbol, None)
