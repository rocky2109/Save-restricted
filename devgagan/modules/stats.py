# ---------------------------------------------------
# File Name: stats.py
# Description: Handles statistics, share commands, user tracking
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-06-17
# Version: 2.0.6
# License: MIT License
# ---------------------------------------------------

import time
import sys
import asyncio
from datetime import datetime, timedelta
import motor

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from devgagan import app
from config import OWNER_ID
from devgagan.core.mongo.users_db import get_users, add_user, get_user
from devgagan.core.mongo.plans_db import premium_users


start_time = time.time()


# ⏱️ Format uptime
def time_formatter():
    minutes, seconds = divmod(int(time.time() - start_time), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)
    tmp = (
        ((str(weeks) + "w:") if weeks else "")
        + ((str(days) + "d:") if days else "")
        + ((str(hours) + "h:") if hours else "")
        + ((str(minutes) + "m:") if minutes else "")
        + ((str(seconds) + "s") if seconds else "")
    )
    if tmp.endswith(":"):
        return tmp[:-1]
    return tmp or "0s"


# 👁️ Track every user who uses the bot
@app.on_message(group=10)
async def chat_watcher_func(_, message: Message):
    try:
        if message.from_user:
            us_in_db = await get_user(message.from_user.id)
            if not us_in_db:
                await add_user(message.from_user.id)
    except:
        pass


# 📊 /stats command
@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats(client, message: Message):
    start = time.time()
    users = len(await get_users())
    premium = await premium_users()
    ping = round((time.time() - start) * 1000)

    await message.reply_text(f"""
**Stats of** {(await client.get_me()).mention} :

🏓 **Ping Pong**: {ping}ms
📊 **Total Users** : `{users}`
📈 **Premium Users** : `{len(premium)}`
⚙️ **Bot Uptime** : `{time_formatter()}`
🎨 **Python Version**: `{sys.version.split()[0]}`
📑 **Mongo Version**: `{motor.version}`
""")


