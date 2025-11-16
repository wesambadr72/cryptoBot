import random
import string
import html
import re
from datetime import datetime, timedelta

def price_change(old_price, new_price):
    return ((new_price - old_price) / old_price) * 100

def format_percentage(value):
    return f"{value:.2f}%"

def format_message(symbol, change, price):
    return f"{symbol}: تغير {format_percentage(change)} والسعر الحالي {price:.2f} USDT"

def generate_order_id(prefix="sub", user_id=None, plan_type=None, duration=None):
    rand_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}_{user_id}_{plan_type}_{duration}_{rand_part}_{ts}"



def is_payment_expired(created_at, timeout_minutes=20):
    created = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
    return datetime.now() > created + timedelta(minutes=timeout_minutes)


def strip_html_tags_and_unescape_entities(text: str) -> str:
    TAG_RE = re.compile(r'<[^>]+>')
    """
    يزيل علامات HTML ويفك تشفير كيانات HTML من النص.
    """
    if not isinstance(text, str):
        return ""
    # فك تشفير كيانات HTML أولاً
    unescaped_text = html.unescape(text)
    # ثم إزالة علامات HTML
    return TAG_RE.sub('', unescaped_text)

def extract_network_from_currency(pay_currency: str) -> str:
    """
    Extracts the network from a given pay_currency string.
    """
    pay_currency = pay_currency.lower()
    if pay_currency.endswith('bsc'):
        return 'Binance Smart Chain (BSC)'
    elif pay_currency.endswith('ton'):
        return 'TON'
    # Add more network extractions as needed
    return 'N/A' # Default if no specific network is identified

