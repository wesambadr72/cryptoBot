import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram import Bot
from config import SUBS_BOT_TOKEN, CHANNEL_ID, CHANNEL_LINK
from setup_database import get_expired_subscribers, get_subscribers_about_to_expire, update_subscriber_status
from utils.logging import logger

bot = Bot(SUBS_BOT_TOKEN)

async def check_and_remove_expired_subscribers():
    logger.info("Starting check for expired subscribers...")
    expired_subscribers = get_expired_subscribers()
    if not expired_subscribers:
        logger.info("No expired subscribers found.")
        return

    for subscriber in expired_subscribers:
        user_id = subscriber[0]
        username = subscriber[1]
        try:
            # Attempt to remove user from channel
            await bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            logger.info(f"Successfully removed user {user_id} ({username}) from channel {CHANNEL_ID}.")
            # Update subscriber status in DB to inactive
            update_subscriber_status(user_id, 0) # 0 for inactive
            logger.info(f"Subscriber {user_id} status updated to inactive in DB.")
        except Exception as e:
            logger.error(f"Failed to remove user {user_id} ({username}) from channel {CHANNEL_LINK}: {e}")
            # If user is already not in channel or bot is not admin, update DB status anyway
            update_subscriber_status(user_id, 0)

    logger.info("Finished checking for expired subscribers.")

async def send_expiration_reminders():
    logger.info("Starting check for subscribers about to expire...")
    # Get subscribers whose subscription expires in 2 days
    subscribers_to_remind = get_subscribers_about_to_expire(days=2)

    if not subscribers_to_remind:
        logger.info("No subscribers found expiring in 2 days.")
        return

    for subscriber in subscribers_to_remind:
        user_id = subscriber[0]
        username = subscriber[1]
        expiration_date_str = subscriber[2] # This is a string from the DB
        try:
            # Convert string to datetime object for formatting
            expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d %H:%M:%S')
            await bot.send_message(
                chat_id=user_id,
                text=f"🔔 تذكير: اشتراكك في قناة OWL CAB سينتهي في {expiration_date.strftime('%Y-%m-%d')}!\nيرجى تجديد اشتراكك لتجنب انقطاع الخدمة."
            )
            logger.info(f"Sent expiration reminder to user {user_id} ({username}).")
        except Exception as e:
            logger.error(f"Failed to send expiration reminder to user {user_id} ({username}): {e}")

    logger.info("Finished sending expiration reminders.")