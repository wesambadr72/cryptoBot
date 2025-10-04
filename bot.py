from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from binance.client import Client
import sqlite3
from datetime import datetime, timedelta
import asyncio
import logging
import nest_asyncio

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تحميل المتغيرات من ملف .env
load_dotenv()

# الحصول على التوكن من ملف .env
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in .env file")

# قائمة العملات المراد مراقبتها
COINS_TO_WATCH = ['ZBCNUSDT', 'HUSDT', 'OGUSDT', 'ELXUSDT', 'ICEUSDT', 'API3USDT', 'ZENUSDT', 'LIONUSDT', 'IDEXUSDT', 'HUMAUSDT','DOLOUSDT', 'ENATUSDT', 'AUSDT', 'AVEOUSDT', 'LQTYUSDT', 'PUNDIXUSDT', 'ARBUSDT', 'PENDLEUSDT', 'RAYUSDT', 'WLDUSDT', 'LISTAUSDT', 'TNSRUSDT', 'GALAUSDT', 'XLMUSDT', 'LAUSDT', 'ETHFIUSDT', 'EIGENUSDT', 'TWTUSDT', 'JTOUSDT', 'AWEUSDT', 'NEARUSDT','FILUSDT', 'LDOUSDT', 'IMXUSDT', 'STXUSDT', 'FETUSDT', 'SCRTUSDT', 'CFXUSDT', 'GRTUSDT', 'DUSKUSDT','NKNUSDT', 'CELRUSDT','DEXEUSDT','APTUSDT','NEOUSDT','SKYUSDT']

# إعداد عميل Binance
binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# متغير عام لتخزين آخر تحديث للأسعار
CHAT_ID = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    await update.message.reply_text("هلا! في بوت المساعد للكريبتو 🚀\nاستخدم الأوامر التالية:\n/news\n/portfolio\n/trade ✅")

async def check_prices(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID:
        logging.warning("No chat ID available")
        return

    conn = sqlite3.connect('crypto_prices.db')
    cursor = conn.cursor()
    
    try:
        # الحصول على أسعار جميع العملات من Binance
        prices = binance_client.get_all_tickers()
        current_time = datetime.now()
        
        for coin in COINS_TO_WATCH:
            try:
                # البحث عن السعر الحالي للعملة
                current_price = float(next(p['price'] for p in prices if p['symbol'] == coin))
                
                # حفظ السعر الحالي في قاعدة البيانات
                cursor.execute('''
                INSERT INTO price_history (symbol, price, timestamp)
                VALUES (?, ?, ?)
                ''', (coin, current_price, current_time))
                
                # الحصول على السعر قبل 15 دقيقة
                cursor.execute('''
                SELECT price
                FROM price_history
                WHERE symbol = ? AND timestamp <= datetime('now', '-15 minutes')
                ORDER BY timestamp DESC
                LIMIT 1
                ''', (coin,))
                
                result = cursor.fetchone()
                if result:
                    old_price = float(result[0])
                    price_change = ((current_price - old_price) / old_price) * 100
                    
                    # إذا كان التغير أكبر من 1.3%
                    if price_change >= 1.3:
                        # التحقق من عدم إرسال تنبيه مكرر
                        cursor.execute('''
                        SELECT timestamp
                        FROM sent_alerts
                        WHERE symbol = ? AND timestamp >= datetime('now', '-15 minutes')
                        ''', (coin,))
                        
                        if not cursor.fetchone():
                            message = f"🚨 تنبيه! {coin}\n"
                            message += f"السعر السابق: {old_price:.8f}\n"
                            message += f"السعر الحالي: {current_price:.8f}\n"
                            message += f"نسبة التغير: {price_change:.2f}%"
                            
                            await context.bot.send_message(chat_id=CHAT_ID, text=message)
                            
                            # تسجيل التنبيه
                            cursor.execute('''
                            INSERT INTO sent_alerts (symbol, price_before, price_after, percentage_change)
                            VALUES (?, ?, ?, ?)
                            ''', (coin, old_price, current_price, price_change))
            
            except Exception as e:
                logging.error(f"Error processing {coin}: {str(e)}")
                continue
        
        conn.commit()
    
    except Exception as e:
        logging.error(f"Error in check_prices: {str(e)}")
    finally:
        conn.close()

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هنا الأخبار الأخيرة!")

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هنا يتم عرض معاملاتك!")

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هنا يتم معاملات العمل!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "الأوامر المتاحة:\n"
        "/start - تشغيل البوت\n"
        "/help - عرض المساعدة\n"
        "/news - عرض الأخبار الأخيرة\n"
        "/portfolio - عرض معاملاتك\n"
        "/trade - معاملات العمل"
    )

async def main():
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()

    # إضافة الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("trade", trade))
    app.add_handler(CommandHandler("help", help_command))

    # إعداد المجدول
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_prices, 'interval', minutes=15, args=[app])
    scheduler.start()

    # تشغيل البوت
    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
