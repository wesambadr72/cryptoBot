import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from SubscriptionsBot.webhookserver import app, process_successful_payment
from SubscriptionsBot.config import CHANNEL_ID

# Mock the bot and PaymentHandler for testing
@pytest.fixture
def mock_bot():
    with patch('SubscriptionsBot.webhookserver.bot', new_callable=AsyncMock) as mock_b:
        yield mock_b

@pytest.fixture
def mock_payment_handler():
    with patch('SubscriptionsBot.webhookserver.payment_handler', new_callable=MagicMock) as mock_ph:
        mock_ph.verify_ipn.return_value = True
        yield mock_ph

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_ipn_webhook_success(client, mock_bot, mock_payment_handler):
    # Mock process_successful_payment to avoid its internal logic during this test
    with patch('SubscriptionsBot.webhookserver.process_successful_payment', new_callable=AsyncMock) as mock_psp:
        mock_psp.return_value = None

        ipn_data = {
            "payment_id": "test_payment_id",
            "order_id": "user_123_plan_premium",
            "pay_amount": 13.99,
            "pay_currency": "usdt",
            "payment_status": "finished"
        }
        response = client.post("/ipn", json=ipn_data)

        assert response.status_code == 200
        assert response.json() == {"message": "IPN received and processed"}
        mock_payment_handler.verify_ipn.assert_called_once_with(ipn_data)
        mock_psp.assert_called_once_with(ipn_data)

@pytest.mark.asyncio
async def test_ipn_webhook_invalid_ipn(client, mock_bot, mock_payment_handler):
    mock_payment_handler.verify_ipn.return_value = False

    ipn_data = {
        "payment_id": "test_payment_id",
        "order_id": "user_123_plan_premium",
        "pay_amount": 13.99,
        "pay_currency": "usdt",
        "payment_status": "finished"
    }
    response = client.post("/ipn", json=ipn_data)

    assert response.status_code == 400
    assert response.json() == {"message": "Invalid IPN signature"}
    mock_payment_handler.verify_ipn.assert_called_once_with(ipn_data)

@pytest.mark.asyncio
async def test_ipn_webhook_missing_data(client, mock_bot, mock_payment_handler):
    ipn_data = {
        "payment_id": "test_payment_id",
        # "order_id": "user_123_plan_premium", # Missing order_id
        "pay_amount": 10.0,
        "pay_currency": "btc",
        "payment_status": "finished"
    }
    response = client.post("/ipn", json=ipn_data)

    assert response.status_code == 422  # Unprocessable Entity for validation errors
    # FastAPI's default error response for missing fields
    assert "detail" in response.json()

@pytest.mark.asyncio
async def test_process_successful_payment_unban_success(mock_bot, mock_payment_handler):
    ipn_data = {
        "payment_id": "test_payment_id",
        "order_id": "user_123_plan_premium",
        "pay_amount": 10.0,
        "pay_currency": "btc",
        "payment_status": "finished"
    }
    user_id = 123

    # Mock database functions
    with patch('SubscriptionsBot.db.get_user_by_id', return_value={'user_id': user_id, 'username': 'testuser'}), \
         patch('SubscriptionsBot.db.update_payment_status'), \
         patch('SubscriptionsBot.db.add_or_update_subscription'):

        await process_successful_payment(ipn_data)

        mock_bot.unban_chat_member.assert_called_once_with(chat_id=CHANNEL_ID, user_id=user_id)
        mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_process_successful_payment_unban_failure(mock_bot, mock_payment_handler):
    ipn_data = {
        "payment_id": "test_payment_id",
        "order_id": "user_123_plan_premium",
        "pay_amount": 10.0,
        "pay_currency": "btc",
        "payment_status": "finished"
    }
    user_id = 123

    mock_bot.unban_chat_member.side_effect = Exception("Failed to unban")

    with patch('SubscriptionsBot.db.get_user_by_id', return_value={'user_id': user_id, 'username': 'testuser'}), \
         patch('SubscriptionsBot.db.update_payment_status'), \
         patch('SubscriptionsBot.db.add_or_update_subscription'):

        await process_successful_payment(ipn_data)

        mock_bot.unban_chat_member.assert_called_once_with(chat_id=CHANNEL_ID, user_id=user_id)
        mock_bot.send_message.assert_called_once() # Should still send message even if unban fails

@pytest.mark.asyncio
async def test_process_successful_payment_new_user(mock_bot, mock_payment_handler):
    ipn_data = {
        "payment_id": "test_payment_id",
        "order_id": "user_456_plan_basic",
        "pay_amount": 13.99,
        "pay_currency": "usdt",
        "payment_status": "finished"
    }
    user_id = 456

    with patch('SubscriptionsBot.db.get_user_by_id', return_value=None), \
         patch('SubscriptionsBot.db.add_user'), \
         patch('SubscriptionsBot.db.update_payment_status'), \
         patch('SubscriptionsBot.db.add_or_update_subscription'):

        await process_successful_payment(ipn_data)

        mock_bot.unban_chat_member.assert_called_once_with(chat_id=CHANNEL_ID, user_id=user_id) # Still attempts unban, which will gracefully fail
        mock_bot.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_process_successful_payment_unsupported_order_id_format(mock_bot, mock_payment_handler):
    ipn_data = {
        "payment_id": "test_payment_id",
        "order_id": "invalid_order_id_format", # Invalid format
        "pay_amount": 13.99,
        "pay_currency": "usdt",
        "payment_status": "finished"
    }

    with patch('SubscriptionsBot.db.get_user_by_id', return_value={'user_id': 123, 'username': 'testuser'}), \
         patch('SubscriptionsBot.db.update_payment_status'), \
         patch('SubscriptionsBot.db.add_or_update_subscription'):

        await process_successful_payment(ipn_data)

        mock_bot.unban_chat_member.assert_not_called() # Should not attempt unban if user_id cannot be parsed
        mock_bot.send_message.assert_called_once() # Should still send a message, perhaps an error message to admin