MESSAGES = {
    'ar': {
        'welcome': """
        🎉  أهلاً وسهلاً بك في بوت اشتراكات قناة OWL CAB🦉!

        😍يسعدنا انضمامك إلى مجموعة مستخدمي القناة الذكية المختصة بسوق الكريبتو لمساعدتك في متابعة سوق الكريبتو بسهولة ويُسر.
        يمكنك الحصول الان على تجربتك المجانية الأولى والتي تتيح لك:

        تجربة جميع الميزات الحصرية لـمدة محدودة بدون أي التزام!

        متابعة اخر اخبار سوق العملات الرقمية من اكثر من مصدر موثوق📰.

        تحليل للاخبار بالذكاء الاصطناعي AI 🤖

        📊تلقي تنبيهات وتحليلات متقدمة للعملات والأسعار، واكتشاف فرص التداول اللحظية.

        روابط مباشرة للعملات عبر البرنامج الشهير TradingView🔗.

        ملاحظات هامة⚠️:

        تستطيع الاستفادة من جميع الخدمات خلال فترة التجربة المجانية. عند انتهائها، سيطلب منك الاشتراك لمواصلة استخدام الميزات المتقدمة.

        لكل مستخدم تجربة مجانية واحدة فقط، بعدها يمكنك اختيار الباقة المناسبة لك.

        (البوت يعرض معلومات فقط ولا يقدم نصائح استثمارية أو يضمن تحقيق أرباح أو تجنب خسائر. جميع قرارات التداول والاستثمار تقع على عاتق المستخدم وحده).

        إذا واجهتك أي مشكلة أو استفسار، تواصل معنا عبر الحساب @Ws7h9.

        حسابات القناة على وسائل التواصل الاجتماعي:
        - تويتر  (X حالياَ): <a href="https://x.com/OwlBot_72?t=vw5b-FfKvAxBe1ND1GenXA&s=09">@OWL_CAB</a>
        - تيك توك : <a href="https://www.tiktok.com/@owl.cab?_r=1&_t=ZS-91SE1Qyqi51">owl.cab</a>
        - يوتيوب : <a href="https://youtube.com/@owlcab_7?si=R1ujFOV2sqEBuDb5">owlcab_7</a>

        🚀 ابدأ تجربتك الآن واستكشف مميزات البوت بالكامل قبل انتهاء الفترة المجانية!

        نتمنى لك رحلة تداول ناجحة وخبرة تحليل متميزة معنا 🌟
        – فريق OWL CAB 🦉
        """,
        'commands_prompt': "يمكنك استخدام الأوامر التالية:",
        'subscribe_plans_prompt': '📦 اختر خطة الاشتراك:',
        'free_trial_activated': "🎉 لقد تم تفعيل التجربة المجانية الخاصة بك!\nرابط القناة: {channel_link}",
        'already_subscribed': "⚠️ أنت لديك اشتراك فعال بالفعل!",
        'payment_details_prompt': "💰 <b>تفاصيل الدفع:</b>\n"
                                  "⚠️  أرسل المبلغ ((بالضبط)) -وإلا قد تحدث مشاكل في عملية الدفع- إلى العنوان الموجود على الشبكة الطلوبة تحديداَ في الرابط أدناه\n"
                                  "🌐 الشبكة: {network}\n"
                                  "✅ سيتم تفعيل اشتراكك تلقائياً بعد التأكيد (1-10 دقائق)\n"
                                  "🔍للتحقق من حالة الدفع: /check_payment",
        'pay_now_button': "💳 ادفع الآن",
        'no_pending_payment': "لا توجد عملية دفع معلقة للتحقق منها.",
        'payment_details_not_found': "لم يتم العثور على تفاصيل الدفع المعلقة.",
        'payment_expired': "⏳ انتهت صلاحية عملية الدفع هذه (أكثر من 20 دقيقة).\nيرجى اختيار الاشتراك من جديد.",
        'payment_successful': "✅ تم تأكيد الدفع بنجاح! تم تفعيل الاشتراك. معرف الطلب: {order_id}, المدة: {duration}, رابط القناة: {channel_link}. (Payment confirmed successfully! Your subscription is now active. Order ID: {order_id}, Duration: {duration}, Channel Link: {channel_link}.)",   
        'payment_failed_cancelled': "❌ فشل أو إلغاء الدفع. يرجى المحاولة مرة أخرى. (Payment failed or cancelled. Please try again.)",
        'payment_pending': "⏳ لا تزال عملية الدفع معلقة. يرجى الانتظار قليلاً والمحاولة مرة أخرى.",
        'help_message': "أهلاً بك في بوت OWL CAB Subscriptions! إليك الأوامر التي يمكنك استخدامها:\n\n"
                        "/start - لبدء التفاعل مع البوت.\n"
                        "/subscribe - لاشتراك في خدمة OWL CAB.\n"
                        "/check_payment - للتحقق من حالة دفعك الأخير.\n"
                        "/help - لعرض هذه الرسالة المساعدة.\n",
        'choose_language': "الرجاء اختيار لغتك المفضلة:",
        'arabic_button': "🇸🇦 العربية",
        'english_button': "🇬🇧 English",
        'language_set_to': "تم تعيين اللغة إلى العربية.",
        'subscribe_command': 'subscribe',
        'check_payment_command': 'check_payment',
        'help_command': 'help',
        'one_day_trial': "1 يوم تجريبي مجانا ",
        'one_month_subscription': "1 شهر",
        'three_month_subscription': "3 أشهر",
        'six_month_subscription': "6 أشهر",
    },
    'en': {
        'welcome': """
🎉 Welcome to OWL CAB🦉 Subscription Bot!

😍 We are delighted to have you join the smart channel user group specialized in the crypto market to help you follow the crypto market with ease.
You can now get your first free trial, which allows you to:

Experience all exclusive features for a limited time without any commitment!

Follow the latest crypto market news from more than one reliable source📰.

AI analysis of news 🤖

📊 Receive advanced alerts and analyses for currencies and prices, and discover instant trading opportunities.

Direct links to currencies via the famous TradingView program🔗.

Important notes⚠️:

You can benefit from all services during the free trial period. Upon its expiration, you will be asked to subscribe to continue using the advanced features.

Each user gets only one free trial, after which you can choose the appropriate package for you.

(The bot displays information only and does not provide investment advice or guarantee profits or avoid losses. All trading and investment decisions are the sole responsibility of the user).

If you encounter any problem or inquiry, contact us via the account @Ws7h9.

Social Media Accounts of OWL CAB:
        - X (Previously known as Twitter) : <a href="https://x.com/OwlBot_72?t=vw5b-FfKvAxBe1ND1GenXA&s=09">@OWL_CAB</a>
        - TikTok : <a href="https://www.tiktok.com/@owl.cab?_r=1&_t=ZS-91SE1Qyqi51">owl.cab</a>
        - YouTube : <a href="https://youtube.com/@owlcab_7?si=R1ujFOV2sqEBuDb5">owlcab_7</a>

🚀 Start your experience now and explore the bot's full features before the free period ends!

We wish you a successful trading journey and an excellent analysis experience with us 🌟
– OWL CAB 🦉 Team
""",
        'commands_prompt': "You can use the following commands:",
        'subscribe_plans_prompt': '📦 Choose a subscription plan:',
        'free_trial_activated': "🎉 Your free trial has been activated!\nChannel Link: {channel_link}",
        'already_subscribed': "⚠️ You already have an active subscription!",
        'payment_details_prompt': "💰 <b>Payment Details:</b>\n"
                                  "⚠️ Send the amount ((exactly)) - otherwise, problems may occur in the payment process - to the address and network specified in the link below\n"
                                  "🌐 Network: {network}\n"
                                  "✅ Your subscription will be activated automatically after confirmation (1-10 minutes)\n"
                                  "🔍 To check payment status: /check_payment",
        'pay_now_button': "💳 Pay Now",
        'no_pending_payment': "No pending payment to check.",
        'payment_details_not_found': "Pending payment details not found.",
        'payment_expired': "⏳ This payment has expired (more than 20 minutes).\nPlease choose a subscription again.",
        'payment_successful': "✅ Payment confirmed successfully! Your subscription is now active. Order ID: {order_id}, Duration: {duration}, Channel Link: {channel_link}. (تم تأكيد الدفع بنجاح! تم تفعيل الاشتراك. معرف الطلب: {order_id}, المدة: {duration}, رابط القناة: {channel_link}.)",
        'payment_failed_cancelled': "❌ Payment failed or cancelled. Please try again. (فشل أو إلغاء الدفع. يرجى المحاولة مرة أخرى.)",
        'payment_pending': "⏳ Payment is still pending. Please wait a moment and try again.",
        'help_message': "Welcome to OWL CAB Subscriptions Bot! Here are the commands you can use:\n\n"
                        "/start - To start interacting with the bot.\n"
                        "/subscribe - To subscribe to the OWL CAB service.\n"
                        "/check_payment - To check the status of your last payment.\n"
                        "/help - To display this help message.\n",
        'choose_language': "Please choose your preferred language:",
        'arabic_button': "🇸🇦 العربية",
        'english_button': "🇬🇧 English",
        'language_set_to': "Language set to English.",
        'one_day_trial': "1 day - Free Trial",
        'one_month_subscription': "1 month - 1 Month Subscription",
        'three_month_subscription': "3 months - 3 Month Subscription",
        'six_month_subscription': "6 months - 6 Month Subscription",
        'subscribe_command': 'subscribe',
        'check_payment_command': 'check_payment',
        'help_command': 'help',
    }
}