# ---------------------------------------------------
# File Name: __init__.py
# Description: Auto-restarting Telegram bot
# Author: Gagan + Modified
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# ---------------------------------------------------

import asyncio
import logging
import os
import sys
import time
from pyrogram import Client
from pyrogram.enums import ParseMode
from config import API_ID, API_HASH, BOT_TOKEN, STRING, MONGO_DB
from telethon.sync import TelegramClient
from motor.motor_asyncio import AsyncIOMotorClient

# Logging setup
logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

loop = asyncio.get_event_loop()
botStartTime = time.time()

# Pyrogram Bot Client
app = Client(
    ":RestrictBot:",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50,
    parse_mode=ParseMode.MARKDOWN
)

# Optional StringSession Client
pro = Client("ggbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING)

# Telethon Client (if needed)
sex = TelegramClient('sexrepo', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# MongoDB Setup
tclient = AsyncIOMotorClient(MONGO_DB)
tdb = tclient["telegram_bot"]
token = tdb["tokens"]
users = tdb["users"]  # users collection to store & notify

# TTL index for expiring tokens
async def create_ttl_index():
    await token.create_index("expires_at", expireAfterSeconds=0)

# Broadcast restart message to all users
async def broadcast_restart():
    logging.info("🔄 Sending restart notice to users...")
    async for user in users.find():
        try:
            await app.send_message(
                chat_id=int(user["id"]),
                text="🔄 Bot restarted. I'm back online!"
            )
        except Exception as e:
            logging.warning(f"❌ Couldn't message {user['id']}: {e}")

# Auto-restart every 5 minutes
async def schedule_restart():
    await asyncio.sleep(300)  # wait 5 minutes before first restart
    await broadcast_restart()
    logging.info("♻️ Restarting bot now...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# Full startup logic
async def restrict_bot():
    global BOT_ID, BOT_NAME, BOT_USERNAME

    await create_ttl_index()
    await app.start()

    me = await app.get_me()
    BOT_ID = me.id
    BOT_USERNAME = me.username
    BOT_NAME = f"{me.first_name} {me.last_name}" if me.last_name else me.first_name

    if STRING:
        await pro.start()

    logging.info(f"🤖 Bot Started: {BOT_NAME} [@{BOT_USERNAME}]")

    # ⏱ Schedule auto-restart
    asyncio.create_task(schedule_restart())

# Run it all
loop.run_until_complete(restrict_bot())
