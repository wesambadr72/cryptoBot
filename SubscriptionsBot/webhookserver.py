import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify
from SubscriptionsBot.Payment_handler import PaymentHandler
import hmac
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from telegram import Bot
from config import SUBS_BOT_TOKEN
from setup_database import add_subscriber, update_payment_status, remove_pending_payment

app = Flask(__name__)
payment_handler = PaymentHandler()
bot = Bot(SUBS_BOT_TOKEN) # إنشاء كائن البوت الحقيقي

@app.route('/webhook/payment', methods=['POST'])
def handle_payment_webhook():
    """استقبال إشعارات الدفع من NOWPayments"""
    
    payload = request.json
    signature = request.headers.get('x-nowpayments-sig')
    
    # تحقق من الصحة
    if not payment_handler.verify_ipn(payload, signature):
        return jsonify({'error': 'Invalid signature'}), 403
    
    payment_status = payload.get('payment_status')
    order_id = payload.get('order_id')
    payment_id = payload.get('payment_id') # الحصول على payment_id من الـ payload
    
    if payment_status == 'finished':
        # استخرج user_id من order_id
        user_id = int(order_id.split('_')[1])
        duration = int(order_id.split('_')[2].replace('m', ''))
        
        # فعّل الاشتراك
        activate_subscription(user_id, duration)
        
        # تحديث حالة الدفعة في جدول المدفوعات
        update_payment_status(payment_id, 'completed')
        
        # إزالة الدفعة من جدول المدفوعات المعلقة
        remove_pending_payment(order_id)
        
        # أرسل رسالة للمستخدم
        bot.send_message(
            user_id, 
            f'✅ تم تفعيل اشتراكك لمدة {duration} شهر!' if duration > 0 else '✅ تم تفعيل اشتراكك التجريبي!'
        )
    elif payment_status == 'failed' or payment_status == 'cancelled':
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
    
    return jsonify({'status': 'ok'}), 200

def activate_subscription(user_id, duration_months):
    """تفعيل الاشتراك في قاعدة البيانات"""
    add_subscriber(user_id, None, duration_months)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
