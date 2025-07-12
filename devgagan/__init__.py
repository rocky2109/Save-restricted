# ---------------------------------------------------
# File Name: __init__.py
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: Gagan
# ---------------------------------------------------

import asyncio
import logging
from pyrogram import Client
from pyrogram.enums import ParseMode
from config import API_ID, API_HASH, BOT_TOKEN, STRING, MONGO_DB
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from motor.motor_asyncio import AsyncIOMotorClient
import time
import os

loop = asyncio.get_event_loop()

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

botStartTime = time.time()

app = Client(
    ":RestrictBot:",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=50,
    parse_mode=ParseMode.MARKDOWN
)

pro = Client("ggbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING)

# Use a persistent Telethon session
telethon_client = TelegramClient("telethon_bot_session", API_ID, API_HASH)

# MongoDB setup
tclient = AsyncIOMotorClient(MONGO_DB)
tdb = tclient["telegram_bot"]
token = tdb["tokens"]

async def create_ttl_index():
    await token.create_index("expires_at", expireAfterSeconds=0)

async def setup_database():
    await create_ttl_index()
    print("MongoDB TTL index created.")

async def restrict_bot():
    global BOT_ID, BOT_NAME, BOT_USERNAME

    # Start Pyrogram bots
    await setup_database()
    await app.start()
    getme = await app.get_me()
    BOT_ID = getme.id
    BOT_USERNAME = getme.username
    BOT_NAME = f"{getme.first_name} {getme.last_name}" if getme.last_name else getme.first_name

    if STRING:
        await pro.start()

    # Start Telethon bot
    try:
        await telethon_client.start(bot_token=BOT_TOKEN)
        me = await telethon_client.get_me()
        logging.info(f"Telethon Bot Started as @{me.username}")
    except FloodWaitError as e:
        logging.warning(f"FloodWaitError: wait for {e.seconds} seconds before restarting Telethon client.")
    except Exception as e:
        logging.error(f"Error while starting Telethon client: {e}")

loop.run_until_complete(restrict_bot())
