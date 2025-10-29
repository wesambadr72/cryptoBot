import random
import string
from datetime import datetime

def price_change(old_price, new_price):
    return ((new_price - old_price) / old_price) * 100

def format_percentage(value):
    return f"{value:.2f}%"

def format_message(symbol, change, price):
    return f"{symbol}: تغير {format_percentage(change)} والسعر الحالي {price:.2f} USDT"

def generate_order_id(prefix="sub", user_id=None, plan_type=None, duration=None):
    rand_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}_{user_id}_{plan_type}_{duration}_{rand_part}_{ts}"




def is_subscription_active(sub_row):
    # sub_row = (user_id, username, join_date, expiry, active)
    if not sub_row: return False
    return sub_row[4] == 1 and datetime.now() < datetime.strptime(sub_row[3], '%Y-%m-%d %H:%M:%S')
