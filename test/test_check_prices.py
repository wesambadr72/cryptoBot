import pytest
from datetime import datetime
from unittest.mock import AsyncMock

# استيراد الوظيفة والوحدات التي تريد اختبارها
# تأكد من أن اسم الملف صحيح
from Jobs.alerts import check_prices

# نستخدم pytest-asyncio للتعامل مع الدوال غير المتزامنة
pytestmark = pytest.mark.asyncio

async def test_check_prices_sends_alert_when_price_increases_and_not_alerted(mocker):
    """
    السيناريو 2: يجب إرسال تنبيه عندما يزداد السعر بنسبة 1.3% ولم يتم التنبيه من قبل.
    """
    # 1. Arrange (إعداد البيانات والـ Mocks)
    
    # محاكاة المتغيرات العامة
    mocker.patch("Jobs.alerts.CHAT_ID", "12345")
    mocker.patch("Jobs.alerts.load_watched_coins", return_value=["BTCUSDT"])

    # محاكاة استجابة API Binance
    mock_prices = [{"symbol": "BTCUSDT", "price": "51300.00"}]
    mocker.patch("Jobs.alerts.get_all_prices", return_value=mock_prices)

    # محاكاة استجابة قاعدة البيانات
    # السعر القديم هو 50000، والسعر الجديد 51300، نسبة التغير = 2.6%
    mocker.patch("Jobs.alerts.get_old_price", return_value=50000.0)
    mocker.patch("Jobs.alerts.already_alerted", return_value=False)
    
    # محاكاة دوال الكتابة في قاعدة البيانات (لا نحتاج لفعل شيء)
    mock_save_price = mocker.patch("Jobs.alerts.save_price")
    mock_save_alert = mocker.patch("Jobs.alerts.save_alert")

    # محاكاة الوقت الحالي
    fixed_time = datetime(2023, 10, 27, 10, 0, 0)
    mock_datetime = mocker.patch("Jobs.alerts.datetime")
    mock_datetime.now.return_value = fixed_time

    # محاكاة البوت الذي سيرسل الرسالة
    mock_bot = AsyncMock()
    mock_context = AsyncMock()
    mock_context.bot = mock_bot

    # 2. Act (تنفيذ الوظيفة)
    await check_prices(mock_context)

    # 3. Assert (التأكد من النتائج)
    
    # التأكد من أن دالة حفظ السعر تم استدعاؤها
    mock_save_price.assert_called_once_with("BTCUSDT", 51300.0, fixed_time)
    
    # التأكد من أن رسالة تم إرسالها مرة واحدة
    mock_bot.send_message.assert_called_once()
    
    # التأكد من محتوى الرسالة
    call_args = mock_bot.send_message.call_args
    assert call_args[1]['chat_id'] == "12345"
    message_text = call_args[1]['text']
    assert "🚨 تنبيه! BTCUSDT" in message_text
    assert "السعر السابق: 50000.00000000" in message_text
    assert "السعر الحالي: 51300.00000000" in message_text
    assert "نسبة التغير: 2.60%" in message_text

    # التأكد من أن التنبيه تم حفظه في قاعدة البيانات
    mock_save_alert.assert_called_once_with("BTCUSDT", 50000.0, 51300.0, 2.6)


async def test_check_prices_does_nothing_when_change_is_low(mocker):
    """
    السيناريو 1: لا يجب إرسال تنبيه عندما تكون نسبة التغير منخفضة.
    """
    # 1. Arrange
    mocker.patch("Jobs.alerts.CHAT_ID", "12345")
    mocker.patch("Jobs.alerts.load_watched_coins", return_value=["ETHUSDT"])

    mock_prices = [{"symbol": "ETHUSDT", "price": "1805.40"}] # نسبة تغير 0.3%
    mocker.patch("Jobs.alerts.get_all_prices", return_value=mock_prices)
    
    mocker.patch("Jobs.alerts.get_old_price", return_value=1800.0)
    mock_save_price = mocker.patch("Jobs.alerts.save_price")
    
    mock_bot = AsyncMock()
    mock_context = AsyncMock()
    mock_context.bot = mock_bot

    # 2. Act
    await check_prices(mock_context)

    # 3. Assert
    # التأكد من أنه لم يتم إرسال أي رسالة
    mock_bot.send_message.assert_not_called()
    # التأكد من أن السعر تم حفظه على أي حال
    mock_save_price.assert_called_once()