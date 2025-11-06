import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify
from SubscriptionsBot.Payment_handler import PaymentHandler
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from telegram import Bot
from config import SUBS_BOT_TOKEN, CHANNEL_LINK, PAYMENTS_PALNS # دمج الاستيرادات
from setup_database import add_subscriber, update_payment_status, remove_pending_payment
from utils.logging import logger

app = Flask(__name__)
payment_handler = PaymentHandler()
bot = Bot(SUBS_BOT_TOKEN) # إنشاء كائن البوت الحقيقي

@app.route('/webhook/payment', methods=['POST'])
def handle_payment_webhook():
    """استقبال إشعارات الدفع من NOWPayments"""
    logger.info("Received payment webhook.")
    payload = request.json
    signature = request.headers.get('x-nowpayments-sig')
    logger.info(f"Webhook payload: {payload}, Signature: {signature}")
    
    # تحقق من الصحة
    if not payment_handler.verify_ipn(payload, signature):
        logger.warning("Invalid signature received for payment webhook.")
        return jsonify({'error': 'Invalid signature'}), 403
    logger.info("IPN signature verified successfully.")
    
    payment_status = payload.get('payment_status')
    order_id = payload.get('order_id')
    payment_id = payload.get('payment_id') # الحصول على payment_id من الـ payload
    
    if payment_status == 'finished':
        logger.info(f"Payment {payment_id} finished. Activating subscription for user {order_id}.")
        # استخراج user_id و plan_id و duration من order_id
        parts = order_id.split('_')
        plan_id = parts[0]
        user_id = int(parts[1])
        # duration = PAYMENTS_PALNS[plan_id]['duration'] # تم الحصول عليها من PAYMENTS_PALNS
        duration = int(parts[2].replace('m', '')) # الحصول على duration من order_id مباشرة

        # استدعاء الدالة المركزية لمعالجة الدفع الناجح مع duration
        process_successful_payment(payment_id, user_id, CHANNEL_LINK, duration, plan_id) # تمرير plan_id
        logger.info(f"Subscription activated and user notified for payment {payment_id}.")
        return jsonify({'status': 'success'}), 200

    elif payment_status == 'failed' or payment_status == 'cancelled':
        logger.warning(f"Payment {payment_id} for order {order_id} failed or cancelled. Status: {payment_status}")
        # في حالة فشل أو إلغاء الدفع، قم بتحديث الحالة وإزالة الدفعة المعلقة
        payment_id = payload.get('payment_id')
        order_id = payload.get('order_id')
        update_payment_status(payment_id, payment_status)
        remove_pending_payment(order_id)
        # يمكنك إضافة منطق لإرسال رسالة للمستخدم هنا إذا أردت
        user_id = int(order_id.split('_')[1])
        bot.send_message(
            user_id,
            f'❌ فشل أو إلغاء الدفع لطلبك رقم {order_id}. يرجى المحاولة مرة أخرى.'
        )
        logger.info(f"Payment {payment_id} status updated to {payment_status} and pending payment removed.")
    
    return jsonify({'status': 'ok'}), 200

def activate_subscription(user_id, duration_months):
    """تفعيل الاشتراك في قاعدة البيانات"""
    logger.info(f"Activating subscription for user {user_id} for {duration_months} months.")
    add_subscriber(user_id, None, duration_months)
    logger.info(f"Subscription activated for user {user_id}.")

# إضافة دالة قابلة لإعادة الاستخدام لتحديث حالة الدفع
def process_successful_payment(payment_id, user_id, channel_link, duration, plan_id):
    """تحديث حالة الدفع وإزالة الدفعة المعلقة وإشعار المستخدم"""
    logger.info(f"Processing successful payment for payment_id: {payment_id}, user_id: {user_id}, duration: {duration}, plan_id: {plan_id}")
    update_payment_status(payment_id, 'completed')
    logger.info(f"Payment status for {payment_id} updated to 'completed'.")
    remove_pending_payment(payment_id)
    logger.info(f"Pending payment {payment_id} removed.")
    add_subscriber(user_id, plan_id, duration) # إضافة المشترك هنا
    logger.info(f"Subscriber {user_id} added/updated with plan {plan_id} for {duration} months.")
    bot.send_message(user_id, f'✅🎉 تم تأكيد دفعك بنجاح! تم تفعيل اشتراكك لمدة {duration} شهر! رابط القناة :{channel_link}.')
    logger.info(f"Confirmation message sent to user {user_id}.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
