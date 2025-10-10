from utils.logging import logger
import feedparser
import hashlib
from datetime import datetime
from handlers import CHAT_ID
from config import RSS_FEEDS
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import asyncio
import re

#Model for sentiment analysis(موديل تحليل المشاعر)
model_name = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
sentiment_labels = [model.config.id2label[i] for i in range(len(model.config.id2label))]#["positive","negative","neutral"]


# list for storing seen news
seen_news = set()

# Function to escape special characters in Markdown( للتحقق من وجود الأحرف الخاصة في Markdown)
def escape_markdown(text: str) -> str:
    # تهريب الأحرف الخاصة في MarkdownV2 باستثناء تلك الموجودة في الروابط
    # الأحرف التي يجب تهريبها: _, *, [, ], (, ), ~, `, >, #, +, -, =, |, {, }, ., !
    # ولكن ( و ) لا يجب تهريبهما إذا كانا جزءًا من رابط [نص](رابط)
    # هذا التعبير العادي يقوم بتهريب جميع الأحرف الخاصة باستثناء تلك الموجودة في الروابط
    # هذا حل مبسط وقد لا يغطي جميع الحالات المعقدة لـ MarkdownV2
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


async def fetch_news_from_rss():
    """
    -------------------------
    وظيفة لجلب الأخبار من مصادر RSS
    -------------------------
    """
    news_list = []
    try:
        for feed_url in RSS_FEEDS:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                uniq_id = hashlib.md5((entry.title + entry.link).encode()).hexdigest()
                if uniq_id not in seen_news:
                    news_list.append({
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.get("published") or "Time of publishing NOT FOUND",
                        "summary": entry.summary,
                    })
                    seen_news.add(uniq_id)
        return news_list
    except Exception as e:
        logger.error(f"Error in fetch_news_from_rss: {e}")
        return []


async def analyze_news_with_ProsusAI_finbert_ai(news): 
     """
     -------------------------
     تحليل الأخبار باستخدام النموذج ProsusAI/finbert
     -------------------------
     """ 
     try: 
         def run_analysis(): 
             inputs = tokenizer( 
                 news["summary"], 
                 return_tensors="pt", 
                 truncation=True, 
                 padding=True, 
                 max_length=256 
             ) 
             with torch.no_grad(): 
                 outputs = model(**inputs) 
                 predictions = torch.nn.functional.softmax(outputs.logits, dim=-1) 
                 sentiment_idx = predictions.argmax(dim=-1).item() 
             return { 
                 "sentiment": sentiment_labels[sentiment_idx], 
                 "confidence": predictions[0][sentiment_idx].item() 
             } 

         return await asyncio.to_thread(run_analysis) 
     except Exception as e: 
         logger.error(f"Error in analyze_news_with_ProsusAI_finbert_ai: {e}") 
         return {"sentiment": "Error", "confidence": 0.0} 
 
async def news_job(context): 
    """
    -------------------------
    الوظيفة الرئيسية لجلب وتحليل الأخبار
    -------------------------
    """
    if not CHAT_ID: 
        logger.warning("CHAT_ID is not set. Cannot send news message.") 
        return [] 

    try: 
        news_list = await fetch_news_from_rss() 
        if not news_list: 
            return [] 

        tasks = [analyze_news_with_ProsusAI_finbert_ai(news) for news in news_list] 
        results = await asyncio.gather(*tasks) 

        for news, analysis in zip(news_list, results): 
            safe_title = escape_markdown(news['title']) 
            safe_summary = escape_markdown(news['summary']) 
            if len(safe_summary) > 1000: 
                safe_summary = safe_summary[:1000] + "\\.\\.\\." 
            
            message = ( 
                f"🗞 العنوان : *{safe_title}*\n\n" 
                f"📅 تاريخ النشر : {news['published']}\n" 
                f"📰 {safe_summary}\n\n" 
                f"🔍 شعور الخبر : {analysis['sentiment']}\n" 
                f"📊 احتمالية شعور الخبر : {analysis['confidence']:.2%}\n" 
                f"🔗 [اقرأ المزيد]({news['link']})" 
            ) 

            try: 
                await context.bot.send_message( 
                    chat_id=CHAT_ID, 
                    text=message, 
                    parse_mode="MarkdownV2", 
                    disable_web_page_preview=True 
                ) 
            except Exception as e: 
                logger.error(f"Error sending message: {e}") 
                await context.bot.send_message( 
                    chat_id=CHAT_ID, 
                    text=f"{news['title']}\n{news['link']}" 
                ) 

        return news_list 
    except Exception as e: 
        logger.error(f"Error in news_job: {e}")
        return []