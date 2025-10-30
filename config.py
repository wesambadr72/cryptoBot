import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

MAIN_BOT_TOKEN = os.getenv("TELEGRAM_MAIN_TOKEN")
SUBS_BOT_TOKEN = os.getenv("TELEGRAM_SUBSCRIPTONS_TOKEN")
SUBS_BOT_USERNAME = os.getenv("BOT_USERNAME")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
NOWPAYMENTS_API_KEY = os.getenv('NOWPAYMENTS_API_KEY')
NOWPAYMENTS_IPN_KEY= os.getenv('NOWPAYMENTS_IPN_SECRET')

if not SUBS_BOT_TOKEN:
    raise ValueError("TELEGRAM_SUBSCRIPTONS_TOKEN is not set in .env file")

from setup_database import load_watched_coins, add_coin, remove_coin
#ALERTS
# قائمة العملات المراد مراقبتها
COINS_TO_WATCH = load_watched_coins()

# إذا كانت القائمة فارغة، أضف العملات الافتراضية
if not COINS_TO_WATCH:
    initial_coins = [
        # Top 25 - العملات الأساسية (القيمة السوقية العالية)
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
        'ADAUSDT', 'DOGEUSDT', 'TRXUSDT', 'TONUSDT', 'LINKUSDT',
        'MATICUSDT', 'DOTUSDT', 'LTCUSDT', 'AVAXUSDT', 'SHIBUSDT',
        'UNIUSDT', 'ATOMUSDT', 'APTUSDT', 'FILUSDT', 'INJUSDT',
        'NEARUSDT', 'ARBUSDT', 'OPUSDT', 'SUIUSDT', 'HBARUSDT',
        
        # 26-50 - عملات قوية متوسطة
        'RNDRUSDT', 'STXUSDT', 'IMXUSDT', 'ALGOUSDT', 'ARUSDT',
        'FTMUSDT', 'ICPUSDT', 'VETUSDT', 'GRTUSDT', 'RUNEUSDT',
        'THETAUSDT', 'XLMUSDT', 'SANDUSDT', 'AXSUSDT', 'MANAUSDT',
        'AAVEUSDT', 'EOSUSDT', 'FLOWUSDT', 'EGLDUSDT', 'MKRUSDT',
        'CFXUSDT', 'QNTUSDT', 'BEAMUSDT', 'TIAUSDT', 'FETUSDT',
        
        # 51-75 - عملات Layer 2 و DeFi
        'LDOUSDT', 'PENDLEUSDT', 'SEIUSDT', 'PYTHUSDT', 'WLDUSDT',
        'JTOUSDT', 'JUPUSDT', 'DYDXUSDT', 'PEPEUSDT', 'FLOKIUSDT',
        'RENDERUSDT', 'AGIXUSDT', 'TNSRUSDT', 'GALAUSDT', 'CHZUSDT',
        'ONEUSDT', 'ZILUSDT', 'ENJUSDT', 'COMPUSDT', 'YFIUSDT',
        'SNXUSDT', 'CRVUSDT', 'BNTUSDT', 'KAVAUSDT', 'FXSUSDT',
        
        # 76-100 - عملات واعدة و Gaming/Metaverse
        'GMXUSDT', 'BLURUSDT', 'WIFUSDT', 'ACEUSDT', 'PIXELUSDT',
        'PORTALUSDT', 'XAIUSDT', 'ALTUSDT', 'IQUSDT', 'MINAUSDT',
        'GALUSDT', 'PEOPLEUSDT', 'FLMUSDT', 'ORDIUSDT', '1000SATSUSDT',
        'ETHFIUSDT', 'EIGENUSDT', 'LISTAUSDT', 'ZENUSDT', 'ROSEUSDT',
        'LPTUSDT', 'BANDUSDT', 'CELRUSDT', 'OGNUSDT', 'COTIUSDT',
        
        # 101-125 - عملات إضافية متنوعة
        'CKBUSDT', 'OCEANUSDT', 'ZRXUSDT', 'NMRUSDT', 'BALUSDT',
        'STORJUSDT', 'RLCUSDT', 'AUDIOUSDT', 'CTSIUSDT', 'AKROUSDT',
        'RAYUSDT', 'C98USDT', 'MASKUSDT', 'ATAUSDT', 'DUSKUSDT',
        'CHRUSDT', 'HOLOUSDT', 'TRUUSDT', 'SLPUSDT', 'DASHUSDT',
        'WAXPUSDT', 'ARPAUSDT', 'LRCUSDT', 'PUNDIXUSDT', 'SUPERUSDT'
    ]
    

    for coin in initial_coins:
        add_coin(coin)
    COINS_TO_WATCH = load_watched_coins()


#NEWS

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed"
]


PAYMENTS_PALNS={
    "1_DAY_TRIAL":0.00,
    "1_MONTH":13.99,
    "3_MONTHS":26.99,
    "6_MONTHS":47.99
}

SUPPORTED_NETWORKS = ['TON', 'BEP20']

SUCCESS_URL = f"https://t.me/{SUBS_BOT_USERNAME}"
CANCEL_URL = f"https://t.me/{SUBS_BOT_USERNAME}"

WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://13.61.23.253/webhook/payment')