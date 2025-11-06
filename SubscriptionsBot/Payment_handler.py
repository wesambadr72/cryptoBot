from nowpayments_api import NOWPaymentsAPI
from config import NOWPAYMENTS_API_KEY, NOWPAYMENTS_IPN_KEY, WEBHOOK_URL,SUCCESS_URL,CANCEL_URL
from utils.helpers import generate_order_id
import time
import os
import hmac
import hashlib
from utils.logging import logger # استيراد الـ logger
from SubscriptionsBot.payment_gatways.nowpayments_crypto_gateway import NOWPaymentsCryptoGateway
from SubscriptionsBot.payment_gatways.nowpayments_Fiat_gateway import NOWPaymentsFiatGateway

class PaymentHandler:
    def __init__(self):
        self.nowpayments_crypto_gateway = NOWPaymentsCryptoGateway()
        # self.nowpayments_fiat_gateway = NOWPaymentsFiatGateway()
        logger.info("PaymentHandler initialized.") # سجل عند التهيئة
    
    def create_subscription_payment(self, user_id, plan_price, plan_duration, payment_method='crypto'):
        # if payment_method == 'crypto':
            return self.nowpayments_crypto_gateway.create_subscription_payment(user_id, plan_price, plan_duration)
        # elif payment_method == 'fiat':
        #     return self.nowpayments_fiat_gateway.create_subscription_payment(user_id, plan_price, plan_duration)
        # else:
        #     raise ValueError("Invalid payment method specified.")
    
    def get_payment_status(self, payment_id, payment_method='crypto'):
        # if payment_method == 'crypto':
            return self.nowpayments_crypto_gateway.get_payment_status(payment_id)
        # elif payment_method == 'fiat':
        #     return self.nowpayments_fiat_gateway.get_payment_status(payment_id)
        # else:
        #     raise ValueError("Invalid payment method specified.")
    
    def verify_ipn(self, payload, signature, payment_method='crypto'):
        # if payment_method == 'crypto':
            return self.nowpayments_crypto_gateway.verify_ipn(payload, signature)
        # elif payment_method == 'fiat':
        #     return self.nowpayments_fiat_gateway.verify_ipn(payload, signature)
        # else:
        #     raise ValueError("Invalid payment method specified.")