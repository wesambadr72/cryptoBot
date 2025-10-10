# test_news_bot.py

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import hashlib
from datetime import datetime
import sys
import os
import torch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# استيراد الوظائف والكائنات من الملف الذي تريد اختباره
# افترضنا أن اسم الملف هو news_bot.py
from Jobs.news import (
    escape_markdown,
    fetch_news_from_rss,
    analyze_news_with_ProsusAI_finbert_ai,
    news_job,
    seen_news,
    CHAT_ID
)

# --- Fixtures (بيانات اختبار قابلة لإعادة الاستخدام) ---

@pytest.fixture
def sample_news_item():
    """يوفر هذا الـ fixture عنصر أخبار نموذجي للاختبار."""
    return {
        "title": "Test News Title with *special* chars",
        "link": "https://example.com/news/1",
        "published": "Mon, 01 Jan 2024 12:00:00 GMT",
        "summary": "This is a test summary. It contains important information."
    }

@pytest.fixture
def mock_context():
    """يوفر هذا الـ fixture كائن context وهمي (mock)."""
    context = MagicMock()
    context.bot = AsyncMock()
    return context

@pytest.fixture(autouse=True)
def clear_seen_news():
    """هذا الـ fixture يعمل تلقائيًا قبل كل اختبار لمسح مجموعة الأخبار التي تم رؤيتها."""
    seen_news.clear()

# --- اختبارات دالة escape_markdown ---

def test_escape_markdown_with_special_chars():
    """اختبار أن الأحرف الخاصة في Markdown يتم تهريبها بشكل صحيح."""
    text = "This is a *test* with _special_ [chars](link)."
    expected = r"This is a \*test\* with \_special\_ \[chars\]\(link\)\."
    assert escape_markdown(text) == expected

def test_escape_markdown_without_special_chars():
    """اختبار نص لا يحتوي على أحرف خاصة."""
    text = "This is a normal text."
    assert escape_markdown(text) == r"This is a normal text\."

def test_escape_markdown_empty_string():
    """اختبار سلسلة نصية فارغة."""
    assert escape_markdown("") == ""

# --- اختبارات دالة fetch_news_from_rss ---

@pytest.mark.asyncio
async def test_fetch_news_success(monkeypatch):
    """اختبار سيناريو نجح جلب الأخبار من مصدر RSS."""
    # محاكاة قائمة الروابط
    fake_feeds = ["https://fake-rss.com/feed"]
    monkeypatch.setattr("Jobs.news.RSS_FEEDS", fake_feeds)

    # إنشاء بيانات وهمية لـ feedparser
    mock_entry = MagicMock()
    mock_entry.title = "Fake Title"
    mock_entry.link = "https://fake.com/link"
    mock_entry.summary = "Fake summary"
    mock_entry.published = "Mon, 01 Jan 2024 12:00:00 GMT"

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    # استخدام patch لمحاكاة feedparser.parse
    with patch('Jobs.news.feedparser.parse', return_value=mock_feed) as mock_parse:
        news_list = await fetch_news_from_rss()

        # التحققات (Assertions)
        mock_parse.assert_called_once_with("https://fake-rss.com/feed")
        assert len(news_list) == 1
        assert news_list[0]['title'] == "Fake Title"
        # التحقق من أن المعرف الفريد تمت إضافته إلى المجموعة
        expected_id = hashlib.md5(("Fake Title" + "https://fake.com/link").encode()).hexdigest()
        assert expected_id in seen_news

@pytest.mark.asyncio
async def test_fetch_news_with_duplicates(monkeypatch):
    """اختبار أن الأخبار المكررة لا يتم جلبها مرة أخرى."""
    fake_feeds = ["https://fake-rss.com/feed"]
    monkeypatch.setattr("Jobs.news.RSS_FEEDS", fake_feeds)

    mock_entry = MagicMock()
    mock_entry.title = "Duplicate Title"
    mock_entry.link = "https://fake.com/duplicate"
    mock_entry.summary = "Duplicate summary"
    mock_entry.published = "Mon, 01 Jan 2024 12:00:00 GMT"

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with patch('Jobs.news.feedparser.parse', return_value=mock_feed):
        # المرة الأولى: يجب أن يتم جلب الخبر
        news_list_1 = await fetch_news_from_rss()
        assert len(news_list_1) == 1

        # المرة الثانية: يجب ألا يتم جلب الخبر لأنه مكرر
        news_list_2 = await fetch_news_from_rss()
        assert len(news_list_2) == 0

