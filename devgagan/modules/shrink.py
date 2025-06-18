 
# ---------------------------------------------------
# File Name: shrink.py
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

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import requests
import string
import aiohttp
from devgagan import app
from devgagan.core.func import *
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB, WEBSITE_URL, AD_API, LOG_GROUP  

tclient = AsyncIOMotorClient(MONGO_DB)
tdb = tclient["telegram_bot"]
token = tdb["tokens"]
 
 
async def create_ttl_index():
    await token.create_index("expires_at", expireAfterSeconds=0)
 
 
 
Param = {}
 
 
async def generate_random_param(length=8):
    """Generate a random parameter."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
 
 
async def get_shortened_url(deep_link):
    api_url = f"https://{WEBSITE_URL}/api?api={AD_API}&url={deep_link}"
 
     
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()   
                if data.get("status") == "success":
                    return data.get("shortenedUrl")
    return None
 
 
async def is_user_verified(user_id):
    """Check if a user has an active session."""
    session = await token.find_one({"user_id": user_id})
    return session is not None
 
 
@app.on_message(filters.command("start"))
async def token_handler(client, message):
    """Handle the /start command."""
    join = await subscribe(client, message)
    if join == 1:
        return

    chat_id = "save_restricted_content_bots"
    msg = await app.get_messages(chat_id, 796)
    user_id = message.chat.id

    if len(message.command) <= 1:
        image_url = "https://freeimage.host/i/F35exwP"  # must end with .jpg/.png etc.
        join_button = InlineKeyboardButton("Main Channel", url="https://t.me/II_LevelUP_II")
        premium = InlineKeyboardButton("💎 Premium Courses", url="https://t.me/+eJQiBsIpvrwxMTZl")
        keyboard = InlineKeyboardMarkup([
            [join_button],
            [premium]
        ])

        # Mention the user in the caption
        user_mention = message.from_user.mention if message.from_user else "User"

        await message.reply_photo(
            image_url,            
            caption=(
                f"👋 **Hello, {user_mention}! Welcome to Save Restricted Bot!**\n\n"
                "🔒 I help you **unlock and save content** from channels or groups that don't allow forwarding.\n\n"
                "📌 **How to use me:**\n"
                "➤ Just **send me the post link** if it's Public\n"
                "🔓 I'll fetch the media or message for you.\n\n"
                "🔐 **Private channel post?**\n"
                "➤ First do /login to save posts from Private Channel\n\n"
                "💡 Need help? Send /guide for more details also use /help\n\n"
                "⚡ Bot Made by CHOSEN ONE ⚝"
            ),
            reply_markup=keyboard,  # ✅ fixed here
            message_effect_id=5104841245755180586
        )
        return
 
    param = message.command[1] if len(message.command) > 1 else None
    freecheck = await chk_user(message, user_id)
    if freecheck != 1:
        await message.reply("You are a premium user no need of token 😉")
        return
 
     
    if param:
        if user_id in Param and Param[user_id] == param:
             
            await token.insert_one({
                "user_id": user_id,
                "param": param,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=3),
            })
            del Param[user_id]   
            await message.reply("✅ You have been verified successfully! Enjoy your session for next 3 hours.")
            return
        else:
            await message.reply("❌ Invalid or expired verification link. Please generate a new token.")
            return
 
