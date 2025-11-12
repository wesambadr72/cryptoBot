from nowpayments_api import NOWPaymentsAPI
from config import NOWPAYMENTS_API_KEY, NOWPAYMENTS_IPN_KEY, WEBHOOK_URL,SUCCESS_URL,CANCEL_URL
from utils.helpers import generate_order_id
import hmac
import hashlib
from utils.logging import logger

class NOWPaymentsCryptoGateway:
    def __init__(self):
        self.api_key = NOWPAYMENTS_API_KEY
        self.ipn_secret = NOWPAYMENTS_IPN_KEY
        self.client = NOWPaymentsAPI(self.api_key, sandbox=False)
        logger.info("NOWPaymentsCryptoGateway initialized.")

    def create_subscription_payment(self, user_id, plan_price, plan_duration):
        order_id = generate_order_id(user_id=user_id, plan_type='subscription', duration=plan_duration)
        logger.info(f"Attempting to create NOWPayments crypto payment for user_id: {user_id}, plan_price: {plan_price}, plan_duration: {plan_duration}, order_id: {order_id}")

        invoice = self.client.create_invoice(
            price_amount=plan_price,
            price_currency='usd',
            pay_currency='usdtton',
            order_id=order_id,
            order_description=f'{plan_duration} شهر اشتراك',
            ipn_callback_url=WEBHOOK_URL,
            success_url=SUCCESS_URL,
            cancel_url=CANCEL_URL
        )
        logger.info(f"NOWPayments crypto invoice created successfully. Invoice ID: {invoice.get('id')}, Invoice URL: {invoice.get('invoice_url')}. Full invoice object: {invoice}")
        
        return {
            'payment_id': invoice.get('id'),
            'pay_address': invoice.get('pay_address'),
            'pay_amount': invoice.get('price_amount'),  # تم التغيير من 'pay_amount' إلى 'price_amount'
            'order_id': invoice.get('order_id'),
            'pay_currency': invoice.get('pay_currency'),
            'invoice_url': invoice.get('invoice_url')
        }
    
    def get_payment_status(self, payment_id):
        logger.info(f"Checking NOWPayments crypto payment status for payment_id: {payment_id}")
        status = self.client.payment_status(payment_id)
        logger.info(f"NOWPayments crypto payment status for {payment_id}: {status.get('payment_status')}")
        return status
    
    def verify_ipn(self, payload, signature):
        logger.info(f"Verifying NOWPayments crypto IPN. Payload: {payload}, Signature: {signature}")
        
        sorted_payload = dict(sorted(payload.items()))
        message = ''.join(str(v) for v in sorted_payload.values())
        
        calculated_sig = hmac.new(
            self.ipn_secret.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()
        
        is_valid = calculated_sig == signature
        logger.info(f"NOWPayments crypto IPN verification result: {is_valid}")
        return is_valid