import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify, Blueprint
from SubscriptionsBot.Payment_handler import PaymentHandler
import json
from telegram import Bot
from config import SUBS_BOT_TOKEN, CHANNEL_LINK, PAYMENTS_PALNS, CHANNEL_ID # دمج الاستيرادات
from setup_database import add_subscriber, update_payment_status, remove_pending_payment
from utils.logging import logger

app = Flask(__name__)
payment_handler = PaymentHandler()
bot = Bot(SUBS_BOT_TOKEN) # إنشاء كائن البوت الحقيقي

webhook_bp = Blueprint('webhook', __name__)

@app.route('/webhook/payment', methods=['POST'])
async def handle_payment_webhook():
    """استقبال إشعارات الدفع من NOWPayments"""
    logger.info("Received payment webhook.")
    try:
        payload = request.json
        signature = request.headers.get('x-nowpayments-sig')
    
        if not payload:
            logger.warning("Received empty payload for payment webhook.")
            return jsonify({'error': 'Empty payload'}), 400

        logger.info(f"Received IPN: {json.dumps(payload)}")
    
        if not payment_handler.verify_ipn(payload, signature):
            logger.warning("Invalid signature received for payment webhook.")
            return jsonify({'error': 'Invalid signature'}), 403
        logger.info("IPN signature verified successfully.")

        payment_status = payload.get('payment_status')
        order_id = payload.get('order_id')
        pay_amount = float(payload.get('pay_amount'))
        pay_currency = payload.get('pay_currency')
        payment_id = payload.get('payment_id')

        if not all([payment_status, order_id, pay_amount, pay_currency, payment_id]):
            logger.error(f"Missing essential IPN data: {payload}")
            return jsonify({'error': 'Missing essential IPN data'}), 400

        # تحليل order_id
        # تنسيق order_id المتوقع: sub_{user_id}_{plan_type}_{duration}_{random_string}_{timestamp}
        parts = order_id.split('_')
        if len(parts) < 6 or parts[0] != 'sub':
            logger.error(f"Invalid order_id format: {order_id}")
            return jsonify({'error': 'Invalid order_id format'}), 400

        user_id = int(parts[1])
        plan_type = parts[2] # على سبيل المثال "subscription"
        duration_value = int(parts[3]) # على سبيل المثال "1"
        
        # بناء اسم الخطة من plan_type و duration_value
        plan_name = None
        if plan_type == "subscription":
            match duration_value:
                case 1:
                    plan_name = "1_MONTH"
                case 3:
                    plan_name = "3_MONTHS"
                case 6:
                    plan_name = "6_MONTHS"
                case _:
                    logger.error(f"Unsupported duration value '{duration_value}' for plan_type '{plan_type}' in order_id: {order_id}")
                    return jsonify({'error': 'Unsupported plan duration'}), 400

        if plan_name not in PAYMENTS_PALNS:
            logger.error(f"Constructed plan_name '{plan_name}' not found in PAYMENTS_PALNS for order_id: {order_id}")
            return jsonify({'error': 'Invalid plan_name'}), 400

        logger.info(f"Processing payment for user_id: {user_id}, plan_name: {plan_name}, status: {payment_status}")

        if payment_status == 'finished':
            logger.info(f"Payment {payment_id} finished. Activating subscription for user {order_id}.")
            # استدعاء الدالة المركزية لمعالجة الدفع الناجح مع duration
            process_successful_payment(payment_id, user_id, CHANNEL_LINK, duration_value, plan_name) # تمرير plan_name و duration_value
            logger.info(f"Subscription activated and user notified for payment {payment_id}.")
            return jsonify({'status': 'success'}), 200

        elif payment_status == 'failed' or payment_status == 'cancelled':
            logger.warning(f"Payment {payment_id} for order {order_id} failed or cancelled. Status: {payment_status}")
            await bot.send_message(user_id, MESSAGES['ar']['payment_failed'].format(payment_id=payment_id))
            update_payment_status(payment_id, payment_status)
            remove_pending_payment(order_id)
            # يمكنك إضافة منطق لإرسال رسالة للمستخدم هنا إذا أردت
            user_id = int(parts[1])
            bot.send_message(
                user_id,
                f'❌ فشل أو إلغاء الدفع لطلبك رقم {order_id}. يرجى المحاولة مرة أخرى.'
            )
            logger.info(f"Payment {payment_id} status updated to {payment_status} and pending payment removed.")
    
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        logger.error(f"Error processing payment webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def activate_subscription(user_id, duration_months):
    """تفعيل الاشتراك في قاعدة البيانات"""
    logger.info(f"Activating subscription for user {user_id} for {duration_months} months.")
    add_subscriber(user_id, None, duration_months)
    logger.info(f"Subscription activated for user {user_id}.")

# إضافة دالة قابلة لإعادة الاستخدام لتحديث حالة الدفع
async def process_successful_payment(payment_id, user_id, channel_link, duration, plan_id):
    """تحديث حالة الدفع وإزالة الدفعة المعلقة وإشعار المستخدم"""

    logger.info(f"Processing successful payment for payment_id: {payment_id}, user_id: {user_id}, duration: {duration}, plan_id: {plan_id}")
    
    # إلغاء حظر المستخدم من القناة للسماح له بالانضمام مرة أخرى
    try:
        # bot_instance = Bot(token=SUBS_BOT_TOKEN) # لا حاجة لإنشاء كائن Bot جديد، bot متاح بالفعل
        await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        logger.info(f"User {user_id} unbanned from channel {CHANNEL_ID}.")
    except Exception as e:
        logger.error(f"Error unbanning user {user_id} from channel {CHANNEL_ID}: {e}")

    update_payment_status(payment_id, 'completed')
    logger.info(f"Payment status for {payment_id} updated to 'completed'.")

    remove_pending_payment(payment_id)
    logger.info(f"Pending payment {payment_id} removed.")

    add_subscriber(user_id, None, duration, subscription_type=plan_id) # إضافة المشترك هنا، وتمرير None لـ username
    logger.info(f"Subscriber {user_id} added/updated with plan {plan_id} for {duration} months.")

    await bot.send_message(user_id, f'✅🎉 تم تأكيد دفعك بنجاح! تم تفعيل اشتراكك لمدة {duration} شهر! رابط القناة :{channel_link}.')
    logger.info(f"Confirmation message sent to user {user_id}.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
