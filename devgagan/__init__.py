# ---------------------------------------------------
# File Name: __init__.py
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.5
# License: MIT License
# ---------------------------------------------------

import asyncio
import logging
import time
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.enums import ParseMode 
from config import API_ID, API_HASH, BOT_TOKEN, STRING, MONGO_DB, ADMINS
from telethon.sync import TelegramClient
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

# Global variables
botStartTime = time.time()
RESTART_INTERVAL = 300  # 5 minutes in seconds
restart_task = None

# Clients initialization
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

async def create_ttl_index():
    """Ensure the TTL index exists for the `tokens` collection."""
    await token.create_index("expires_at", expireAfterSeconds=0)

async def notify_admins_restart():
    """Send restart notification to all admins"""
    restart_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"♻️ **Bot Restarted**\n\n⏰ Time: `{restart_time}`\n🔄 Next restart in 5 minutes"
    
    for admin_id in ADMINS:
        try:
            await app.send_message(admin_id, message)
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {str(e)}")

async def restart_bot():
    """Restart the bot every 5 minutes"""
    while True:
        await asyncio.sleep(RESTART_INTERVAL)
        logging.info("Initiating scheduled restart...")
        
        try:
            await notify_admins_restart()
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

async def restrict_bot():
    """Main bot startup function"""
    global BOT_ID, BOT_NAME, BOT_USERNAME, restart_task
    
    await setup_database()
    await app.start()
    
    getme = await app.get_me()
    BOT_ID = getme.id
    BOT_USERNAME = getme.username
    BOT_NAME = getme.first_name + (" " + getme.last_name if getme.last_name else "")
    
    if STRING:
        await pro.start()
    
    # Send startup notification
    startup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for admin_id in ADMINS:
        try:
            await app.send_message(
                admin_id,
                f"🤖 **Bot Started Successfully**\n\n"
                f"🕒 Startup Time: `{startup_time}`\n"
                f"🔧 Version: `2.0.5`\n"
                f"🔄 Auto-restart every 5 minutes"
            )
        except Exception as e:
            logging.error(f"Failed to send startup notification: {str(e)}")
    
    # Start restart scheduler
    restart_task = asyncio.create_task(restart_bot())

async def setup_database():
    """Initialize database connections"""
    await create_ttl_index()
    logging.info("MongoDB TTL index created")

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
        if restart_task:
            restart_task.cancel()
        loop.run_until_complete(app.stop())
        if STRING:
            loop.run_until_complete(pro.stop())
        loop.run_until_complete(sex.disconnect())
        loop.close()
