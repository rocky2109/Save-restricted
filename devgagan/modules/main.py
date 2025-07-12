# ---------------------------------------------------
# File Name: main.py
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
# More readable 
# ---------------------------------------------------

import time
import random
import string
import asyncio
import subprocess
from datetime import datetime, timedelta

from pyrogram import filters, Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from devgagan import app
from config import API_ID, API_HASH, FREEMIUM_LIMIT, PREMIUM_LIMIT, OWNER_ID
from devgagan.core.get_func import get_msg
from devgagan.core.func import *
from devgagan.core.mongo import db
from devgagan.modules.shrink import is_user_verified
from devgagan.core.mongo.referral_db import get_points, consume_points
from devgagan.core.mongo.plans_db import add_premium

users_loop = {}
interval_set = {}
batch_mode = {}

async def generate_random_name(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

async def check_interval(user_id, freecheck):
    now = datetime.now()
    if user_id in interval_set:
        cooldown_end = interval_set[user_id]
        if now < cooldown_end:
            remaining_time = (cooldown_end - now).seconds
            return False, f"⏳ Please wait {remaining_time} seconds before sending another link. You can also use /token for free 3-hour premium access."
        else:
            del interval_set[user_id]
    return True, None

async def set_interval(user_id, interval_minutes=45):
    now = datetime.now()
    interval_set[user_id] = now + timedelta(seconds=interval_minutes)

async def initialize_userbot(user_id):
    data = await db.get_data(user_id)
    if data and "session" in data:
        try:
            device = 'iPhone 16 Pro'
            userbot = Client(
                "userbot",
                api_id=API_ID,
                api_hash=API_HASH,
                device_model=device,
                session_string=data["session"]
            )
            await userbot.start()
            return userbot
        except Exception:
            return None
    return None

async def is_normal_tg_link(link: str) -> bool:
    special_identifiers = ['t.me/+', 't.me/c/', 't.me/b/', 'tg://openmessage']
    return 't.me/' in link and not any(x in link for x in special_identifiers)

async def process_special_links(userbot, user_id, msg, link):
    if 't.me/+' in link:
        result = await userbot_join(userbot, link)
        await msg.edit_text(result)
    elif any(sub in link for sub in ['t.me/c/', 't.me/b/', '/s/', 'tg://openmessage']):
        await process_and_upload_link(userbot, user_id, msg.id, link, 0, msg)
        await set_interval(user_id, interval_minutes=45)
    else:
        await msg.edit_text("Invalid link format.")

async def process_and_upload_link(userbot, user_id, msg_id, link, retry_count, message):
    try:
        await get_msg(userbot, user_id, msg_id, link, retry_count, message)
        await asyncio.sleep(15)
    finally:
        pass

@app.on_message(
    filters.regex(r'https?://(?:www\.)?t\.me/[^\s]+|tg://openmessage\?user_id=\w+&message_id=\d+')
    & filters.private
)
async def single_link(_, message):
    user_id = message.chat.id

    if await subscribe(_, message) == 1 or user_id in batch_mode:
        return

    if users_loop.get(user_id, False):
        await message.reply("You already have an ongoing process. Use /cancel to stop it.")
        return

    freecheck = await chk_user(message, user_id)

    if freecheck == 1 and FREEMIUM_LIMIT == 0 and user_id not in OWNER_ID and not await is_user_verified(user_id):
        await message.reply("Freemium service is not available. Please upgrade to premium.")
        return

    can_proceed, response_message = await check_interval(user_id, freecheck)
    if not can_proceed:
        await message.reply(response_message)
        return

    users_loop[user_id] = True

    link = message.text if "tg://openmessage" in message.text else get_link(message.text)
    msg = await message.reply("Processing...")
    userbot = await initialize_userbot(user_id)

    try:
        if await is_normal_tg_link(link):
            await process_and_upload_link(userbot, user_id, msg.id, link, 0, message)
            await set_interval(user_id, interval_minutes=45)
        else:
            await process_special_links(userbot, user_id, msg, link)

    except FloodWait as fw:
        await msg.edit_text(f'Try again after {fw.x} seconds due to Telegram flood control.')
    except Exception as e:
        await msg.edit_text(f"Link: `{link}`\n\n**Error:** {str(e)}")
    finally:
        users_loop[user_id] = False
        if userbot:
            await userbot.stop()
        try:
            await msg.delete()
        except Exception:
            pass

@app.on_message(filters.command("mypoints") & filters.private)
async def mypoints_cmd(_, message):
    points = await get_points(message.from_user.id)
    days = points // 10
    await message.reply_text(
        f"📊 You have **{points} referral point(s)**.\n"
        f"🔓 That gives you: **{days} day(s)** premium access.\n"
        f"💡 Use /batch to activate if you have 10+ points."
    )

@app.on_message(filters.command("batch") & filters.private)
async def batch_link(_, message):
    join = await subscribe(_, message)
    if join == 1:
        return

    user_id = message.chat.id
    if users_loop.get(user_id, False):
        await app.send_message(user_id, "You already have a batch process running.")
        return

    freecheck = await chk_user(message, user_id)
    if freecheck == 1 and not await is_user_verified(user_id):
        points = await get_points(user_id)
        if points < 10:
            bot_username = (await app.get_me()).username
            ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
            share_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("📣 Share & Earn", url=f"https://t.me/share/url?url={ref_link}&text=🚀 Try this awesome bot!")],
            ])
            await message.reply_text(
                f"🚫 You need at least **10 referral points** to use /batch.\n\n"
                f"📎 Referral Link: `{ref_link}`\n"
                f"🪙 10 points = 1 day premium.\n"
                f"🔍 Use /mypoints to check your points.",
                reply_markup=share_button
            )
            return

        granted = await consume_points(user_id, 10)
        if granted:
            expire_time = datetime.utcnow() + timedelta(days=1)
            await add_premium(user_id, expire_time)
            await message.reply("🎉 1-day premium granted using 10 points!")
        else:
            await message.reply("⚠️ Could not grant premium. Try again.")
            return

    max_batch_size = FREEMIUM_LIMIT if freecheck == 1 else PREMIUM_LIMIT

    for attempt in range(3):
        await app.send_photo(
            user_id,
            photo="https://i.postimg.cc/BXkchVpY/image.jpg",
            caption="Just send the link where I should start...\n\nजहाँ से शुरू करना है उस पोस्ट का लिंक भेजो"
        )
        start = await app.ask(user_id, "🎯 Send start post link:\n> You have 3 tries.")
        start_id = start.text.strip()
        s = start_id.split("/")[-1]
        if s.isdigit():
            cs = int(s)
            break
        await app.send_message(user_id, "Invalid link. Try again.")
    else:
        await app.send_message(user_id, "Maximum attempts exceeded.")
        return

    for attempt in range(3):
        num_messages = await app.ask(user_id, f"How many messages? Max {max_batch_size}")
        try:
            cl = int(num_messages.text.strip())
            if 1 <= cl <= max_batch_size:
                break
        except:
            pass
        await app.send_message(user_id, f"Enter a valid number (1-{max_batch_size})")
    else:
        await app.send_message(user_id, "Maximum attempts exceeded.")
        return

    can_proceed, response_message = await check_interval(user_id, freecheck)
    if not can_proceed:
        await message.reply(response_message)
        return

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Join Channel", url="https://t.me/II_Way_to_Success_II")]])
    pin_msg = await app.send_message(
        user_id,
        f"Batch started ⚡ Processing: 0/{cl}\n\n**Powered by CHOSEN ONE ⚝**",
        reply_markup=keyboard
    )
    try:
        await pin_msg.pin(both_sides=True)
    except:
        pass

    users_loop[user_id] = True
    userbot = await initialize_userbot(user_id)

    try:
        for i in range(cs, cs + cl):
            if users_loop[user_id]:
                url = f"{'/'.join(start_id.split('/')[:-1])}/{i}"
                link = get_link(url)
                msg = await app.send_message(user_id, "Processing...")
                await process_and_upload_link(userbot, user_id, msg.id, link, 0, message)
                await pin_msg.edit_text(
                    f"Batch started ⚡ Processing: {i - cs + 1}/{cl}\n\n**__Powered by CHOSEN ONE ⚝__**",
                    reply_markup=keyboard
                )

        await set_interval(user_id, interval_minutes=300)
        await pin_msg.edit_text(
            f"Batch completed ✅ {cl} messages processed.\n\n**__Powered by CHOSEN ONE ⚝__**",
            reply_markup=keyboard
        )
        await app.send_message(user_id, "😘 𝗖ꪮ𝗺𝗽𝗹𝗲𝘁𝗲 𝗛ꪮ 𝗚𝗮𝘆𝗮 𝗕ꪮ$$ 😎")

    except Exception as e:
        await app.send_message(user_id, f"Error: {e}")
    finally:
        users_loop.pop(user_id, None)
        if userbot:
            await userbot.stop()

@app.on_message(filters.command("cancel"))
async def stop_batch(_, message):
    user_id = message.chat.id
    if user_id in users_loop and users_loop[user_id]:
        users_loop[user_id] = False
        await app.send_message(user_id, "Batch stopped. You can start a new /batch now.")
    elif user_id in users_loop:
        await app.send_message(user_id, "Batch was already stopped. You can start a new /batch.")
    else:
        await app.send_message(user_id, "No batch process is running.")

@app.on_message(filters.command("sharelink"))
async def sharelink_handler(client, message: Message):
    bot = await client.get_me()
    bot_username = bot.username
    bot_link = f"https://t.me/{bot_username}?start=True"
    share_link = f"https://t.me/share/url?url={bot_link}&text=🚀 Check this awesome Telegram media saver bot!"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Share Me With Others 🫠", url=share_link)]
    ])

    await message.reply_text(
        f"✨ **Spread the Magic!**\n\n"
        f"Help others discover this bot that can save restricted channel media, even if forwarding is off! 🔒\n\n"
        f"Click below 👇 to share it!",
        reply_markup=reply_markup
    )
