from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# الحصول على التوكن من ملف .env
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set in .env file")

# دالة /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("هلا!  في بوت المساعد للكريبتو 🚀\nاستخدم الأوامر التالية:\n/news\n/alert\n/portfolio\n/trade ✅")


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE): #لعرض الأخبار الأخيرة
    await update.message.reply_text("هنا الأخبار الأخيرة!")

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE): #لعرض التنبيهات
    await update.message.reply_text("هنا يتم إعداد إشعارات!")

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE): #لعرض اخر احصائيات المحفظة
    await update.message.reply_text("هنا يتم عرض معاملاتك!")

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE): #لمحاكاة صفقة عملية
    await update.message.reply_text("هنا يتم معاملات العمل!")

# دالة /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "الأوامر المتاحة:\n"
        "/start - تشغيل البوت\n"
        "/help - عرض المساعدة\n"
        "/news - عرض الأخبار الأخيرة\n"
        "/alert - إعداد إشعارات\n"
        "/portfolio - عرض معاملاتك\n"
        "/trade - معاملات العمل"
    )

def main():
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()

    # إضافة الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("trade", trade))
    app.add_handler(CommandHandler("help", help_command))

    # تشغيل البوت
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
