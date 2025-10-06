from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_API_SECRET

binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

def get_all_prices():
    return binance_client.get_all_tickers()
