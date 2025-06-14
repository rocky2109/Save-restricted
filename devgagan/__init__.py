# ---------------------------------------------------
# File Name: __init__.py
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-06-14
# Version: 2.1.0
# License: MIT License
# ---------------------------------------------------

import asyncio
import logging
import os
import time

from pyrogram import Client
from pyrogram.enums import ParseMode
from telethon.sync import TelegramClient
from telethon.errors import FloodWaitError
from motor.motor_asyncio import AsyncIOMotorClient

from config import API_ID, API_HASH, BOT_TOKEN, STRING, MONGO_DB

# Logging setup
logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

botStartTime = time.time()

# Pyrogram bot client
app = Client(
    ":RestrictBot:",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50,
    parse_mode=ParseMode.MARKDOWN
)

# Pyrogram user session client (for string session use)
pro = Client("ggbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING)

# Safe Telethon setup with flood wait handling
sex = None
try:
    if not os.path.exists("sexrepo.session"):
        logging.info("Creating new Telethon session...")
        sex = TelegramClient('sexrepo', API_ID, API_HASH)
        sex.start(bot_token=BOT_TOKEN)
    else:
        logging.info("Using existing Telethon session...")
        sex = TelegramClient('sexrepo', API_ID, API_HASH).start()
except FloodWaitError as e:
    logging.error(f"FloodWaitError: Wait for {e.seconds} seconds before retrying.")
    sex = None

# MongoDB setup
tclient = AsyncIOMotorClient(MONGO_DB)
tdb = tclient["telegram_bot"]
token = tdb["tokens"]  # Your tokens collection

async def create_ttl_index():
    """Ensure the TTL index exists for the `tokens` collection."""
    await token.create_index("expires_at", expireAfterSeconds=0)

async def setup_database():
    await create_ttl_index()
    print("✅ MongoDB TTL index created.")

async def restrict_bot():
    global BOT_ID, BOT_NAME, BOT_USERNAME
    await setup_database()
    await app.start()

    getme = await app.get_me()
    BOT_ID = getme.id
    BOT_USERNAME = getme.username
    BOT_NAME = f"{getme.first_name} {getme.last_name}" if getme.last_name else getme.first_name

    if STRING:
        await pro.start()
    logging.info(f"🤖 Bot Started as @{BOT_USERNAME} (ID: {BOT_ID})")

# Run startup logic
loop = asyncio.get_event_loop()
loop.run_until_complete(restrict_bot())
