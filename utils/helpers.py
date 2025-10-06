def price_change(old_price, new_price):
    return ((new_price - old_price) / old_price) * 100

def format_percentage(value):
    return f"{value:.2f}%"

def format_message(symbol, change, price):
    return f"{symbol}: تغير {format_percentage(change)} والسعر الحالي {price:.2f} USDT"
