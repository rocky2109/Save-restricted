# ---------------------------------------------------
# File Name: stats.py
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



import time
import sys
import motor
from devgagan import app
from pyrogram import filters
from config import OWNER_ID
from devgagan.core.mongo.users_db import get_users, add_user, get_user
from devgagan.core.mongo.plans_db import premium_users
import asyncio
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType


start_time = time.time()

@app.on_message(group=10)
async def chat_watcher_func(_, message):
    try:
        if message.from_user:
            us_in_db = await get_user(message.from_user.id)
            if not us_in_db:
                await add_user(message.from_user.id)
    except:
        pass



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
    if tmp != "":
        if tmp.endswith(":"):
            return tmp[:-1]
        else:
            return tmp
    else:
        return "0 s"

SCHEDULE_TIME = datetime(2025, 6, 1, 11, 15)  # year, month, day, hour, minute

# 🎯 Function to send bot share message
async def send_share_button_to_owner():
    now = datetime.now()
    wait_seconds = (SCHEDULE_TIME - now).total_seconds()
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)

    bot = await app.get_me()
    bot_username = bot.username

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🤖 Share This Bot", switch_inline_query="")
    ]])

    await app.send_message(
        OWNER_ID,
        f"🚀 **Ready to share?**\n\nTap the button below to share @{bot_username} instantly!",
        reply_markup=reply_markup
    )

# 📩 Command to start scheduling manually
@app.on_message(filters.command("schedule_share") & filters.user(OWNER_ID))
async def schedule_share_command(client, message):
    asyncio.create_task(send_share_button_to_owner())
    await message.reply("✅ Share button will be sent to you at the scheduled time.")

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats(client, message):
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
  
