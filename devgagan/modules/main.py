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
from pyrogram import filters, Client
from devgagan import app
from config import API_ID, API_HASH, FREEMIUM_LIMIT, PREMIUM_LIMIT, OWNER_ID
from devgagan.core.get_func import get_msg
from devgagan.core.func import *
from devgagan.core.mongo import db
from pyrogram.errors import FloodWait
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import subprocess
from devgagan.modules.shrink import is_user_verified
async def generate_random_name(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))



users_loop = {}
interval_set = {}
batch_mode = {}

async def process_and_upload_link(userbot, user_id, msg_id, link, retry_count, message):
    try:
        await get_msg(userbot, user_id, msg_id, link, retry_count, message)
        await asyncio.sleep(15)
    finally:
        pass

# Function to check if the user can proceed
async def check_interval(user_id, freecheck):
    if freecheck != 1 or await is_user_verified(user_id):  # Premium or owner users can always proceed
        return True, None

    now = datetime.now()

    # Check if the user is on cooldown
    if user_id in interval_set:
        cooldown_end = interval_set[user_id]
        if now < cooldown_end:
            remaining_time = (cooldown_end - now).seconds
            return False, f"Please wait {remaining_time} seconds(s) before sending another link. Alternatively, purchase premium for instant access.\n\n> Hey 👋 You can use /token to use the bot free for 3 hours without any time limit."
        else:
            del interval_set[user_id]  # Cooldown expired, remove user from interval set

    return True, None

async def set_interval(user_id, interval_minutes=45):
    now = datetime.now()
    # Set the cooldown interval for the user
    interval_set[user_id] = now + timedelta(seconds=interval_minutes)
    

@app.on_message(
    filters.regex(r'https?://(?:www\.)?t\.me/[^\s]+|tg://openmessage\?user_id=\w+&message_id=\d+')
    & filters.private
)
async def single_link(_, message):
    user_id = message.chat.id

    # Check subscription and batch mode
    if await subscribe(_, message) == 1 or user_id in batch_mode:
        return

    # Check if user is already in a loop
    if users_loop.get(user_id, False):
        await message.reply(
            "You already have an ongoing process. Please wait for it to finish or cancel it with /cancel."
        )
        return

    # Check freemium limits
    if await chk_user(message, user_id) == 1 and FREEMIUM_LIMIT == 0 and user_id not in OWNER_ID and not await is_user_verified(user_id):
        await message.reply("Freemium service is currently not available. Upgrade to premium for access.")
        return

    # Check cooldown
    can_proceed, response_message = await check_interval(user_id, await chk_user(message, user_id))
    if not can_proceed:
        await message.reply(response_message)
        return

    # Add user to the loop
    users_loop[user_id] = True

    link = message.text if "tg://openmessage" in message.text else get_link(message.text)
    msg = await message.reply("Processing...")
    userbot = await initialize_userbot(user_id)

    try:
        if await is_normal_tg_link(link):
            # Pass userbot if available; handle normal Telegram links
            await process_and_upload_link(userbot, user_id, msg.id, link, 0, message)
            await set_interval(user_id, interval_minutes=45)
        else:
            # Handle special Telegram links
            await process_special_links(userbot, user_id, msg, link)
            
    except FloodWait as fw:
        await msg.edit_text(f'Try again after {fw.x} seconds due to floodwait from Telegram.')
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


async def initialize_userbot(user_id): # this ensure the single startup .. even if logged in or not
    """Initialize the userbot session for the given user."""
    data = await db.get_data(user_id)
    if data and data.get("session"):
        try:
            device = 'iPhone 16 Pro' # added gareebi text
            userbot = Client(
                "userbot",
                api_id=API_ID,
                api_hash=API_HASH,
                device_model=device,
                session_string=data.get("session")
            )
            await userbot.start()
            return userbot
        except Exception:
            return None
    return None


async def is_normal_tg_link(link: str) -> bool:
    """Check if the link is a standard Telegram link."""
    special_identifiers = ['t.me/+', 't.me/c/', 't.me/b/', 'tg://openmessage']
    return 't.me/' in link and not any(x in link for x in special_identifiers)
    
