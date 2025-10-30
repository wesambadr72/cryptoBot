import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from Payment_handler import PaymentHandler
from config import SUBS_BOT_TOKEN
from setup_database import add_subscriber, update_payment_status, get_subscriber, remove_pending_payment, add_payment, add_pending_payment, get_pending_payment
from datetime import datetime, timedelta
import asyncio
from utils import logging as utils_logging # Import logging from utils
from utils.helpers import is_payment_expired


# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

payment_handler = PaymentHandler()

app = Application.builder().token(SUBS_BOT_TOKEN).build()
logging.info("Subscriptions bot started...")

async def start_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض خطط الاشتراك"""
    keyboard = [
        [InlineKeyboardButton("1 تجريبي مجاناَ- $0.00", callback_data='plan_d1_0.00')],
        [InlineKeyboardButton("1 شهر - $13.99", callback_data='plan_m1_13.99')],
        [InlineKeyboardButton("3 أشهر - $26.99", callback_data='plan_m3_26.99')],
        [InlineKeyboardButton("6 أشهر - $47.99", callback_data='plan_m6_47.99')]
    ]
    
    await update.message.reply_text(
        '📦 اختر خطة الاشتراك:',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار الخطة"""
    query = update.callback_query
    await query.answer()
    
    # استخرج البيانات
    _, duration, price = query.data.split('_')
    user_id = query.from_user.id
    
    # أنشئ الدفعة
    payment = payment_handler.create_subscription_payment(
        user_id, 
        float(price), 
        int(duration)
    )
    
    # احفظ في قاعدة البيانات
    add_payment(
        payment['payment_id'],
        user_id,
        payment['order_id'],
        payment['pay_amount'],
        payment['pay_currency'],
        'pending',
        payment['pay_network']
    )

    # احفظ الدفعة المعلقة في قاعدة البيانات
    add_pending_payment(
        user_id,
        payment['order_id'],
        payment['pay_amount'],
        payment['pay_currency'],
        'pending',
        payment['pay_address'],
        payment['payment_id']
    )

    # احفظ order_id في context.user_data للتحقق لاحقًا
    context.user_data['last_order_id'] = payment['order_id']
    
    # أرسل تعليمات الدفع
    message = f"""
💰 تفاصيل الدفع:

**المبلغ**: {payment['pay_amount']} USDT
**العنوان**: `{payment['pay_address']}`

⚠️  أرسل المبلغ بالضبط إلى العنوان أعلاه على شبكة : {payment['pay_network']}
✅ سيتم تفعيل اشتراكك تلقائياً بعد التأكيد (1-10 دقائق)

🔍 حالة الدفع: /check_payment
    """
    
    await query.edit_message_text(message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_message = (
        "أهلاً بك في بوت الاشتراك! إليك الأوامر التي يمكنك استخدامها:\n\n"
        "/start - لبدء التفاعل مع البوت والحصول على معلومات حول الاشتراك.\n"
        "/check_payment - للتحقق من حالة دفعك الأخير.\n"
        "/help - لعرض هذه الرسالة المساعدة.\n"
    )
    await update.message.reply_text(help_message)


async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    order_id = context.user_data.get('last_order_id')

    if not order_id:
        await update.message.reply_text("لا توجد عملية دفع معلقة للتحقق منها.")
        return

    pending_payment = get_pending_payment(order_id)

    if not pending_payment:
        await update.message.reply_text("لم يتم العثور على تفاصيل الدفع المعلقة.")
        return

    # pending_payment[7] هو created_at
    if is_payment_expired(pending_payment[7]):
        update_payment_status(pending_payment[6], "expired") # pending_payment[6] هو payment_id
        remove_pending_payment(order_id)
        await update.message.reply_text("⏳ انتهت صلاحية عملية الدفع هذه (أكثر من 20 دقيقة).\nيرجى اختيار الاشتراك من جديد.")
        remove_pending_payment(order_id)
        return

    # إذا لم تنتهِ الصلاحية، تحقق من NOWPayments
    payment_status_nowpayments = payment_handler.get_payment_status(pending_payment[6]) # pending_payment[6] هو payment_id

    if payment_status_nowpayments and payment_status_nowpayments['payment_status'] == 'finished':
        # تم الدفع بنجاح
        # المنطق الفعلي لتفعيل الاشتراك سيتم التعامل معه بواسطة الـ webhook
        # هنا فقط نبلغ المستخدم وننظف قاعدة البيانات
        update_payment_status(pending_payment[6], "completed")
        remove_pending_payment(order_id)
        await update.message.reply_text("✅ تم تأكيد دفعك بنجاح! سيتم تفعيل اشتراكك قريباً.")
        del context.user_data['last_order_id']
    elif payment_status_nowpayments and (payment_status_nowpayments['payment_status'] == 'failed' or payment_status_nowpayments['payment_status'] == 'cancelled'):
        # فشل أو إلغاء الدفع
        update_payment_status(pending_payment[6], payment_status_nowpayments['payment_status'])
        remove_pending_payment(order_id)
        await update.message.reply_text("❌ فشل أو إلغاء الدفع. يرجى المحاولة مرة أخرى.")
        del context.user_data['last_order_id']
    else:
        # لا يزال معلقًا أو حالة غير معروفة
        await update.message.reply_text("⏳ لا تزال عملية الدفع معلقة. يرجى الانتظار قليلاً والمحاولة مرة أخرى.")

# سجّل الـ handlers
app.add_handler(CommandHandler('start', start_subscription))
app.add_handler(CallbackQueryHandler(handle_plan_selection, pattern='^plan_'))
app.add_handler(CommandHandler('check_payment', check_payment))
app.add_handler(CommandHandler('help', help_command))



if __name__ == "__main__":
    app.run_polling()
