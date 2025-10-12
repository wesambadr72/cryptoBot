from utils.logging import logger
import feedparser
import hashlib
from datetime import datetime
from config import RSS_FEEDS
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import asyncio
import html
import re



news_lock = asyncio.Lock()



#Model for sentiment analysis(موديل تحليل المشاعر)
model_name = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
sentiment_labels = [model.config.id2label[i] for i in range(len(model.config.id2label))]#["positive","negative","neutral"]




# list for storing seen news
seen_news = set()



# Function to escape HTML special characters
def escape_html(text: str) -> str:
    """
    تهريب الأحرف الخاصة في HTML
    """
    return html.escape(text)




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
                    image_url = None
                    if 'media_content' in entry and entry['media_content']:
                        for media in entry['media_content']:
                            if media.get('type', '').startswith('image/') and media.get('url'):
                                image_url = media['url']
                                break
                    elif 'enclosures' in entry and entry['enclosures']:
                        for enclosure in entry['enclosures']:
                            if enclosure.get('type', '').startswith('image/') and enclosure.get('url'):
                                image_url = enclosure['url']
                                break
                    
                    # Fallback: try to find an <img> tag in the summary
                    if not image_url and entry.summary:
                        img_match = re.search(r'<img[^>]+src=["\'](.*?)["\']', entry.summary, re.IGNORECASE)
                        if img_match:
                            image_url = img_match.group(1)


                    news_list.append({
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.get("published") or "Time of publishing NOT FOUND",
                        "summary": entry.summary,
                        "image_url": image_url,
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
    async with news_lock:
        """
        -------------------------
        الوظيفة الرئيسية لجلب وتحليل الأخبار
        -------------------------
        """
        chat_id = context.bot_data.get('chat_id')
        if not chat_id: 
            logger.warning("CHAT_ID is not set. Cannot send news message.") 
            return [] 



        try: 
            news_list = await fetch_news_from_rss() 
            if not news_list: 
                return [] 



            tasks = [analyze_news_with_ProsusAI_finbert_ai(news) for news in news_list] 
            results = await asyncio.gather(*tasks) 



            for news, analysis in zip(news_list, results): 
                # تهريب النصوص باستخدام HTML
                safe_title = escape_html(news['title']) 
                safe_summary = escape_html(news['summary'])
                
                # تقليل الملخص للصور (caption محدود بـ 1024 حرف)
                if len(safe_summary) > 600:  
                    safe_summary = safe_summary[:600] + "..." 
                
                safe_published = escape_html(news['published'])
                safe_sentiment = escape_html(analysis['sentiment'])
                safe_confidence = f"{analysis['confidence']:.2%}"
                safe_link = news['link']  # لا نحتاج escape للرابط داخل HTML tag



                # بناء الرسالة بصيغة HTML
                caption = (
                    f"🗞 العنوان : <b>{safe_title}</b>\n"
                    f"📅 تاريخ النشر : {safe_published}\n"
                    f"📰 {safe_summary}\n"
                    f"🔍 شعور الخبر : {safe_sentiment}\n"
                    f"📊 احتمالية شعور الخبر : {safe_confidence} 🟢 \n"
                    if safe_sentiment == "Positive"
                    else f"📊 احتمالية شعور الخبر : {safe_confidence} 🔴 \n"
                    f"🔗 <a href=\"{safe_link}\">اقرأ المزيد</a>"
                )


                try: 
                    if news['image_url']:
                        # إرسال صورة مع caption
                        await context.bot.send_photo(
                            chat_id=chat_id,
                            photo=news['image_url'],
                            caption=caption,
                            parse_mode="HTML"
                        )
                    else:
                        # إرسال رسالة نصية بدون صورة
                        await context.bot.send_message( 
                            chat_id=chat_id, 
                            text=caption, 
                            parse_mode="HTML", 
                            disable_web_page_preview=True  # ✅ فقط في send_message
                        ) 
                except Exception as e: 
                    logger.error(f"Error sending message: {e}") 
                    # في حالة الخطأ، إرسال رسالة بسيطة
                    await context.bot.send_message( 
                        chat_id=chat_id, 
                        text=f"{news['title']}\n{news['link']}\n"
                    ) 


            return news_list 
        except Exception as e: 
            logger.error(f"Error in news_job: {e}")
            return []