async def process_special_links(userbot, user_id, msg, link):
    """Handle special Telegram links."""
    if 't.me/+' in link:
        result = await userbot_join(userbot, link)
        await msg.edit_text(result)
    elif any(sub in link for sub in ['t.me/c/', 't.me/b/', '/s/', 'tg://openmessage']):
        await process_and_upload_link(userbot, user_id, msg.id, link, 0, msg)
        await set_interval(user_id, interval_minutes=45)
    else:
        await msg.edit_text("Invalid link format.")


@app.on_message(filters.command("batch") & filters.private)
async def batch_link(_, message):
    join = await subscribe(_, message)
    if join == 1:
        return
    user_id = message.chat.id
    
    # Check if batch process already running
    if users_loop.get(user_id, False):
        await message.reply(
            "⏳ You already have a batch process running.\n"
            "Please wait for it to complete before starting a new one."
        )
        return

    freecheck = await chk_user(message, user_id)
    if freecheck == 1 and FREEMIUM_LIMIT == 0 and user_id not in OWNER_ID and not await is_user_verified(user_id):
        await message.reply(
            "🚫 Freemium service is currently not available.\n"
            "Upgrade to premium for access:\n"
            "<code>/plan</code> to see premium options"
        )
        return

    max_batch_size = FREEMIUM_LIMIT if freecheck == 1 else PREMIUM_LIMIT

    # Start link input
    for attempt in range(3):
        start = await app.ask(
            message.chat.id,
            "🔗 <b>Please send the start link:</b>\n"
            "<i>(Max 3 attempts)</i>"
        )
        start_id = start.text.strip()
        s = start_id.split("/")[-1]
        if s.isdigit():
            cs = int(s)
            break
        await message.reply("❌ Invalid link format. Please send a valid Telegram message link.")
    else:
        await message.reply("⚠️ Maximum attempts exceeded. Please try again later.")
        return

    # Number of messages input
    for attempt in range(3):
        num_messages = await app.ask(
            message.chat.id,
            f"🔢 <b>How many messages to process?</b>\n"
            f"<i>(Max limit: {max_batch_size})</i>"
        )
        try:
            cl = int(num_messages.text.strip())
            if 1 <= cl <= max_batch_size:
                break
            raise ValueError()
        except ValueError:
            await message.reply(
                f"❌ Invalid number. Please enter between <b>1</b> and <b>{max_batch_size}</b>."
            )
    else:
        await message.reply("⚠️ Maximum attempts exceeded. Please try again later.")
        return

    # Validate interval
    can_proceed, response_message = await check_interval(user_id, freecheck)
    if not can_proceed:
        await message.reply(response_message)
        return
        
    join_button = InlineKeyboardButton("📢 Join Channel", url="https://t.me/team_spy_pro")
    keyboard = InlineKeyboardMarkup([[join_button]])
    
    pin_msg = await message.reply(
        f"⚡ <b>Batch Process Started</b>\n\n"
        f"▫️ Progress: <code>0/{cl}</code>\n"
        f"▫️ First ID: <code>{cs}</code>\n\n"
        f"<i>Powered by @CHOSEN_ONEx_bot</i>",
        reply_markup=keyboard
    )
    await pin_msg.pin(both_sides=True)

    users_loop[user_id] = True
    try:
        normal_links_handled = False
        userbot = await initialize_userbot(user_id)
        
        # Process normal links
        for i in range(cs, cs + cl):
            if not users_loop.get(user_id, False):
                break
                
            url = f"{'/'.join(start_id.split('/')[:-1])}/{i}"
            link = get_link(url)
            
            # Handle t.me links without userbot
            if 't.me/' in link and not any(x in link for x in ['t.me/b/', 't.me/c/', 'tg://openmessage']):
                msg = await message.reply(f"🔄 Processing message {i-cs+1}/{cl}...")
                await process_and_upload_link(userbot, user_id, msg.id, link, 0, message)
                await pin_msg.edit_text(
                    f"⚡ <b>Batch Process Running</b>\n\n"
                    f"▫️ Progress: <code>{i-cs+1}/{cl}</code>\n"
                    f"▫️ Current ID: <code>{i}</code>\n\n"
                    f"<i>Powered by @CHOSEN_ONEx_bot</i>",
                    reply_markup=keyboard
                )
                normal_links_handled = True

        if normal_links_handled:
            await set_interval(user_id, interval_minutes=300)
            await pin_msg.edit_text(
                f"✅ <b>Batch Completed Successfully</b>\n\n"
                f"▫️ Total Processed: <code>{cl}</code>\n"
                f"▫️ First ID: <code>{cs}</code>\n"
                f"▫️ Last ID: <code>{cs+cl-1}</code>\n\n"
                f"<i>Powered by @CHOSEN_ONEx_bot</i>",
                reply_markup=keyboard
            )
            await send_completion_message(message, cl)
            return
            
        # Process special links with userbot
        for i in range(cs, cs + cl):
            if not users_loop.get(user_id, False):
                break
                
            if not userbot:
                await message.reply("🔒 Please login to the bot first using /login")
                users_loop[user_id] = False
                return
                
            url = f"{'/'.join(start_id.split('/')[:-1])}/{i}"
            link = get_link(url)
            
            if any(x in link for x in ['t.me/b/', 't.me/c/']):
                msg = await message.reply(f"🔄 Processing message {i-cs+1}/{cl}...")
                await process_and_upload_link(userbot, user_id, msg.id, link, 0, message)
                await pin_msg.edit_text(
                    f"⚡ <b>Batch Process Running</b>\n\n"
                    f"▫️ Progress: <code>{i-cs+1}/{cl}</code>\n"
                    f"▫️ Current ID: <code>{i}</code>\n\n"
                    f"<i>Powered by @CHOSEN_ONEx_bot</i>",
                    reply_markup=keyboard
                )

        await set_interval(user_id, interval_minutes=300)
        await pin_msg.edit_text(
            f"✅ <b>Batch Completed Successfully</b>\n\n"
            f"▫️ Total Processed: <code>{cl}</code>\n"
            f"▫️ First ID: <code>{cs}</code>\n"
            f"▫️ Last ID: <code>{cs+cl-1}</code>\n\n"
            f"<i>Powered by @CHOSEN_ONEx_bot</i>",
            reply_markup=keyboard
        )
        await send_completion_message(message, cl)

    except Exception as e:
        await message.reply(f"❌ Error occurred:\n<code>{str(e)}</code>")
        logging.error(f"Batch error for {user_id}: {str(e)}")
    finally:
        users_loop.pop(user_id, None)
        try:
            await pin_msg.unpin()
        except:
            pass

async def send_completion_message(message, count):
    bot = await app.get_me()
    share_link = f"https://t.me/share/url?url=https://t.me/{bot.username}?start=true"
    
    share_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌟 Share Bot", url=share_link)],
        [InlineKeyboardButton("💎 Upgrade", callback_data="premium")]
    ])

    await message.reply(
        f"🎉 <b>Batch of {count} messages completed!</b>\n\n"
        "Share this bot with your friends or upgrade for more features:",
        reply_markup=share_keyboard
    )

@app.on_message(filters.command("cancel"))
async def stop_batch(_, message):
    user_id = message.chat.id

    # Check if there is an active batch process for the user
    if user_id in users_loop and users_loop[user_id]:
        users_loop[user_id] = False  # Set the loop status to False
        await app.send_message(
            message.chat.id, 
            "Batch processing has been stopped successfully. You can start a new batch now if you want."
        )
    elif user_id in users_loop and not users_loop[user_id]:
        await app.send_message(
            message.chat.id, 
            "The batch process was already stopped. No active batch to cancel."
        )
    else:
        await app.send_message(
            message.chat.id, 
            "No active batch processing is running to cancel."
        )
