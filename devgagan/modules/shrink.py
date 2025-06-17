 
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
    """Handle the /start command including referral & token logic."""
    join = await subscribe(client, message)
    if join == 1:
        return

    user_id = message.chat.id
    args = message.text.split()
    param = args[1] if len(args) > 1 else None
    joined_from_referral = False

    # 📌 MongoDB setup
    from motor.motor_asyncio import AsyncIOMotorClient
    from config import MONGO_DB
    tclient = AsyncIOMotorClient(MONGO_DB)
    users = tclient["telegram_bot"]["users"]

    # 🧩 Handle referral links like /start ref_12345678
    if param and param.startswith("ref_"):
        try:
            referrer_id = int(param.replace("ref_", ""))
            user = await users.find_one({"_id": user_id})

            # ✅ If new user: track referral
            if not user:
                await users.insert_one({
                    "_id": user_id,
                    "points": 0,
                    "referrals": [],
                    "joined_from": referrer_id
                })
                joined_from_referral = True

                if referrer_id != user_id:
                    await users.update_one(
                        {"_id": referrer_id},
                        {"$inc": {"points": 10}, "$addToSet": {"referrals": user_id}}
                    )

            # ✅ If existing user without referral info
            elif not user.get("joined_from") and referrer_id != user_id:
                joined_from_referral = True
                await users.update_one({"_id": user_id}, {"$set": {"joined_from": referrer_id}})
                await users.update_one(
                    {"_id": referrer_id},
                    {"$inc": {"points": 10}, "$addToSet": {"referrals": user_id}}
                )
        except Exception as e:
            print(f"Referral processing error: {e}")

    # 📸 Show welcome message
    if not param or (param and param.startswith("ref_")):
        image_url = "https://freeimage.host/i/F35exwP"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Main Channel", url="https://t.me/II_LevelUP_II")],
            [InlineKeyboardButton("💎 Premium Courses", url="https://t.me/+eJQiBsIpvrwxMTZl")]
        ])
        user_mention = message.from_user.mention or "User"

        # ✅ Add referral notice if joined via referral
        referral_notice = (
            "🎉 You joined using a referral! Your friend earned 10 points.\n\n"
            if joined_from_referral else ""
        )

        await message.reply_photo(
            image_url,
            caption=(
                f"{referral_notice}"
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
            reply_markup=keyboard
        )
        return

    # 🔐 Handle token verification
    freecheck = await chk_user(message, user_id)
    if freecheck != 1:
        await message.reply("You are a premium user no need of token 😉")
        return

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

    await message.reply("❌ Invalid or expired verification link. Please generate a new token.")
