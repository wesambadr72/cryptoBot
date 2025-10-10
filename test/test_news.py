import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import torch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collections import UserDict
from Jobs.news import escape_markdown, fetch_news_from_rss, analyze_news_with_ProsusAI_finbert_ai, news_job, seen_news, sentiment_labels, CHAT_ID

@pytest.fixture
def reset_seen_news():
    seen_news.clear()
    yield
    seen_news.clear()

def test_escape_markdown():
    text = "*bold* _italic_ [link](url) ~strikethrough~ `code` >quote #header +list -list =code |table { }"
    expected = "\\*bold\\* \\_italic\\_ \\[link\\]\\(url\\) \\~strikethrough\\~ \\`code\\` \\>quote \\#header \\+list \\-list \\=code \\|table \\{ \\}"
    assert escape_markdown(text) == expected
    assert escape_markdown("normal text") == "normal text"
    assert escape_markdown("") == ""

class FakeEntry(UserDict):
    def __getattr__(self, name):
        return self[name]

@pytest.mark.asyncio
async def test_fetch_news_from_rss_success(mocker, reset_seen_news):
    entry1 = FakeEntry(title='News1', link='link1', published='2023-01-01', summary='sum1')
    entry2 = FakeEntry(title='News2', link='link2', summary='sum2')
    mock_feed = MagicMock()
    mock_feed.entries = [entry1, entry2]
    mocker.patch('feedparser.parse', return_value=mock_feed)
    result = await fetch_news_from_rss()
    assert len(result) == 2
    assert result[0]['title'] == 'News1'
    assert result[0]['published'] == '2023-01-01'
    assert result[1]['published'] == "Time of publishing NOT FOUND"
    # Duplicate
    result2 = await fetch_news_from_rss()
    assert len(result2) == 0

@pytest.mark.asyncio
async def test_fetch_news_from_rss_empty(mocker, reset_seen_news):
    mock_feed = MagicMock()
    mock_feed.entries = []
    mocker.patch('feedparser.parse', return_value=mock_feed)
    result = await fetch_news_from_rss()
    assert result == []

@pytest.mark.asyncio
async def test_fetch_news_from_rss_error(mocker, reset_seen_news):
    mocker.patch('feedparser.parse', side_effect=Exception("Parse error"))
    result = await fetch_news_from_rss()
    assert result == []

@pytest.mark.asyncio
async def test_analyze_news_with_ProsusAI_finbert_ai_success(mocker):
    news = {'summary': 'Positive news'}
    mock_inputs = {'input_ids': torch.tensor([[1,2,3]]), 'attention_mask': torch.tensor([[1,1,1]])}
    mock_tokenizer = mocker.patch('Jobs.news.tokenizer', return_value=mock_inputs)
    mock_outputs = MagicMock(logits=torch.tensor([[ -1.0, 2.0, -1.0 ]]))  # Assuming indices: 0 negative, 1 positive, 2 neutral
    mocker.patch('Jobs.news.model', return_value=mock_outputs)
    mocker.patch('torch.nn.functional.softmax', return_value=torch.tensor([[0.015, 0.97, 0.015]]))
    result = await analyze_news_with_ProsusAI_finbert_ai(news)
    assert result['sentiment'] == sentiment_labels[1]  # positive
    assert result['confidence'] == pytest.approx(0.97, 0.01)
    # Negative
    mocker.patch('torch.nn.functional.softmax', return_value=torch.tensor([[0.97, 0.015, 0.015]]))
    result_neg = await analyze_news_with_ProsusAI_finbert_ai(news)
    assert result_neg['sentiment'] == sentiment_labels[0]
    # Neutral
    mocker.patch('torch.nn.functional.softmax', return_value=torch.tensor([[0.015, 0.015, 0.97]]))
    result_neu = await analyze_news_with_ProsusAI_finbert_ai(news)
    assert result_neu['sentiment'] == sentiment_labels[2]

@pytest.mark.asyncio
async def test_analyze_news_with_ProsusAI_finbert_ai_error(mocker):
    news = {'summary': 'news'}
    mocker.patch('Jobs.news.tokenizer', side_effect=Exception("Token error"))
    result = await analyze_news_with_ProsusAI_finbert_ai(news)
    assert result == {"sentiment": "Error", "confidence": 0.0}

@pytest.mark.asyncio
async def test_news_job_no_chat_id(mocker):
    mocker.patch('Jobs.news.CHAT_ID', None)
    result = await news_job(MagicMock())
    assert result == []

@pytest.mark.asyncio
async def test_news_job_empty_news(mocker):
    mocker.patch('Jobs.news.CHAT_ID', '123')
    mocker.patch('Jobs.news.fetch_news_from_rss', return_value=[])
    result = await news_job(MagicMock())
    assert result == []

@pytest.mark.asyncio
async def test_news_job_success(mocker):
    mocker.patch('Jobs.news.CHAT_ID', '123')
    mock_news = [{'title': 'Title', 'link': 'link', 'published': 'date', 'summary': 'short summary'}]
    mocker.patch('Jobs.news.fetch_news_from_rss', return_value=mock_news)
    mock_analysis = {'sentiment': 'positive', 'confidence': 0.9}
    mocker.patch('Jobs.news.analyze_news_with_ProsusAI_finbert_ai', return_value=mock_analysis)
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    context = MagicMock(bot=mock_bot)
    result = await news_job(context)
    assert result == mock_news
    mock_bot.send_message.assert_called_once()
    # Long summary
    long_summary = 'a' * 2000
    long_news = [{'title': 'Title', 'link': 'link', 'published': 'date', 'summary': long_summary}]
    mocker.patch('Jobs.news.fetch_news_from_rss', return_value=long_news)
    await news_job(context)
    _, kwargs = mock_bot.send_message.call_args_list[1]
    assert len(kwargs['text'].split('📰 ')[1].split('\n\n')[0]) == 1006  # 1000 + len("\\.\\.\\.") = 6

@pytest.mark.asyncio
async def test_news_job_send_error(mocker):
    mocker.patch('Jobs.news.CHAT_ID', '123')
    mock_news = [{'title': 'Title', 'link': 'link', 'published': 'date', 'summary': 'summary'}]
    mocker.patch('Jobs.news.fetch_news_from_rss', return_value=mock_news)
    mocker.patch('Jobs.news.analyze_news_with_ProsusAI_finbert_ai', return_value={'sentiment': 'pos', 'confidence': 0.9})
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock(side_effect=[Exception("Send error"), None])
    context = MagicMock(bot=mock_bot)
    result = await news_job(context)
    assert result == mock_news
    assert mock_bot.send_message.call_count == 2
    # Second call is fallback
    _, kwargs = mock_bot.send_message.call_args_list[1]
    assert kwargs['text'] == "Title\nlink"

@pytest.mark.asyncio
async def test_news_job_overall_error(mocker):
    mocker.patch('Jobs.news.CHAT_ID', '123')
    mocker.patch('Jobs.news.fetch_news_from_rss', side_effect=Exception("Job error"))
    result = await news_job(MagicMock())
    assert result == []