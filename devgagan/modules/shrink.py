 
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
users = tdb["users"]  # 👈 This is required for referral system

 
 
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
    """Handle the /start command and referral tracking."""
    join = await subscribe(client, message)
    if join == 1:
        return

    chat_id = "save_restricted_content_bots"
    msg = await app.get_messages(chat_id, 796)
    user_id = message.chat.id

    args = message.text.split()
    referrer_id = None

    # 🔗 Check if user joined using a referral link
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
        except:
            referrer_id = None

    # 👤 Check if new user
    user = await users.find_one({"_id": user_id})
    if not user:
        user_data = {
            "_id": user_id,
            "points": 0,
            "referrals": [],
            "joined_from": referrer_id
        }
        await users.insert_one(user_data)

        # 💰 Reward referrer
        if referrer_id and referrer_id != user_id:
            await users.update_one(
                {"_id": referrer_id},
                {
                    "$inc": {"points": 10},
                    "$addToSet": {"referrals": user_id}
                }
            )

    # 📩 Send intro message
    user_mention = message.from_user.mention if message.from_user else "User"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Main Channel", url="https://t.me/II_LevelUP_II")],
        [InlineKeyboardButton("💎 Premium Courses", url="https://t.me/+eJQiBsIpvrwxMTZl")]
    ])

    await message.reply_photo(
        "https://freeimage.host/i/F35exwP",
        caption=(
            f"👋 **Hello, {user_mention}! Welcome to Save Restricted Bot!**\n\n"
            "🔒 I help you **unlock and save content** from channels or groups that don't allow forwarding.\n\n"
            "📌 **How to use me:**\n"
            "➤ Just **send me the post link** if it's Public\n"
            "🔓 I'll fetch the media or message for you.\n\n"
            "🔐 **Private channel post?**\n"
            "➤ First do /login to save posts from Private Channel\n\n"
            "🎯 Use /refer to invite & earn points\n"
            "💰 Use /points to check your earnings\n"
            "⚡ Made by CHOSEN ONE ⚝"
        ),
        reply_markup=reply_markup,
        message_effect_id=5104841245755180586
    )

@app.on_message(filters.command("refer"))
async def refer_command(client, message):
    user_id = message.chat.id
    bot_username = (await client.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await message.reply(f"🔗 Your referral link:\n\n`{referral_link}`\n\nInvite friends and earn 10 points per join!")

@app.on_message(filters.command("points"))
async def points_command(client, message):
    user_id = message.chat.id
    user = await users.find_one({"_id": user_id})
    if not user:
        return await message.reply("ℹ️ You have no referral data yet.")

    points = user.get("points", 0)
    total_refs = len(user.get("referrals", []))
    await message.reply(f"💰 You have `{points}` points.\n👥 Referrals: `{total_refs}` users.")


@app.on_message(filters.command("token"))
async def smart_handler(client, message):
    user_id = message.chat.id
     
    freecheck = await chk_user(message, user_id)
    if freecheck != 1:
        await message.reply("You are a premium user no need of token 😉")
        return
    if await is_user_verified(user_id):
        await message.reply("✅ Your free session is already active enjoy!")
    else:
         
        param = await generate_random_param()
        Param[user_id] = param   
 
         
        deep_link = f"https://t.me/{client.me.username}?start={param}"
 
         
        shortened_url = await get_shortened_url(deep_link)
        if not shortened_url:
            await message.reply("❌ Failed to generate the token link. Please try again.")
            return
 
         
        button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Verify the token now...", url=shortened_url)]]
        )
        await message.reply("Click the button below to verify your free access token: \n\n> What will you get ? \n1. No time bound upto 3 hours \n2. Batch command limit will be FreeLimit + 20 \n3. All functions unlocked", reply_markup=button)
 
