from nowpayments_api import NOWPaymentsAPI
from config import NOWPAYMENTS_API_KEY, NOWPAYMENTS_IPN_KEY, WEBHOOK_URL,SUCCESS_URL,CANCEL_URL
from utils.helpers import generate_order_id
import hmac
import hashlib
import json
from utils.logging import setup_logging # استيراد الـ logger
logger = setup_logging(log_file='nowpayments_crypto_gateway.log', name=__name__) # إعداد الـ logger

class NOWPaymentsCryptoGateway:
    def __init__(self):
        self.api_key = NOWPAYMENTS_API_KEY
        self.ipn_secret = NOWPAYMENTS_IPN_KEY
        self.client = NOWPaymentsAPI(self.api_key, sandbox=False)
        logger.info("NOWPaymentsCryptoGateway initialized.")

    def create_subscription_payment(self, user_id, plan_price, plan_duration):
        order_id = generate_order_id(user_id=user_id, plan_type='subscription', duration=plan_duration)
        logger.info(f"Attempting to create NOWPayments crypto payment for user_id: {user_id}, plan_price: {plan_price}, plan_duration: {plan_duration}, order_id: {order_id}")

        payment_response = self.client.create_payment(
                price_amount=plan_price,
                price_currency='usd',
                pay_amount = plan_price,
                pay_currency='usdtton',
                order_id=order_id,
                order_description=f'{plan_duration} شهر اشتراك',
                ipn_callback_url=WEBHOOK_URL
            )
        logger.info(f"NOWPayments crypto payment created successfully. Payment ID: {payment_response.get('payment_id')}, Invoice URL: {payment_response.get('invoice_url')}. order_id: {order_id}. pay_currency: {payment_response.get('pay_currency')}. price_amount: {payment_response.get('price_amount')}. order_description: {payment_response.get('order_description')}")
        logger.debug(f"Raw payment response: {payment_response}") # Added detailed logging
        
        return {
            'payment_id': int(payment_response.get('payment_id')),
            'order_id': payment_response.get('order_id'),
            'pay_address': payment_response.get('pay_address'),
            'price_amount': payment_response.get('price_amount'),
            'pay_currency': payment_response.get('pay_currency'),
            'invoice_url': payment_response.get('invoice_url'),
            'order_description': payment_response.get('order_description'),
            'network': payment_response.get('network'),
            'payment_status': payment_response.get('payment_status'),
        }
    
    def get_payment_status(self, payment_id):
        logger.info(f"Checking NOWPayments crypto payment status for payment_id: {payment_id}")
        status = self.client.payment_status(payment_id)
        logger.info(f"NOWPayments crypto payment status for {payment_id}: {status.get('payment_status')}")
        return status
    
    def verify_ipn(self, payload, signature):
        logger.info(f"Verifying NOWPayments crypto IPN. Payload: {payload}, Signature: {signature}")
        
        sorted_msg = json.dumps(payload, separators=(',', ':'), sort_keys=True, ensure_ascii=False)
        message = sorted_msg
        calculated_sig = hmac.new(
            str(self.ipn_secret).encode(),
           f"{message}".encode(),
            hashlib.sha512
        ).hexdigest()
        
        is_valid = calculated_sig == signature
        logger.info(f"NOWPayments crypto IPN verification result: {is_valid} signature: {signature} calculated_sig: {calculated_sig}")
        return is_valid