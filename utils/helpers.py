import random
import string
import html
import re
from datetime import datetime, timedelta

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



def is_payment_expired(created_at, timeout_minutes=20):
    created = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    return datetime.now() > created + timedelta(minutes=timeout_minutes)


def strip_html_tags_and_unescape_entities(text: str) -> str:
    TAG_RE = re.compile(r'<[^>]+>')
    """
    يزيل علامات HTML ويفك تشفير كيانات HTML من النص.
    """
    if not isinstance(text, str):
        return ""
    # فك تشفير كيانات HTML أولاً
    unescaped_text = html.unescape(text)
    # ثم إزالة علامات HTML
    return TAG_RE.sub('', unescaped_text)
