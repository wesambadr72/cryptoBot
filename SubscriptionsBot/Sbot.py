import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging import setup_logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from Payment_handler import PaymentHandler
from config import SUBS_BOT_TOKEN, PAYMENTS_PLANS,CHANNEL_LINK
from setup_database import add_subscriber, update_payment_status, get_subscriber, remove_pending_payment, add_payment, add_pending_payment, get_pending_payment, get_pending_payments_by_user_id
import asyncio
from utils.helpers import is_payment_expired, strip_html_tags_and_unescape_entities, MESSAGES, extract_network_from_currency
from SubscriptionsBot.webhookserver import process_successful_payment

payment_handler = PaymentHandler()


logger = setup_logging(log_file='sbot.log', name=__name__)
app = Application.builder().token(SUBS_BOT_TOKEN).build()
logger.info("Subscriptions bot started...")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"User {user_id} initiated /start command.")

    keyboard = [
        [InlineKeyboardButton(MESSAGES['ar']['arabic_button'], callback_data='lang_ar')],
        [InlineKeyboardButton(MESSAGES['en']['english_button'], callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=user_id, text=MESSAGES['ar']['choose_language'], reply_markup=reply_markup)

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    lang_code = query.data.split('_')[1] # 'lang_ar' -> 'ar'
    context.user_data['language'] = lang_code
    logger.info(f"User {user_id} selected language: {lang_code}")

    await query.edit_message_text(text=MESSAGES[lang_code]['language_set_to'])
    await welcoming_msg(update, context, lang_code)

async def welcoming_msg(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code: str = 'ar'):
    """رسالة الترحيب"""
    user_id = update.effective_user.id
    logger.info(f"Sending welcoming message to user {user_id} in {lang_code} language.")

    await context.bot.send_message(chat_id=user_id, text=MESSAGES[lang_code]['welcome'],parse_mode='HTML')
    logger.info(f"Welcoming message sent successfully to user {user_id}")

    # إنشاء لوحة مفاتيح مخصصة بالأوامر
    command_keyboard = [
        [KeyboardButton(f"/{MESSAGES[lang_code]['subscribe_command']}")],
        [KeyboardButton(f"/{MESSAGES[lang_code]['check_payment_command']}")],
        [KeyboardButton(f"/{MESSAGES[lang_code]['help_command']}")]
    ]
    reply_markup = ReplyKeyboardMarkup(command_keyboard, resize_keyboard=True, one_time_keyboard=False)

    # إرسال رسالة مع لوحة المفاتيح المخصصة
    await context.bot.send_message(chat_id=user_id, text=MESSAGES[lang_code]['commands_prompt'], reply_markup=reply_markup)

async def start_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض خطط الاشتراك"""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} requested subscription plans.")
    
    lang_code = context.user_data.get('language', 'ar') # Default to Arabic

    keyboard = [
        [InlineKeyboardButton(f"{MESSAGES[lang_code]['one_day_trial']} - ${PAYMENTS_PLANS['1_DAY_TRIAL']}", callback_data=f'plan_d1_{PAYMENTS_PLANS['1_DAY_TRIAL']}')],
        [InlineKeyboardButton(f"{MESSAGES[lang_code]['one_month_subscription']} -${PAYMENTS_PLANS['1_MONTH']}", callback_data=f'plan_m1_{PAYMENTS_PLANS['1_MONTH']}')],
        [InlineKeyboardButton(f"{MESSAGES[lang_code]['three_month_subscription']}-${PAYMENTS_PLANS['3_MONTHS']}({'💸 خصم %15' if lang_code == 'ar' else '💸 15% OFF'})", callback_data=f'plan_m3_{PAYMENTS_PLANS["3_MONTHS"]}')],
        [InlineKeyboardButton(f"{MESSAGES[lang_code]['six_month_subscription']} -${PAYMENTS_PLANS['6_MONTHS']} ({'💸خصم %36' if lang_code == 'ar' else '💸💸 36% OFF'})", callback_data=f'plan_m6_{PAYMENTS_PLANS["6_MONTHS"]}')]
    ]
    
    await update.message.reply_text(
        MESSAGES[lang_code]['subscribe_plans_prompt'],
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

    lang_code = context.user_data.get('language', 'ar') # Default to Arabic

    # التعامل مع التجربة المجانية
    _, duration, price_str = query.data.split('_')
    price = float(price_str)
    user_id = query.from_user.id

    logger.info(f"User {user_id} proceeding with paid plan. Duration: {duration}, Price: {price}")
    # التحقق مما إذا كان هناك دفع معلق بالفعل للمستخدم
    pending_payments = get_pending_payments_by_user_id(user_id)
    if pending_payments:
        for p_payment in pending_payments:
            # p_payment[7] هو created_at
            if not is_payment_expired(p_payment[7]):
                # إذا كان هناك دفع معلق نشط، أبلغ المستخدم
                await query.edit_message_text(
                    MESSAGES[lang_code]['already_have_pending_payment'].format(
                        payment_id=p_payment[6], # payment_id
                        invoice_url=p_payment[5] # payment_address (نستخدمه هنا كـ invoice_url مؤقتًا)
                    ),
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(MESSAGES[lang_code]['pay_now_button'], url=p_payment[5])]])
                )
                logger.info(f"User {user_id} already has an active pending payment {p_payment[6]}.")
                return
            else:
                # إذا انتهت صلاحية الدفع المعلق، قم بإزالته
                remove_pending_payment(p_payment[6]) # order_id
                logger.info(f"Expired pending payment {p_payment[6]} for user {user_id} removed.")

    # إذا لم يكن هناك دفع معلق نشط، استمر في إنشاء دفع جديد
    if price == 0.0:
        if not get_subscriber(user_id):
            logger.info(f"User {user_id} is activating free trial.")
            # حفظ بيانات المستخدم في قاعدة البيانات باستخدام add_subscriber
            add_subscriber(user_id, username, 1, duration_type='days', subscription_type='1_DAY_TRIAL', payment_method='Trial', payment_reference='N/A')
            await query.message.reply_text(MESSAGES[lang_code]['free_trial_activated'].format(channel_link=CHANNEL_LINK))
            logger.info(f"Free trial activated for user {user_id}.")
            return
        else:
            logger.warning(f"User {user_id} already has an active subscription or trial.")
            await query.message.reply_text(MESSAGES[lang_code]['already_subscribed'])
            return

    payment = payment_handler.create_subscription_payment(
        user_id,
        float(price),
        int(duration[1:])
    )
    
    logger.info(f"Payment request created for user {user_id}. Payment ID: {payment.get('payment_id')} , payment object: {payment}")
    
    # احفظ في قاعدة البيانات
    add_payment(
        payment['payment_id'],
        user_id,
        payment['order_id'],
        payment['price_amount'],
        payment['pay_currency'],
        'pending'
            )
    logger.info(f"Payment details added to database for user {user_id}, order_id: {payment.get('order_id')}")

    # احفظ الدفعة المعلقة في قاعدة البيانات
    add_pending_payment(
        user_id,
        payment['order_id'],
        payment['price_amount'],
        payment['pay_currency'],
        'pending',
        payment['pay_address'],
        payment['payment_id']
    )
    logger.info(f"Pending payment added to database for user {user_id}, order_id: {payment.get('order_id')}")

    # احفظ order_id في context.user_data للتحقق لاحقًا
    context.user_data['last_order_id'] = payment['order_id']
    
    # أرسل تعليمات الدفع مع زر الدفع
    network = extract_network_from_currency(payment.get('pay_currency'))
    message = strip_html_tags_and_unescape_entities(
        MESSAGES[lang_code]['payment_details_prompt'].format(network=network)
    )
    
    keyboard = []
    if payment.get('invoice_url'):
        keyboard.append([InlineKeyboardButton(MESSAGES[lang_code]['pay_now_button'], url=payment.get('invoice_url'))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, parse_mode='HTML', reply_markup=reply_markup)
    logger.info(f"Payment instructions sent to user {user_id} for order_id: {payment.get('order_id')}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang_code = context.user_data.get('language', 'ar') # Default to Arabic
    help_text = MESSAGES[lang_code]['help_message']
    await update.message.reply_text(help_text, parse_mode='HTML')


async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    order_id = context.user_data.get('last_order_id')
    logger.info(f"User {user_id} checking payment status for order_id: {order_id}")

    lang_code = context.user_data.get('language', 'ar') # Default to Arabic

    if not order_id:
        logger.info(f"No pending payment found for user {user_id}.")
        await update.message.reply_text(MESSAGES[lang_code]['no_pending_payment'])
        return

    pending_payment = get_pending_payment(order_id)

    if not pending_payment:
        logger.warning(f"Pending payment details not found for order_id: {order_id} (user: {user_id}).")
        await update.message.reply_text(MESSAGES[lang_code]['payment_details_not_found'])
        return

    # pending_payment[7] هو created_at
    if is_payment_expired(pending_payment[7]):

        logger.info(f"Payment {order_id} for user {user_id} has expired.")

        update_payment_status(pending_payment[6], "expired") # pending_payment[6] هو payment_id
        remove_pending_payment(order_id)

        await update.message.reply_text(MESSAGES[lang_code]['payment_expired'])
        remove_pending_payment(order_id)

        logger.info(f"Expired payment {order_id} removed for user {user_id}.")
        return

    # إذا لم تنتهِ الصلاحية، تحقق من NOWPayments
    payment_id_to_check = int(pending_payment[6]) # pending_payment[6] هو payment_id
    logger.info(f"Attempting to get NOWPayments status for payment_id: {payment_id_to_check} (order_id: {order_id})")
    payment_status_nowpayments = payment_handler.get_payment_status(payment_id_to_check) # pending_payment[6] هو payment_id
    logger.info(f"NOWPayments status for payment {pending_payment[6]} (order: {order_id}): {payment_status_nowpayments.get('payment_status')}")

    if payment_status_nowpayments and payment_status_nowpayments['payment_status'] == 'finished':
        logger.info(f"Payment {order_id} for user {user_id} finished successfully.")
        # تم الدفع بنجاح
        # المنطق الفعلي لتفعيل الاشتراك سيتم التعامل معه بواسطة الـ webhook
        # هنا فقط نبلغ المستخدم وننظف قاعدة البيانات

        # استخراج plan_id و duration من order_id
        parts = order_id.split('_')
        user_id = int(parts[1]) # التأكد من استخدام user_id الصحيح
        plan_id = parts[2] # plan_id هو الجزء الأول من order_id
        duration = int(parts[3]) # duration هو الجزء الثالث من order_id

        # استدعاء الدالة المركزية لمعالجة الدفع الناجح
        process_successful_payment(pending_payment[6], user_id, CHANNEL_LINK, duration, plan_id)
        await update.message.reply_text(MESSAGES[lang_code]['payment_successful'])
        del context.user_data['last_order_id']

        logger.info(f"Successful payment {order_id} processed for user {user_id}.")

    elif payment_status_nowpayments and (payment_status_nowpayments['payment_status'] == 'failed' or payment_status_nowpayments['payment_status'] == 'cancelled'):
       
        logger.warning(f"Payment {order_id} for user {user_id} failed or cancelled. Status: {payment_status_nowpayments.get('payment_status')}")
        # فشل أو إلغاء الدفع

        update_payment_status(pending_payment[6], payment_status_nowpayments['payment_status'])
        remove_pending_payment(order_id)
        await update.message.reply_text(MESSAGES[lang_code]['payment_failed_cancelled'])
        del context.user_data['last_order_id']

        logger.info(f"Failed/cancelled payment {order_id} removed for user {user_id}.")
    else:

        logger.info(f"Payment {order_id} for user {user_id} is still pending or in unknown state. Status: {payment_status_nowpayments.get('payment_status')}")
        # لا يزال معلقًا أو حالة غير معروفة
        await update.message.reply_text(MESSAGES[lang_code]['payment_pending'])

# سجّل الـ handlers
app.add_handler(CommandHandler('start', start_command))
app.add_handler(CallbackQueryHandler(handle_language_selection, pattern='^lang_'))
app.add_handler(CommandHandler('subscribe', start_subscription))
app.add_handler(CallbackQueryHandler(handle_plan_selection, pattern='^plan_'))
app.add_handler(CommandHandler('check_payment', check_payment))
app.add_handler(CommandHandler('help', help_command))


if __name__ == "__main__":
    app.run_polling()
