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


# 🔗 /sharelink command
@app.on_message(filters.command("sharelink"))
async def sharelink_handler(client, message: Message):
    bot = await client.get_me()
    bot_username = bot.username

    bot_link = f"https://t.me/{bot_username}?start=True"
    share_link = f"https://t.me/share/url?url={bot_link}&text=🚀%20Check%20out%20this%20awesome%20bot%20to%20unlock%20restricted%20Telegram%20media!%20Try%20now%20👉"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Open Bot", url=bot_link)],
        [InlineKeyboardButton("📤 Share with Friends", url=share_link)]
    ])

    await message.reply_text(
        f"✨ **Spread the Magic!**\n\n"
        f"Help others discover this bot that can save **restricted channel media**, even if forwarding is off! 🔒\n\n"
        f"Click a button below 👇 to open or share this bot with your friends!",
        reply_markup=reply_markup
    )

# ---------------------------------------------------

@app.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user(client, message):
    """Ban a user from using the bot"""
    if len(message.command) < 2:
        await message.reply("ℹ️ Usage: /ban <user_id> [reason] [days]\n\n"
                          "Example:\n"
                          "/ban 123456789 Spamming 7\n"
                          "/ban 123456789 Permanent ban")
        return

    try:
        user_id = int(message.command[1])
        reason = " ".join(message.command[2:-1]) if len(message.command) > 3 else message.command[2] if len(message.command) > 2 else "Violation of terms"
        days = int(message.command[-1]) if message.command[-1].isdigit() else 0

        if user_id in ADMINS:
            await message.reply("❌ Cannot ban an admin!")
            return

        if await UserDB.is_banned(user_id):
            await message.reply("⚠️ This user is already banned")
            return

        await UserDB.ban_user(
            user_id=user_id,
            admin_id=message.from_user.id,
            reason=reason,
            days=days
        )

        duration = f"for {days} days" if days > 0 else "permanently"
        response = (f"✅ User {user_id} has been banned {duration}.\n"
                   f"📝 Reason: {reason}\n\n"
                   f"🛡️ Banned by: {message.from_user.mention}")
        
        await message.reply(response)
        
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command("unban") & filters.user(ADMINS))
async def unban_user(client, message):
    """Unban a user"""
    if len(message.command) < 2:
        await message.reply("ℹ️ Usage: /unban <user_id>")
        return

    try:
        user_id = int(message.command[1])
        
        if not await UserDB.is_banned(user_id):
            await message.reply("ℹ️ This user is not currently banned")
            return

        await UserDB.unban_user(user_id)
        await message.reply(f"✅ User {user_id} has been unbanned successfully")

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@app.on_message(filters.command("baninfo") & filters.user(ADMINS))
async def ban_info(client, message):
    """Get ban information for a user"""
    if len(message.command) < 2:
        await message.reply("ℹ️ Usage: /baninfo <user_id>")
        return

    try:
        user_id = int(message.command[1])
        ban_info = await UserDB.get_ban_info(user_id)
        
        if not ban_info:
            await message.reply("ℹ️ This user has no active bans")
            return

        ban_date = ban_info['ban_date'].strftime("%Y-%m-%d %H:%M:%S")
        duration = f"{ban_info['days']} days" if ban_info['days'] > 0 else "Permanent"
        unban_date = ban_info['unban_date'].strftime("%Y-%m-%d %H:%M:%S") if ban_info.get('unban_date') else "Never"
        
        response = (f"🔨 Ban Information for User {user_id}:\n\n"
                   f"🛡️ Banned by: {ban_info['admin_id']}\n"
                   f"📅 Ban Date: {ban_date}\n"
                   f"⏳ Duration: {duration}\n"
                   f"📅 Unban Date: {unban_date}\n"
                   f"📝 Reason: {ban_info['reason']}")
        
        await message.reply(response)

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
