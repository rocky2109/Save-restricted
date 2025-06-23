# ---------------------------------------------------
# File Name: __init__.py
# Description: A Pyrogram bot with auto-restart functionality
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.6
# License: MIT License
# ---------------------------------------------------

import asyncio
import logging
import time
import os
import sys
from datetime import datetime
from pyrogram import Client
from pyrogram.enums import ParseMode
from config import API_ID, API_HASH, BOT_TOKEN, STRING, MONGO_DB
from telethon.sync import TelegramClient
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

# Constants
RESTART_INTERVAL = 300  # 5 minutes in seconds
botStartTime = time.time()

# Initialize clients
app = Client(
    ":RestrictBot:",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50,
    parse_mode=ParseMode.MARKDOWN
)

pro = Client("ggbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING)
sex = TelegramClient('sexrepo', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# MongoDB setup
tclient = AsyncIOMotorClient(MONGO_DB)
tdb = tclient["telegram_bot"]
token = tdb["tokens"]
users = tdb["users"]  # Collection to store user IDs

async def create_ttl_index():
    """Ensure the TTL index exists for the tokens collection."""
    await token.create_index("expires_at", expireAfterSeconds=0)

async def setup_database():
    """Initialize database connections and indexes."""
    await create_ttl_index()
    logging.info("MongoDB TTL index created.")

async def get_all_users():
    """Retrieve all user IDs from the database."""
    try:
        return await users.distinct("_id")
    except Exception as e:
        logging.error(f"Error fetching users: {str(e)}")
        return []

async def notify_users_restart():
    """Send restart notification to all users."""
    try:
        user_ids = await get_all_users()
        restart_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = (
            "♻️ **Bot Maintenance Notification**\n\n"
            f"🕒 Last Restart: `{restart_time}`\n"
            "⚙️ The bot has been automatically restarted for maintenance.\n"
            "🔧 All services are now back online!"
        )

        success = 0
        failures = 0

        for user_id in user_ids:
            try:
                await app.send_message(user_id, message)
                success += 1
                await asyncio.sleep(0.5)  # Rate limiting
            except Exception as e:
                failures += 1
                logging.error(f"Failed to notify user {user_id}: {str(e)}")

        logging.info(f"Restart notifications sent: {success} successful, {failures} failed")
    except Exception as e:
        logging.error(f"Notification system error: {str(e)}")

async def restart_sequence():
    """Perform the restart sequence with notifications."""
    logging.info("Initiating scheduled restart...")
    
    try:
        await notify_users_restart()
    except Exception as e:
        logging.error(f"Restart notification failed: {str(e)}")
    
    # Graceful shutdown
    try:
        await app.stop()
        if STRING:
            await pro.stop()
        await sex.disconnect()
    except Exception as e:
        logging.error(f"Error during shutdown: {str(e)}")
    
    # Restart process
    os.execv(sys.executable, [sys.executable] + sys.argv)

async def auto_restart_scheduler():
    """Schedule automatic restarts every 5 minutes."""
    while True:
        await asyncio.sleep(RESTART_INTERVAL)
        await restart_sequence()

async def restrict_bot():
    """Main bot startup function."""
    global BOT_ID, BOT_NAME, BOT_USERNAME
    
    await setup_database()
    await app.start()
    
    getme = await app.get_me()
    BOT_ID = getme.id
    BOT_USERNAME = getme.username
    BOT_NAME = getme.first_name + (" " + getme.last_name if getme.last_name else "")
    
    if STRING:
        await pro.start()
    
    # Start the auto-restart scheduler
    asyncio.create_task(auto_restart_scheduler())
    
    logging.info(f"Bot started successfully! Auto-restart scheduled every {RESTART_INTERVAL//60} minutes.")

# Main execution
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(restrict_bot())
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
    finally:
        loop.run_until_complete(app.stop())
        if STRING:
            loop.run_until_complete(pro.stop())
        loop.run_until_complete(sex.disconnect())
        loop.close()
