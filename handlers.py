from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ALLOWED_CHAT_ID
from utils.logging import setup_logging # استيراد الـ logger
logger = setup_logging(log_file='handlers.log', name=__name__) # إعداد الـ logger

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_id = update.effective_user.id
    logger.info(f"User Chat ID: {user_chat_id}")
    logger.info(f"Allowed Chat ID (from config): {ALLOWED_CHAT_ID}")
    try:
        allowed_chat_id_int = int(ALLOWED_CHAT_ID)
        logger.info(f"Allowed Chat ID (as int): {allowed_chat_id_int}")
    except ValueError:
        logger.error(f"Error converting ALLOWED_CHAT_ID to int: {ALLOWED_CHAT_ID}") 
        await update.message.reply_text("حدث خطأ في إعدادات البوت. يرجى الاتصال بالمسؤول.")
        return

    if user_chat_id != allowed_chat_id_int:
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


