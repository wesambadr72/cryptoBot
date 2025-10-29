from flask import Flask, request, jsonify
from payment_handler import PaymentHandler
import sqlite3
from datetime import datetime, timedelta
from setup_database import add_subscriber

app = Flask(__name__)
payment_handler = PaymentHandler()

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
    
    if payment_status == 'finished':
        # استخرج user_id من order_id
        user_id = int(order_id.split('_')[1])
        duration = int(order_id.split('_')[2].replace('m', ''))
        
        # فعّل الاشتراك
        activate_subscription(user_id, duration)
        
        # أرسل رسالة للمستخدم
        bot.send_message(
            user_id, 
            f'✅ تم تفعيل اشتراكك لمدة {duration} شهر!' if duration > 0 else '✅ تم تفعيل اشتراكك التجريبي!'
        )
    
    return jsonify({'status': 'ok'}), 200

def activate_subscription(user_id, duration_months):
    """تفعيل الاشتراك في قاعدة البيانات"""
    add_subscriber(user_id, None, duration_months)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
