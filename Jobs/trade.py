async def trade_job(context):
    chat_id = context.bot_data.get('chat_id')
    if not chat_id:
        return
    await context.bot.send_message(chat_id=chat_id, text="🔄 تحديث التداول...")
