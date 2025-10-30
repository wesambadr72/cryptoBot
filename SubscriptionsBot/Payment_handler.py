from nowpayments_api import NOWPaymentsAPI
from config import NOWPAYMENTS_API_KEY, NOWPAYMENTS_IPN_KEY, WEBHOOK_URL,SUCCESS_URL,CANCEL_URL
from utils.helpers import generate_order_id
import time
import os
import hmac
import hashlib

class PaymentHandler:
    def _init_(self):
        self.api_key = NOWPAYMENTS_API_KEY
        self.ipn_secret = NOWPAYMENTS_IPN_KEY
        
        
        # استخدم sandbox=True للتجربة أولاً
        self.client = NOWPaymentsAPI(self.api_key, sandbox=True)
    
    def create_subscription_payment(self, user_id, plan_price, plan_duration):
        """إنشاء دفعة جديدة للاشتراك"""
        
        # أنشئ order_id فريد
        order_id = generate_order_id(user_id=user_id, plan_type='subscription', duration=plan_duration)

        payment = self.client.create_payment(
            price_amount=plan_price,
            price_currency='USD',
            pay_currency='USDT',
            order_id=order_id,
            pay_network='TON',
            order_description=f'{plan_duration} شهر اشتراك',
            ipn_callback_url=WEBHOOK_URL,
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL
        )
        
        return {
            'payment_id': payment['payment_id'],
            'pay_address': payment['pay_address'],
            'pay_amount': payment['pay_amount'],
            'order_id':payment['order_id'],
            'pay_currency': payment['pay_currency'],
            'pay_network': payment['pay_network']
        }
    
    def get_payment_status(self, payment_id):
        """التحقق من حالة الدفع"""
        return self.client.payment_status(payment_id)
    
    def verify_ipn(self, payload, signature):
        """التحقق من صحة webhook"""
        
        sorted_payload = dict(sorted(payload.items()))
        message = ''.join(str(v) for v in sorted_payload.values())
        
        calculated_sig = hmac.new(
            self.ipn_secret.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()
        
        return calculated_sig == signature