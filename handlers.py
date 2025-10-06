from telegram import Update
from telegram.ext import ContextTypes

CHAT_ID = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CHAT_ID
    CHAT_ID = update.effective_chat.id
    await update.message.reply_text(
        "هلا! في بوت المساعد للكريبتو 🚀\n"
        "الأوامر:\n/news\n/portfolio\n/trade\n/help"
    )

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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("إضافة عملة", callback_data='add_coin')],
        [InlineKeyboardButton("إزالة عملة", callback_data='remove_coin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('اختر الإجراء:', reply_markup=reply_markup)