@pytest.mark.asyncio
async def test_fetch_news_entry_without_published_date(monkeypatch):
    """اختبار معالجة خبر لا يحتوي على تاريخ نشر."""
    fake_feeds = ["https://fake-rss.com/feed"]
    monkeypatch.setattr("Jobs.news.RSS_FEEDS", fake_feeds)

    mock_entry = MagicMock()
    mock_entry.title = "No Date Title"
    mock_entry.link = "https://fake.com/nodate"
    mock_entry.summary = "No date summary"
    # محاكاة عدم وجود حقل published
    mock_entry.get.return_value = None
    # del mock_entry.published

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with patch('Jobs.news.feedparser.parse', return_value=mock_feed):
        news_list = await fetch_news_from_rss()
        assert len(news_list) == 1
        # التحقق من استخدام التاريخ الافتراضي
        assert "Time of publishing NOT FOUND" in news_list[0]['published']

@pytest.mark.asyncio
async def test_fetch_news_feedparser_exception(monkeypatch):
    """اختبار سيناريو حدوث خطأ أثناء جلب الأخبار."""
    fake_feeds = ["https://fake-rss.com/feed"]
    monkeypatch.setattr("Jobs.news.RSS_FEEDS", fake_feeds)

    with patch('Jobs.news.feedparser.parse', side_effect=Exception("Network error")) as mock_parse:
        with patch('Jobs.news.logger.error') as mock_logger:
            news_list = await fetch_news_from_rss()
            mock_parse.assert_called_once()
            mock_logger.assert_called_once()
            assert "Error in fetch_news_from_rss: Network error" in mock_logger.call_args[0][0]
            assert news_list == []

# --- اختبارات دالة analyze_news_with_ProsusAI_finbert_ai ---

@pytest.mark.asyncio
async def test_analyze_news_success(sample_news_item):
    """اختبار سيناريو نجح تحليل الخبر."""
    # محاكاة مخرجات النموذج
    mock_outputs = MagicMock()
    mock_outputs.logits = MagicMock()
    
    # محاكاة سلوك torch
    mock_predictions_tensor = MagicMock()
    mock_predictions_tensor.argmax.return_value = torch.tensor(1)
    mock_predictions_tensor.__getitem__.return_value.__getitem__.return_value.item.return_value = 0.8
    with patch('Jobs.news.torch.nn.functional.softmax', return_value=mock_predictions_tensor) as mock_softmax, \
         patch('Jobs.news.tokenizer', return_value={"input_ids": "fake_tensor"}) as mock_tokenizer, \
         patch('Jobs.news.model', return_value=mock_outputs) as mock_model:
        
        # افترض أن التسميات هي ['positive', 'negative', 'neutral']
        with patch('Jobs.news.sentiment_labels', ['positive', 'negative', 'neutral']):
            analysis = await analyze_news_with_ProsusAI_finbert_ai(sample_news_item)

            # التحققات
            mock_tokenizer.assert_called_once()
            mock_model.assert_called_once()
            mock_softmax.assert_called_once()
            mock_predictions_tensor.argmax.assert_called_once_with(dim=-1)

            assert analysis["sentiment"] == "negative"
            assert analysis["confidence"] == 0.8

@pytest.mark.asyncio
async def test_analyze_news_model_exception(sample_news_item):
    """اختبار سيناريو حدوث خطأ في النموذج أثناء التحليل."""
    with patch('Jobs.news.tokenizer', side_effect=RuntimeError("Model crashed")) as mock_tokenizer, \
         patch('Jobs.news.logger.error') as mock_logger:
        
        analysis = await analyze_news_with_ProsusAI_finbert_ai(sample_news_item)

        mock_tokenizer.assert_called_once()
        mock_logger.assert_called_once()
        assert "Error in analyze_news_with_ProsusAI_finbert_ai: Model crashed" in mock_logger.call_args[0][0]
        assert analysis["sentiment"] == "Error"
        assert analysis["confidence"] == 0.0

# --- اختبارات دالة news_job ---

@pytest.mark.asyncio
async def test_news_job_success_flow(mock_context, sample_news_item, monkeypatch):
    """اختبار التدفق الكامل للوظيفة عند نجاح جميع الخطوات."""
    monkeypatch.setattr("Jobs.news.CHAT_ID", "12345")

    # محاكاة قائمة الأخبار والتحليل
    mock_news_list = [sample_news_item]
    mock_analysis = {"sentiment": "positive", "confidence": 0.95}

    with patch('Jobs.news.fetch_news_from_rss', new_callable=AsyncMock, return_value=mock_news_list) as mock_fetch, \
         patch('Jobs.news.analyze_news_with_ProsusAI_finbert_ai', new_callable=AsyncMock, return_value=mock_analysis) as mock_analyze:
        
        result = await news_job(mock_context)

        # التحققات
        mock_fetch.assert_called_once()
        mock_analyze.assert_called_once_with(sample_news_item)
        mock_context.bot.send_message.assert_called_once()
        
        # التحقق من محتوى الرسالة المرسلة
        call_args = mock_context.bot.send_message.call_args
        assert call_args[1]['chat_id'] == "12345"
        assert call_args[1]['parse_mode'] == "MarkdownV2"
        assert "Test News Title with \\*special\\* chars" in call_args[1]['text']
        assert "positive" in call_args[1]['text']
        assert "95.00%" in call_args[1]['text']
        assert result == mock_news_list

