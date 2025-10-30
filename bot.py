import asyncio
import nest_asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import MAIN_BOT_TOKEN
from handlers import start, news, portfolio, trade, help_command, alerts
from Jobs.alerts import check_prices
from Jobs.news import news_job
# from Jobs.portfolio import portfolio_job
# from Jobs.stoploss import stoploss_job
from utils.logging import logger
from setup_database import add_coin, remove_coin, load_watched_coins
logger.info("Main Bot is starting...")



async def coin_handler(update, context):
    if 'action' in context.user_data:
        coin = update.message.text.upper()
        action = context.user_data['action']
        if action == 'add_coin':
                
            if coin not in load_watched_coins():
                add_coin(coin)
            await update.message.reply_text(f"تم إضافة {coin} إلى القائمة.")
        elif action == 'remove_coin':

            if coin in load_watched_coins():
                remove_coin(coin)
            await update.message.reply_text(f"تم إزالة {coin} من القائمة.")
        del context.user_data['action']

async def button_handler(update, context):
    query = update.callback_query
    query.answer()

    if query.data == 'add_coin':
        await query.edit_message_text(text="أدخل اسم العملة للإضافة (مثل BTCUSDT):")
        context.user_data['action'] = 'add_coin'
    elif query.data == 'remove_coin':
        await query.edit_message_text(text="أدخل اسم العملة للإزالة:")
        context.user_data['action'] = 'remove_coin'

async def main():
    app = Application.builder().token(MAIN_BOT_TOKEN).build()

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
    logger.info("CallbackQueryHandler for 'button_handler' added")
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, coin_handler))
    logger.info("MessageHandler for 'coin_handler' added")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_prices, "interval", minutes=15, args=[app])
    scheduler.add_job(news_job, "interval", minutes=30, args=[app])
    # scheduler.add_job(portfolio_job, "interval", days=1, args=[app])
    # scheduler.add_job(stoploss_job, "interval", minutes=10, args=[app])
    logger.info("Scheduler is starting...")
    scheduler.start()
    logger.info("Scheduler started successfully")

    logger.info("Bot is running...")
    await app.run_polling()
    logger.info("Bot stopped running")







if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
