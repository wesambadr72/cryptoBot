import asyncio
import nest_asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN, COINS_TO_WATCH
from handlers import start, news, portfolio, trade, help_command, alerts
from jobs.alerts import check_prices
from jobs.news import news_job
from jobs.portfolio import portfolio_job
from jobs.stoploss import stoploss_job
from utils.logging import logger
from setup_database import add_coin, remove_coin
logger.info("Bot is starting...")



async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    logger.info("CommandHandler for 'start' added")

    app.add_handler(CommandHandler("alerts", alerts))
    logger.info("CommandHandler for 'alerts' added")

    app.add_handler(CommandHandler("news", news))
    logger.info("CommandHandler for 'news' added")

    app.add_handler(CommandHandler("portfolio", portfolio))
    logger.info("CommandHandler for 'portfolio' added")

    app.add_handler(CommandHandler("trade", trade))
    logger.info("CommandHandler for 'trade' added")
    
    app.add_handler(CommandHandler("help", help_command))
    logger.info("CommandHandler for 'help' added")

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, coin_handler))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_prices, "interval", minutes=15, args=[app])
    # scheduler.add_job(news_job, "interval", hours=1, args=[app])
    # scheduler.add_job(portfolio_job, "interval", hours=2, args=[app])
    # scheduler.add_job(stoploss_job, "interval", minutes=10, args=[app])
    scheduler.start()

    logger.info("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())


async def button_handler(update, context):
    query = update.callback_query
    query.answer()

    if query.data == 'add_coin':
        await query.edit_message_text(text="أدخل اسم العملة للإضافة (مثل BTCUSDT):")
        context.user_data['action'] = 'add_coin'
    elif query.data == 'remove_coin':
        await query.edit_message_text(text="أدخل اسم العملة للإزالة:")
        context.user_data['action'] = 'remove_coin'


async def coin_handler(update, context):
    if 'action' in context.user_data:
        coin = update.message.text.upper()
        action = context.user_data['action']
        if action == 'add_coin':
            add_coin(coin)
            if coin not in COINS_TO_WATCH:
                COINS_TO_WATCH.append(coin)
            await update.message.reply_text(f"تم إضافة {coin} إلى القائمة.")
        elif action == 'remove_coin':
            remove_coin(coin)
            if coin in COINS_TO_WATCH:
                COINS_TO_WATCH.remove(coin)
            await update.message.reply_text(f"تم إزالة {coin} من القائمة.")
        del context.user_data['action']
