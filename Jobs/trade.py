from handlers import CHAT_ID

async def trade_job(context):
    if not CHAT_ID:
        return
    await context.bot.send_message(chat_id=CHAT_ID, text="🔄 تحديث التداول...")
