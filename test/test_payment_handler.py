import sys
import os
from unittest.mock import patch, MagicMock
import asyncio
import pytest

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from SubscriptionsBot.Payment_handler import PaymentHandler, generate_order_id
from SubscriptionsBot.config import NOWPAYMENTS_API_KEY, NBP_API_KEY, SUBS_BOT_TOKEN, ADMIN_TELEGRAM_ID
from setup_database import setup_database, DB_FILE # Import setup_database and DB_FILE

@pytest.fixture(scope="function")
def setup_teardown_database():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    setup_database()
    yield
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

@pytest.fixture(scope="function")
def payment_handler(setup_teardown_database):
    return PaymentHandler()

@patch('SubscriptionsBot.Payment_handler.NOWPaymentsAPI')
def test_create_payment(MockNOWPaymentsAPI, payment_handler):
    mock_api_instance = MockNOWPaymentsAPI.return_value
    mock_api_instance.create_payment.return_value = {
        "payment_id": "test_payment_id",
        "pay_address": "test_pay_address",
        "price_amount": 10.0,
        "price_currency": "usd",
        "pay_amount": 0.001,
        "pay_currency": "btc",
        "order_id": "test_order_id",
        "gmt_create": "2023-01-01T12:00:00.000Z"
    }

    user_id = 123
    amount_usd = 10
    currency = "btc"
    order_id = generate_order_id(user_id)

    payment_data = asyncio.run(payment_handler.create_payment(user_id, amount_usd, currency, order_id))

    assert payment_data is not None
    assert payment_data["order_id"] == order_id
    mock_api_instance.create_payment.assert_called_once()

@patch('SubscriptionsBot.Payment_handler.NOWPaymentsAPI')
def test_get_payment_status(MockNOWPaymentsAPI, payment_handler):
    mock_api_instance = MockNOWPaymentsAPI.return_value
    mock_api_instance.get_payment_status.return_value = {
        "payment_id": "test_payment_id",
        "payment_status": "waiting",
        "pay_address": "test_pay_address",
        "price_amount": 10.0,
        "price_currency": "usd",
        "pay_amount": 0.001,
        "pay_currency": "btc",
        "order_id": "test_order_id",
        "gmt_create": "2023-01-01T12:00:00.000Z"
    }

    payment_id = "test_payment_id"
    status_data = asyncio.run(payment_handler.get_payment_status(payment_id))

    assert status_data is not None
    assert status_data["payment_status"] == "waiting"
    mock_api_instance.get_payment_status.assert_called_once_with(payment_id)

@patch('SubscriptionsBot.Payment_handler.NOWPaymentsAPI')
def test_get_exchange_rate(MockNOWPaymentsAPI, payment_handler):
    mock_api_instance = MockNOWPaymentsAPI.return_value
    mock_api_instance.get_exchange_rate.return_value = {
        "currency_from": "usd",
        "currency_to": "btc",
        "estimated_amount": 0.00005,
    }

    amount_usd = 1
    currency = "btc"
    exchange_rate_data = asyncio.run(payment_handler.get_exchange_rate(amount_usd, currency))

    assert exchange_rate_data is not None
    assert exchange_rate_data["currency_from"] == "usd"
    assert exchange_rate_data["currency_to"] == "btc"
    mock_api_instance.get_exchange_rate.assert_called_once_with(amount_usd, currency)

@patch('SubscriptionsBot.Payment_handler.NOWPaymentsAPI')
def test_get_min_amount(MockNOWPaymentsAPI, payment_handler):
    mock_api_instance = MockNOWPaymentsAPI.return_value
    mock_api_instance.get_min_amount.return_value = {
        "currency_from": "usd",
        "currency_to": "btc",
        "min_amount": 0.5,
    }

    currency_from = "usd"
    currency_to = "btc"
    min_amount_data = asyncio.run(payment_handler.get_min_amount(currency_from, currency_to))

    assert min_amount_data is not None
    assert min_amount_data["currency_from"] == "usd"
    assert min_amount_data["currency_to"] == "btc"
    mock_api_instance.get_min_amount.assert_called_once_with(currency_from, currency_to)