@pytest.mark.asyncio
async def test_news_job_no_chat_id(mock_context):
    """اختبار سيناريو عدم تعيين CHAT_ID."""
    with patch('Jobs.news.CHAT_ID', None), \
         patch('Jobs.news.logger.warning') as mock_logger:
        
        result = await news_job(mock_context)
        
        mock_logger.assert_called_once_with("CHAT_ID is not set. Cannot send news message.")
        mock_context.bot.send_message.assert_not_called()
        assert result == []

@pytest.mark.asyncio
async def test_news_job_no_news_fetched(mock_context, monkeypatch):
    """اختبار سيناريو عدم جلب أي أخبار جديدة."""
    monkeypatch.setattr("Jobs.news.CHAT_ID", "12345")
    
    with patch('Jobs.news.fetch_news_from_rss', new_callable=AsyncMock, return_value=[]) as mock_fetch:
        result = await news_job(mock_context)
        
        mock_fetch.assert_called_once()
        mock_context.bot.send_message.assert_not_called()
        assert result == []

@pytest.mark.asyncio
async def test_news_job_send_message_fails(mock_context, sample_news_item, monkeypatch):
    """اختبار سيناريو فشل إرسال الرسالة واستخدام الرسالة البديلة."""
    monkeypatch.setattr("Jobs.news.CHAT_ID", "12345")
    mock_news_list = [sample_news_item]
    mock_analysis = {"sentiment": "positive", "confidence": 0.95}

    # جعل المحاكاة ترمي استثناء في المرة الأولى وتنجح في الثانية
    mock_context.bot.send_message.side_effect = [Exception("Telegram API Error"), None]

    with patch('Jobs.news.fetch_news_from_rss', new_callable=AsyncMock, return_value=mock_news_list), \
         patch('Jobs.news.analyze_news_with_ProsusAI_finbert_ai', new_callable=AsyncMock, return_value=mock_analysis), \
         patch('Jobs.news.logger.error') as mock_logger:
        
        await news_job(mock_context)

        # التحقق من أن send_message تم استدعاؤه مرتين
        assert mock_context.bot.send_message.call_count == 2
        
        # التحقق من أن الاستخدام الأول كان بالرسالة الكاملة (والذي فشل)
        first_call_args = mock_context.bot.send_message.call_args_list[0]
        assert "MarkdownV2" in first_call_args[1].values()
        
        # التحقق من أن الاستخدام الثاني كان بالرسالة البسيطة
        second_call_args = mock_context.bot.send_message.call_args_list[1]
        assert second_call_args[1]['text'] == f"{sample_news_item['title']}\n{sample_news_item['link']}"
        
        # التحقق من تسجيل الخطأ
        mock_logger.assert_called_once()
        assert "Error sending message: Telegram API Error" in mock_logger.call_args[0][0]

@pytest.mark.asyncio
async def test_news_job_long_summary_truncation(mock_context, monkeypatch):
    """اختبار أن الملخص الطويل يتم قطعه بشكل صحيح."""
    monkeypatch.setattr("Jobs.news.CHAT_ID", "12345")
    
    # إنشاء خبر بملخص طويل جدًا
    long_summary = "A" * 1100
    news_with_long_summary = {
        "title": "Long Summary News",
        "link": "https://example.com/long",
        "published": "Mon, 01 Jan 2024 12:00:00 GMT",
        "summary": long_summary,
    }
    mock_news_list = [news_with_long_summary]
    mock_analysis = {"sentiment": "neutral", "confidence": 0.5}

    with patch('Jobs.news.fetch_news_from_rss', new_callable=AsyncMock, return_value=mock_news_list), \
         patch('Jobs.news.analyze_news_with_ProsusAI_finbert_ai', new_callable=AsyncMock, return_value=mock_analysis):
        
        await news_job(mock_context)
        
        call_args = mock_context.bot.send_message.call_args
        message_text = call_args[1]['text']
        
        # التحقق من أن طول الملخص في الرسالة هو 1000 حرف + "\.\.\."
        summary_part = message_text.split("📰 ")[1].split("\n\n")[0]
        assert len(summary_part) == 1000 + len("\\.\\.\\.")
        assert summary_part.endswith("\\.\\.\\.")
