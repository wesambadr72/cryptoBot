from utils.logging import logger
from datetime import datetime
from config import RSS_FEEDS,CHANNEL_ID
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from googletrans import Translator
from setup_database import is_news_processed, mark_news_as_processed
from utils.helpers import strip_html_tags_and_unescape_entities
import email.utils as eut
import hashlib
import feedparser
import torch
import asyncio
import re


translator = Translator()
news_lock = asyncio.Lock()



#Model for sentiment analysis(موديل تحليل المشاعر)
model_name = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
sentiment_labels = [model.config.id2label[i] for i in range(len(model.config.id2label))]#["positive","negative","neutral"]







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
                uniq_id = hashlib.md5((entry.title + entry.link + entry.published).encode()).hexdigest()
                if is_news_processed(uniq_id):
                    logger.info(f"News already processed: {entry.title}")
                    continue

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


                # Convert published time to 12-hour format
                if entry.get('published_parsed'):
                    dt = datetime(*entry.published_parsed[:6])
                else:
                    dt = datetime.fromtimestamp(eut.mktime_tz(eut.parsedate_tz(entry.get('published', ''))))

                published_12h = dt.strftime("%a, %d %b %Y • %I:%M %p")

                summary_text = entry.summary or entry.description or entry.title #موقع coindesk ما يعطي summary او description لذلك نرسل title كا حل اخير
                
                news_list.append({
                    "uniq_id": uniq_id,
                    "title": entry.title,
                    "link": entry.link,
                    "published": published_12h or "Time of publishing NOT FOUND",
                    "summary": strip_html_tags_and_unescape_entities(summary_text), 
                    "image_url": image_url,
                })

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
                 max_length=512
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
        chat_id = CHANNEL_ID  # استخدام CHANNEL_ID المستورد من config.py
        if not chat_id:
            logger.warning("CHANNEL_ID is not set. Cannot send news message.")
            return []

        try: 
            news_list = await fetch_news_from_rss() 
            if not news_list: 
                return [] 



            tasks = [analyze_news_with_ProsusAI_finbert_ai(news) for news in news_list] 
            results = await asyncio.gather(*tasks) 



            for news, analysis in zip(news_list, results): 
                original_title = news.get('title','') # الحصول على العنوان الأصلي

                # ترجمة العنوان إلى العربية
                try:
                    title_ar = (await translator.translate(original_title, dest='ar')).text
                except Exception as e:
                    title_ar = '' #يحذف النص بدون مشاكل و يكمل طبيعي
                    logger.error(f"Error in translating title to Arabic: {e}")



                # تهريب النصوص باستخدام HTML
                safe_title_en = strip_html_tags_and_unescape_entities(original_title)
                safe_title_ar = strip_html_tags_and_unescape_entities(title_ar) if title_ar else '' #  يتاكد إذا كان فارغًا، سيكون فارغًا أيضًا 

                summary_text = strip_html_tags_and_unescape_entities(news['summary'])
                safe_summary = strip_html_tags_and_unescape_entities(summary_text)
                
                #كتابة حالة الخبر بالعربي
                sentiment_arabic_map = {
                    "positive": "إيجابي",
                    "negative": "سلبي",
                    "neutral": "محايد"
                }
                safe_sentiment_arabic = sentiment_arabic_map.get(analysis['sentiment'], "غير معروف")

                # تقليل الملخص للصور (caption محدود بـ 1024 حرف)
                if len(safe_summary) > 600:  
                    safe_summary = safe_summary[:600] + "..." 

                # emoji_status = "🔴" if analysis['sentiment'] == "negative" else ("🟢" if analysis['sentiment'] == "positive" else "⚪") طريقة اخرى لكن بجرب switch 
                switch = {
                    "negative": "🔴",
                    "positive": "🟢",
                    "neutral": "⚪",
                }
                emoji_status = switch.get(analysis['sentiment'], "⚪")
                
                safe_published = strip_html_tags_and_unescape_entities(news['published'])
                safe_sentiment = strip_html_tags_and_unescape_entities(analysis['sentiment'])
                safe_confidence = f"{analysis['confidence']:.2%}"
                safe_link = news['link']  # لا نحتاج escape للرابط داخل HTML tag

                title_section = f"<b>🇸🇦 {safe_title_ar}</b>\n <b>🇬🇧 {safe_title_en}</b>\n" if safe_title_ar else f"<b>🇬🇧 {safe_title_en}</b>\n"

                # بناء الرسالة بصيغة HTML

                caption = (
                    f"🗞 العنوان(Title) : \n{title_section}\n"
                    f"📅 تاريخ النشر(Published) : {safe_published}\n"
                    f"📰 {safe_summary}\n"
                    f"\n 🤖 تحليل الخبر (News Analysis) :  \n"
                    f"🔍 شعور الخبر (News Sentiment) : \n{safe_sentiment_arabic} ({safe_sentiment}) {emoji_status}\n"
                    f"📊 احتمالية شعور الخبر (Confidence) : {safe_confidence}\n"
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
                            
                    mark_news_as_processed(news['uniq_id'], news['title'], news['link'])
                except Exception as e:
                    logger.error(f"Error sending message: {e}")



            return news_list
        except Exception as e:
            logger.error(f"Error in news_job: {e}")
            return []
