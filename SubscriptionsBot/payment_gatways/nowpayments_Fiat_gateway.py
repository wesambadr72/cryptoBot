from utils.logging import logger

class NOWPaymentsFiatGateway:
    def __init__(self):
        logger.info("NOWPaymentsFiatGateway initialized.")
    
    # Placeholder for future fiat payment methods
    def create_subscription_payment(self, user_id, plan_price, plan_duration):
        logger.info(f"Attempting to create NOWPayments fiat payment for user_id: {user_id}, plan_price: {plan_price}, plan_duration: {plan_duration}")
        # Implement fiat payment logic here
        raise NotImplementedError("Fiat payment method not yet implemented.")

    def get_payment_status(self, payment_id):
        raise NotImplementedError("Fiat payment status check not yet implemented.")

    def verify_ipn(self, payload, signature):
        raise NotImplementedError("Fiat IPN verification not yet implemented.")