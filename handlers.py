from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ALLOWED_CHAT_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_id = update.effective_chat.id
    if user_chat_id != ALLOWED_CHAT_ID:
        await update.message.reply_text("عذراً، لا يمكنك استخدام هذا البوت.")
        return

    context.bot_data['chat_id'] = user_chat_id
    await update.message.reply_text(
        "هلا! في بوت المساعد للكريبتو 🚀\n"
        "الأوامر:/alerts\n/news\n/portfolio\n/trade\n/help"
    )

async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("إضافة عملة", callback_data='add_coin')],
        [InlineKeyboardButton("إزالة عملة", callback_data='remove_coin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('اختر الإجراء:', reply_markup=reply_markup)

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
        "/alerts - إدارة العملات التي تتبعها\n"
        "/news - عرض الأخبار الأخيرة\n"
        "/portfolio - عرض تقرير معاملاتك\n"
        "/trade -  عمل صفقة افتراضية"
    )


