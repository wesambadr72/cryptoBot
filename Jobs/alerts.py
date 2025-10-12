from utils.logging import logger
from datetime import datetime
from utils.binance_api import get_all_prices
from setup_database import save_price, get_old_price, already_alerted, save_alert
from setup_database import load_watched_coins
from utils.helpers import price_change as calculate_price_change

async def check_prices(context):
    chat_id = context.bot_data.get('chat_id')
    if not chat_id:
        logger.warning("CHAT_ID is not set. Cannot send alert message.")
        return

    try:
        prices = get_all_prices()
        current_time = datetime.now()

        coins = load_watched_coins()
        for coin in coins:
            try:
                current_price = float(next(p['price'] for p in prices if p['symbol'] == coin))
                save_price(coin, current_price, current_time)

                old_price = get_old_price(coin)
                if not old_price:
                    continue

                price_change = calculate_price_change(old_price, current_price)
                if price_change >= 1.3 and not already_alerted(coin):
                    message = f"🚨 تنبيه! {coin}\n"
                    message += f"السعر السابق: {old_price:.8f}\n"
                    message += f"السعر الحالي: {current_price:.8f}\n"
                    message += f"نسبة التغير: {price_change:.2f}%"

                    await context.bot.send_message(chat_id=chat_id, text=message)
                    save_alert(coin, old_price, current_price, price_change)

            except Exception as e:
                logger.error(f"Error processing {coin}: {str(e)}")

    except Exception as e:
        logger.error(f"Error in check_prices: {str(e)}")
