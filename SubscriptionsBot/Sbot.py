import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging import logger
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from Payment_handler import PaymentHandler
from config import SUBS_BOT_TOKEN, PAYMENTS_PALNS,CHANNEL_LINK
from setup_database import add_subscriber, update_payment_status, get_subscriber, remove_pending_payment, add_payment, add_pending_payment, get_pending_payment
from datetime import datetime, timedelta
import asyncio
from utils import logging as utils_logging # Import logging from utils
from utils.helpers import is_payment_expired, strip_html_tags_and_unescape_entities
from SubscriptionsBot.webhookserver import process_successful_payment

payment_handler = PaymentHandler()

app = Application.builder().token(SUBS_BOT_TOKEN).build()
logger.info("Subscriptions bot started...")


async def welcoming_msg(update: Update,context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب"""
    user_id = update.effective_user.id
    logger.info(f"Sending welcoming message to user {user_id}")
    await context.bot.send_message(chat_id=user_id, text="""
        🎉  أهلاً وسهلاً بك في بوت اشتراكات قناة OWL CAB🦉!

    😍يسعدنا انضمامك إلى مجموعة مستخدمي القناة الذكية المختصة بسوق الكريبتو لمساعدتك في متابعة سوق الكريبتو بسهولة ويُسر.
    يمكنك الحصول الان على تجربتك المجانية الأولى والتي تتيح لك:

    تجربة جميع الميزات الحصرية لـمدة محدودة بدون أي التزام!

    متابعة اخر اخبار سوق العملات الرقمية من اكثر من مصدر موثوق📰.

    تحليل للاخبار بالذكاء الاصطناعي AI 🤖

    📊تلقي تنبيهات وتحليلات متقدمة للعملات والأسعار، واكتشاف فرص التداول اللحظية.

    روابط مباشرة للعملات عبر البرنامج الشهير TradingView🔗.

    ملاحظات هامة⚠️:

    تستطيع الاستفادة من جميع الخدمات خلال فترة التجربة المجانية. عند انتهائها، سيطلب منك الاشتراك لمواصلة استخدام الميزات المتقدمة.

    لكل مستخدم تجربة مجانية واحدة فقط، بعدها يمكنك اختيار الباقة المناسبة لك.

    (البوت يعرض معلومات فقط ولا يقدم نصائح استثمارية أو يضمن تحقيق أرباح أو تجنب خسائر. جميع قرارات التداول والاستثمار تقع على عاتق المستخدم وحده).

    إذا واجهتك أي مشكلة أو استفسار، تواصل معنا عبر الحساب @Ws7h9.

    🚀 ابدأ تجربتك الآن واستكشف مميزات البوت بالكامل قبل انتهاء الفترة المجانية!

    نتمنى لك رحلة تداول ناجحة وخبرة تحليل متميزة معنا 🌟
    – فريق OWL CAB 🦉
    """
    )
    logger.info(f"Welcoming message sent successfully to user {user_id}")

    # إنشاء لوحة مفاتيح مخصصة بالأوامر
    command_keyboard = [
        [KeyboardButton("/subscribe")],
        [KeyboardButton("/check_payment")],
        [KeyboardButton("/help")]
    ]
    reply_markup = ReplyKeyboardMarkup(command_keyboard, resize_keyboard=True, one_time_keyboard=False)

    # إرسال رسالة مع لوحة المفاتيح المخصصة
    await context.bot.send_message(chat_id=user_id, text="يمكنك استخدام الأوامر التالية:", reply_markup=reply_markup)

async def start_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض خطط الاشتراك"""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested subscription plans.")
    keyboard = [
        [InlineKeyboardButton(f"1 يوم تجريبي مجاناَ - ${PAYMENTS_PALNS['1_DAY_TRIAL']}", callback_data=f'plan_d1_{PAYMENTS_PALNS['1_DAY_TRIAL']}')],
        [InlineKeyboardButton(f"1 شهر - ${PAYMENTS_PALNS['1_MONTH']}", callback_data=f'plan_m1_{PAYMENTS_PALNS['1_MONTH']}')],
        [InlineKeyboardButton(f"3 أشهر - ${PAYMENTS_PALNS['3_MONTHS']} (💸 خصم %15)", callback_data=f'plan_m3_{PAYMENTS_PALNS['3_MONTHS']}')],
        [InlineKeyboardButton(f"6 أشهر - ${PAYMENTS_PALNS['6_MONTHS']} (💸💸 خصم %36)", callback_data=f'plan_m6_{PAYMENTS_PALNS['6_MONTHS']}')]
    ]
    
    await update.message.reply_text(
        '📦 اختر خطة الاشتراك:',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"Subscription plans displayed to user {user_id}.")

async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع اختيار خطة الاشتراك"""
    query = update.callback_query
    await query.answer()

    # استخراج بيانات المستخدم
    user_id = query.from_user.id
    username = query.from_user.username if query.from_user.username else str(user_id)
    callback_data = query.data
    logger.info(f"User {user_id} selected plan: {callback_data}")

    # التعامل مع التجربة المجانية
    _, duration, price_str = query.data.split('_')
    price = float(price_str)
    user_id = query.from_user.id

    logger.info(f"User {user_id} proceeding with paid plan. Duration: {duration}, Price: {price}")
    # أنشئ الدفعة
    if price == 0.0:
        if not get_subscriber(user_id):
            logger.info(f"User {user_id} is activating free trial.")
            # حفظ بيانات المستخدم في قاعدة البيانات باستخدام add_subscriber
            add_subscriber(user_id, username, 1, duration_type='days', subscription_type='trial', payment_method='Trial', payment_reference='N/A')
            await query.message.reply_text(f"🎉 لقد تم تفعيل التجربة المجانية الخاصة بك!\nرابط القناة: {CHANNEL_LINK}")
            logger.info(f"Free trial activated for user {user_id}.")
            return
        else:
            logger.warning(f"User {user_id} already has an active subscription or trial.")
            await query.message.reply_text("⚠️ أنت لديك اشتراك فعال بالفعل!")
            return

    payment = payment_handler.create_subscription_payment(
        user_id,
        float(price),
        int(duration[1:])
    )
    logger.info(f"Payment request created for user {user_id}. Payment ID: {payment.get('payment_id')}")
    
    # احفظ في قاعدة البيانات
    add_payment(
        payment['payment_id'],
        user_id,
        payment['order_id'],
        payment['pay_amount'],
        payment['pay_currency'],
        'pending'
            )
    logger.info(f"Payment details added to database for user {user_id}, order_id: {payment.get('order_id')}")

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
    logger.info(f"Pending payment added to database for user {user_id}, order_id: {payment.get('order_id')}")

    # احفظ order_id في context.user_data للتحقق لاحقًا
    context.user_data['last_order_id'] = payment['order_id']
    
    # أرسل تعليمات الدفع مع زر الدفع
    message = strip_html_tags_and_unescape_entities(
        f"💰 <b>تفاصيل الدفع:</b>\n\n"
        f"⚠️  أرسل المبلغ ((بالضبط)) -وإلا قد تحدث مشاكل في عملية الدفع- إلى العنوان الموجود في الرابط أدناه\n"
        f"✅ سيتم تفعيل اشتراكك تلقائياً بعد التأكيد (1-10 دقائق)\n\n"
        f"🔍للتحقق من حالة الدفع: /check_payment"
    )
    
    keyboard = []
    if payment.get('invoice_url'):
        keyboard.append([InlineKeyboardButton("💳 ادفع الآن", url=payment.get('invoice_url'))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)
    logger.info(f"Payment instructions sent to user {user_id} for order_id: {payment.get('order_id')}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested help.")
    help_message = (
        "أهلاً بك في بوت OWL CAB Subscriptions! إليك الأوامر التي يمكنك استخدامها:\n\n"
        "/start - لبدء التفاعل مع البوت.\n"
        "/subscribe - لاشتراك في خدمة OWL CAB.\n"
        "/check_payment - للتحقق من حالة دفعك الأخير.\n"
        "/help - لعرض هذه الرسالة المساعدة.\n"
    )
    await update.message.reply_text(help_message)
    logger.info(f"Help message sent to user {user_id}.")


async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    order_id = context.user_data.get('last_order_id')
    logger.info(f"User {user_id} checking payment status for order_id: {order_id}")

    if not order_id:
        logger.info(f"No pending payment found for user {user_id}.")
        await update.message.reply_text("لا توجد عملية دفع معلقة للتحقق منها.")
        return

    pending_payment = get_pending_payment(order_id)

    if not pending_payment:
        logger.warning(f"Pending payment details not found for order_id: {order_id} (user: {user_id}).")
        await update.message.reply_text("لم يتم العثور على تفاصيل الدفع المعلقة.")
        return

    # pending_payment[7] هو created_at
    if is_payment_expired(pending_payment[7]):

        logger.info(f"Payment {order_id} for user {user_id} has expired.")

        update_payment_status(pending_payment[6], "expired") # pending_payment[6] هو payment_id
        remove_pending_payment(order_id)

        await update.message.reply_text("⏳ انتهت صلاحية عملية الدفع هذه (أكثر من 20 دقيقة).\nيرجى اختيار الاشتراك من جديد.")
        remove_pending_payment(order_id)

        logger.info(f"Expired payment {order_id} removed for user {user_id}.")
        return

    # إذا لم تنتهِ الصلاحية، تحقق من NOWPayments
    payment_status_nowpayments = payment_handler.get_payment_status(pending_payment[6]) # pending_payment[6] هو payment_id
    logger.info(f"NOWPayments status for payment {pending_payment[6]} (order: {order_id}): {payment_status_nowpayments.get('payment_status')}")

    if payment_status_nowpayments and payment_status_nowpayments['payment_status'] == 'finished':
        logger.info(f"Payment {order_id} for user {user_id} finished successfully.")
        # تم الدفع بنجاح
        # المنطق الفعلي لتفعيل الاشتراك سيتم التعامل معه بواسطة الـ webhook
        # هنا فقط نبلغ المستخدم وننظف قاعدة البيانات

        # استخراج plan_id و duration من order_id
        parts = order_id.split('_')
        plan_id = parts[0]
        user_id = int(parts[1]) # التأكد من استخدام user_id الصحيح
        duration = int(parts[2].replace('m', ''))

        # استدعاء الدالة المركزية لمعالجة الدفع الناجح
        process_successful_payment(pending_payment[6], user_id, CHANNEL_LINK, duration, plan_id)
        del context.user_data['last_order_id']

        logger.info(f"Successful payment {order_id} processed for user {user_id}.")

    elif payment_status_nowpayments and (payment_status_nowpayments['payment_status'] == 'failed' or payment_status_nowpayments['payment_status'] == 'cancelled'):
       
        logger.warning(f"Payment {order_id} for user {user_id} failed or cancelled. Status: {payment_status_nowpayments.get('payment_status')}")
        # فشل أو إلغاء الدفع

        update_payment_status(pending_payment[6], payment_status_nowpayments['payment_status'])
        remove_pending_payment(order_id)
        await update.message.reply_text("❌ فشل أو إلغاء الدفع. يرجى المحاولة مرة أخرى.")
        del context.user_data['last_order_id']

        logger.info(f"Failed/cancelled payment {order_id} removed for user {user_id}.")
    else:

        logger.info(f"Payment {order_id} for user {user_id} is still pending or in unknown state. Status: {payment_status_nowpayments.get('payment_status')}")
        # لا يزال معلقًا أو حالة غير معروفة
        await update.message.reply_text("⏳ لا تزال عملية الدفع معلقة. يرجى الانتظار قليلاً والمحاولة مرة أخرى.")

# سجّل الـ handlers
app.add_handler(CommandHandler('start', welcoming_msg))
app.add_handler(CommandHandler('subscribe', start_subscription))
app.add_handler(CallbackQueryHandler(handle_plan_selection, pattern='^plan_'))
app.add_handler(CommandHandler('check_payment', check_payment))
app.add_handler(CommandHandler('help', help_command))



if __name__ == "__main__":
    app.run_polling()
