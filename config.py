import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in .env file")

from setup_database import load_watched_coins, add_coin, remove_coin
#ALERTS
# قائمة العملات المراد مراقبتها
COINS_TO_WATCH = load_watched_coins()

# إذا كانت القائمة فارغة، أضف العملات الافتراضية
if not COINS_TO_WATCH:
    initial_coins = [
        'ZBCNUSDT', 'HUSDT', 'OGUSDT', 'ELXUSDT', 'ICEUSDT',
        'API3USDT', 'ZENUSDT', 'LIONUSDT', 'IDEXUSDT', 'HUMAUSDT',
        'DOLOUSDT', 'ENATUSDT', 'AUSDT', 'AVEOUSDT', 'LQTYUSDT',
        'PUNDIXUSDT', 'ARBUSDT', 'PENDLEUSDT', 'RAYUSDT', 'WLDUSDT',
        'LISTAUSDT', 'TNSRUSDT', 'GALAUSDT', 'XLMUSDT', 'LAUSDT',
        'ETHFIUSDT', 'EIGENUSDT', 'TWTUSDT', 'JTOUSDT', 'AWEUSDT',
        'NEARUSDT','FILUSDT', 'LDOUSDT', 'IMXUSDT', 'STXUSDT',
        'FETUSDT', 'SCRTUSDT', 'CFXUSDT', 'GRTUSDT', 'DUSKUSDT',
        'NKNUSDT', 'CELRUSDT', 'DEXEUSDT', 'APTUSDT', 'NEOUSDT', 'SKYUSDT'
    ]
    for coin in initial_coins:
        add_coin(coin)
    COINS_TO_WATCH = load_watched_coins()


#NEWS

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://cryptoslate.com/feed"
]