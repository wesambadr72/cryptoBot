import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from SubscriptionsBot import Sbot
from config import CHANNEL_LINK, CHANNEL_ID

@pytest.fixture
def mock_update():
    update = AsyncMock()
    update.message.from_user.id = 123
    update.message.from_user.username = "testuser"
    update.message.reply_text = AsyncMock()
    update.callback_query = AsyncMock()
    update.callback_query.from_user.id = 123
    update.callback_query.from_user.username = "testuser"
    update.callback_query.message.edit_text = AsyncMock()
    return update

@pytest.fixture
def mock_context():
    context = AsyncMock()
    context.bot.send_message = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    context.bot_data = {'channel_id': CHANNEL_ID}
    return context

@pytest.mark.asyncio
async def test_start_command(mock_update, mock_context):
    await Sbot.start_command(mock_update, mock_context)
    mock_context.bot.send_message.assert_called_once()
    args, kwargs = mock_context.bot.send_message.call_args
    assert "الرجاء اختيار لغتك المفضلة" in kwargs['text']
    assert "reply_markup" in kwargs

@pytest.mark.asyncio
@patch('config.PAYMENTS_PALNS')
@patch('SubscriptionsBot.Sbot.MESSAGES')
async def test_select_plan_command(MockMessages, MockPaymentsPalns, mock_update, mock_context):
    MockMessages.return_value = {
        'ar': {
            'select_plan': "الرجاء اختيار الخطة",
            'one_day_trial': "تجربة يوم واحد",
            'one_month_subscription': "اشتراك شهر واحد",
            'three_month_subscription': "اشتراك ثلاثة أشهر",
            'six_month_subscription': "اشتراك ستة أشهر"
        }
    }
    MockPaymentsPalns.return_value = {
        '1_DAY_TRIAL': 0,
        '1_MONTH': 13.99,
        '3_MONTHS': 35.67,
        '6_MONTHS': 53.18
    }
    mock_context.user_data = {'language': 'ar'}
    await Sbot.start_subscription(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    args, kwargs = mock_update.message.reply_text.call_args
    assert "الرجاء اختيار الخطة" in args[0]
    assert "reply_markup" in kwargs

@pytest.mark.asyncio
async def test_button_callback_select_plan(mock_update, mock_context):
    mock_update.callback_query.data = "plan_1month_0.0"
    mock_context.user_data = {'language': 'ar'}
    await Sbot.handle_plan_selection(mock_update, mock_context)
    mock_update.callback_query.message.edit_text.assert_called_once()
    args, kwargs = mock_update.callback_query.message.edit_text.call_args
    assert "تفعيل التجربة المجانية الخاصة بك" in args[0]
    assert CHANNEL_LINK in args[0]

@pytest.mark.asyncio
@patch('SubscriptionsBot.Sbot.add_pending_payment')
@patch('SubscriptionsBot.Sbot.PaymentHandler')
async def test_button_callback_create_payment(MockPaymentHandler, MockAddPendingPayment, mock_update, mock_context):
    mock_update.callback_query.data = "plan_1month_13.99"
    mock_context.user_data = {'language': 'ar'}

    mock_payment_handler_instance = MockPaymentHandler.return_value
    mock_payment_handler_instance.create_payment.return_value = {
        "payment_id": "test_payment_id",
        "pay_address": "test_pay_address",
        "price_amount": 13.99,
        "price_currency": "usd",
        "pay_amount": 13.99,
        "pay_currency": "usdt",
        "order_id": "user_123_1_month_13.99",
        "gmt_create": "2023-01-01T12:00:00.000Z"
    }

    await Sbot.handle_plan_selection(mock_update, mock_context)

    mock_payment_handler_instance.create_payment.assert_called_once_with(13.99, 'usd', 'user_123_1_month_13.99')
    MockAddPendingPayment.assert_called_once()
    mock_update.callback_query.message.edit_text.assert_called_once()
    args, kwargs = mock_update.callback_query.message.edit_text.call_args
    assert "تفاصيل الدفع" in args[0]
    assert "reply_markup" in kwargs

@pytest.mark.asyncio
@patch('SubscriptionsBot.Sbot.PaymentHandler')
async def test_button_callback_check_payment_status_waiting(MockPaymentHandler, mock_update, mock_context):
    mock_update.callback_query.data = "check_payment_status_test_payment_id"
    mock_context.user_data = {'language': 'ar', 'last_order_id': 'user_123_1_month_13.99'}

    mock_payment_handler_instance = MockPaymentHandler.return_value
    mock_payment_handler_instance.get_payment_status.return_value = {
        "payment_id": "test_payment_id",
        "payment_status": "waiting",
        "pay_address": "test_pay_address",
        "price_amount": 13.99,
        "price_currency": "usd",
        "pay_amount": 13.99,
        "pay_currency": "usdt",
        "order_id": "user_123_1_month_13.99",
        "gmt_create": "2023-01-01T12:00:00.000Z"
    }

    await Sbot.check_payment(mock_update, mock_context)

    mock_payment_handler_instance.get_payment_status.assert_called_once_with("test_payment_id")
    mock_update.callback_query.message.edit_text.assert_called_once()
    args, kwargs = mock_update.callback_query.message.edit_text.call_args
    assert "حالة الدفع: في انتظار الدفع" in args[0]
    assert "reply_markup" in kwargs

@pytest.mark.asyncio
@patch('SubscriptionsBot.Sbot.PaymentHandler')
@patch('SubscriptionsBot.Sbot.update_payment_status')
@patch('SubscriptionsBot.Sbot.add_or_update_subscription')
@patch('SubscriptionsBot.Sbot.get_user_by_id')
async def test_button_callback_check_payment_status_finished(MockGetUser, MockAddSubscription, MockUpdatePayment, MockPaymentHandler, mock_update, mock_context):
    mock_update.callback_query.data = "check_payment_status_test_payment_id"
    mock_context.user_data = {'payment_id': 'test_payment_id'}

    mock_payment_handler_instance = MockPaymentHandler.return_value
    mock_payment_handler_instance.get_payment_status.return_value = {
        "payment_id": "test_payment_id",
        "payment_status": "finished",
        "pay_address": "test_pay_address",
        "price_amount": 13.99,
        "price_currency": "usd",
        "pay_amount": 13.99,
        "pay_currency": "usdt",
        "order_id": "user_123_1_month_13.99",
        "gmt_create": "2023-01-01T12:00:00.000Z"
    }

    MockGetUser.return_value = {'user_id': 123, 'username': 'testuser'}

    await Sbot.check_payment(mock_update, mock_context)

    mock_payment_handler_instance.get_payment_status.assert_called_once_with("test_payment_id")
    MockUpdatePayment.assert_called_once()
    MockAddSubscription.assert_called_once()
    mock_update.callback_query.message.edit_text.assert_called_once()
    args, kwargs = mock_update.callback_query.message.edit_text.call_args
    assert "تم تأكيد الدفع بنجاح!" in args[0]
    assert CHANNEL_LINK in args[0]

@pytest.mark.asyncio
@patch('SubscriptionsBot.Sbot.add_pending_payment')
@patch('SubscriptionsBot.Sbot.PaymentHandler')
async def test_create_payment_request_success(MockPaymentHandler, MockAddPendingPayment, mock_update, mock_context):
    mock_update.callback_query.data = "plan_1month_13.99"
    mock_context.user_data = {'language': 'ar'}

    mock_payment_handler_instance = MockPaymentHandler.return_value
    mock_payment_handler_instance.create_payment.return_value = {
        "payment_id": "test_payment_id",
        "pay_address": "test_pay_address",
        "price_amount": 13.99,
        "price_currency": "usd",
        "pay_amount": 13.99,
        "pay_currency": "usdt",
        "order_id": "user_123_1_month_13.99",
        "gmt_create": "2023-01-01T12:00:00.000Z"
    }

    await Sbot.handle_plan_selection(mock_update, mock_context)

    mock_payment_handler_instance.create_payment.assert_called_once_with(13.99, 'usd', 'user_123_1_month_13.99')
    MockAddPendingPayment.assert_called_once()
    mock_update.callback_query.message.edit_text.assert_called_once()
    args, kwargs = mock_update.callback_query.message.edit_text.call_args
    assert "تفاصيل الدفع" in args[0]
    assert "reply_markup" in kwargs

@pytest.mark.asyncio
@patch('SubscriptionsBot.Sbot.update_payment_status')
@patch('SubscriptionsBot.Sbot.add_or_update_subscription')
@patch('SubscriptionsBot.Sbot.get_user_by_id')
async def test_check_payment_status_finished(MockGetUser, MockAddSubscription, MockUpdatePayment, MockPaymentHandler, mock_update, mock_context):
    mock_context.user_data = {'payment_id': 'test_payment_id'}

    mock_payment_handler_instance = MockPaymentHandler.return_value
    mock_payment_handler_instance.get_payment_status.return_value = {
        "payment_id": "test_payment_id",
        "payment_status": "finished",
        "pay_address": "test_pay_address",
        "price_amount": 10.0,
        "price_currency": "usd",
        "pay_amount": 10.0,
        "pay_currency": "usdt",
        "order_id": "user_123_1_month_10",
        "gmt_create": "2023-01-01T12:00:00.000Z"
    }

    MockGetUser.return_value = {'user_id': 123, 'username': 'testuser'}

    await Sbot.check_payment(mock_update, mock_context)

    mock_payment_handler_instance.get_payment_status.assert_called_once_with("test_payment_id")
    MockUpdatePayment.assert_called_once()
    MockAddSubscription.assert_called_once()
    mock_update.callback_query.message.edit_text.assert_called_once()
    args, kwargs = mock_update.callback_query.message.edit_text.call_args
    assert "تم تأكيد الدفع بنجاح!" in args[0]
    assert CHANNEL_LINK in args[0]

@pytest.mark.asyncio
@patch('telegram.ext.CallbackQueryHandler')
@patch('telegram.ext.CommandHandler')
@patch('telegram.ext.Application.builder')
async def test_application_builder_init(MockApplicationBuilder, MockCommandHandler, MockCallbackQueryHandler):
    # Mock the build method to return a mock application instance
    mock_app_instance = MagicMock()
    MockApplicationBuilder.return_value.token.return_value.build.return_value = mock_app_instance

    # Import Sbot after patching to ensure the global app setup uses our mocks
    from SubscriptionsBot import Sbot as Sbot_reloaded

    MockApplicationBuilder.assert_called_once()
    MockApplicationBuilder.return_value.token.assert_called_once_with(os.getenv("SUBS_BOT_TOKEN"))
    MockApplicationBuilder.return_value.token.return_value.build.assert_called_once()

    # Assert that handlers are added
    MockCommandHandler.assert_any_call("start", Sbot_reloaded.start_command)
    MockCallbackQueryHandler.assert_any_call(Sbot_reloaded.handle_language_selection, pattern='^lang_')
    MockCommandHandler.assert_any_call("subscribe", Sbot_reloaded.start_subscription)
    MockCallbackQueryHandler.assert_any_call(Sbot_reloaded.handle_plan_selection, pattern='^plan_')
    MockCommandHandler.assert_any_call("check_payment", Sbot_reloaded.check_payment)
    MockCommandHandler.assert_any_call("help", Sbot_reloaded.help_command)

    mock_app_instance.add_handler.assert_any_call(MockCommandHandler.return_value)
    mock_app_instance.add_handler.assert_any_call(MockCallbackQueryHandler.return_value)