@patch('SubscriptionsBot.Payment_handler.NOWPaymentsAPI')
def test_get_all_currencies(MockNOWPaymentsAPI, payment_handler):
    mock_api_instance = MockNOWPaymentsAPI.return_value
    mock_api_instance.get_all_currencies.return_value = {
        "currencies": [
            {"name": "bitcoin", "ticker": "btc"},
            {"name": "ethereum", "ticker": "eth"}
        ]
    }

    currencies_data = asyncio.run(payment_handler.get_all_currencies())

    assert currencies_data is not None
    assert isinstance(currencies_data["currencies"], list)
    assert len(currencies_data["currencies"]) > 0
    mock_api_instance.get_all_currencies.assert_called_once()

@patch('SubscriptionsBot.Payment_handler.NOWPaymentsAPI')
def test_get_all_fiat_currencies(MockNOWPaymentsAPI, payment_handler):
    mock_api_instance = MockNOWPaymentsAPI.return_value
    mock_api_instance.get_all_fiat_currencies.return_value = {
        "fiat_currencies": [
            {"name": "united-states-dollar", "ticker": "usd"},
            {"name": "euro", "ticker": "eur"}
        ]
    }

    fiat_currencies_data = asyncio.run(payment_handler.get_all_fiat_currencies())

    assert fiat_currencies_data is not None
    assert isinstance(fiat_currencies_data["fiat_currencies"], list)
    assert len(fiat_currencies_data["fiat_currencies"]) > 0
    mock_api_instance.get_all_fiat_currencies.assert_called_once()

@patch('SubscriptionsBot.Payment_handler.NOWPaymentsAPI')
def test_get_all_available_pairs(MockNOWPaymentsAPI, payment_handler):
    mock_api_instance = MockNOWPaymentsAPI.return_value
    mock_api_instance.get_all_available_pairs.return_value = {
        "available_pairs": [
            {"from": "usd", "to": "btc"},
            {"from": "eur", "to": "eth"}
        ]
    }

    available_pairs_data = asyncio.run(payment_handler.get_all_available_pairs())

    assert available_pairs_data is not None
    assert isinstance(available_pairs_data["available_pairs"], list)
    assert len(available_pairs_data["available_pairs"]) > 0
    mock_api_instance.get_all_available_pairs.assert_called_once()

@patch('SubscriptionsBot.Payment_handler.NOWPaymentsAPI')
def test_get_all_coins(MockNOWPaymentsAPI, payment_handler):
    mock_api_instance = MockNOWPaymentsAPI.return_value
    mock_api_instance.get_all_coins.return_value = {
        "coins": [
            {"name": "bitcoin", "ticker": "btc"},
            {"name": "ethereum", "ticker": "eth"}
        ]
    }

    coins_data = asyncio.run(payment_handler.get_all_coins())

    assert coins_data is not None
    assert isinstance(coins_data["coins"], list)
    assert len(coins_data["coins"]) > 0
    mock_api_instance.get_all_coins.assert_called_once()

@patch('SubscriptionsBot.Payment_handler.NOWPaymentsAPI')
def test_get_all_networks(MockNOWPaymentsAPI, payment_handler):
    mock_api_instance = MockNOWPaymentsAPI.return_value
    mock_api_instance.get_all_networks.return_value = {
        "networks": [
            {"network": "eth", "currency": "ethereum"},
            {"network": "bsc", "currency": "binancecoin"}
        ]
    }

    networks_data = asyncio.run(payment_handler.get_all_networks())

    assert networks_data is not None
    assert isinstance(networks_data["networks"], list)
    assert len(networks_data["networks"]) > 0
    mock_api_instance.get_all_networks.assert_called_once()