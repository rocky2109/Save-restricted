 
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
    """Handle the /start command and referral tracking."""
    join = await subscribe(client, message)
    if join == 1:
        return

    chat_id = "save_restricted_content_bots"
    msg = await app.get_messages(chat_id, 796)
    user_id = message.chat.id

    args = message.text.split()
    referrer_id = None

    # Check for referral param
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
        except:
            referrer_id = None

    user = await users.find_one({"_id": user_id})
    if not user:
        user_data = {
            "_id": user_id,
            "points": 0,
            "referrals": [],
            "joined_from": referrer_id
        }
        await users.insert_one(user_data)

        # Credit points to referrer
        if referrer_id and referrer_id != user_id:
            await users.update_one(
                {"_id": referrer_id},
                {
                    "$inc": {"points": 10},
                    "$addToSet": {"referrals": user_id}
                }
            )

    # Send welcome message
    if len(args) <= 1 or not args[1].startswith("token"):
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Main Channel", url="https://t.me/II_LevelUP_II")],
            [InlineKeyboardButton("💎 Premium Courses", url="https://t.me/+eJQiBsIpvrwxMTZl")]
        ])

        await message.reply_photo(
            msg.photo.file_id,
            caption=(
                "Hi 👋 Welcome!\n\n"
                "✳️ I can save posts from channels or groups where forwarding is off.\n"
                "✳️ Simply send the post link of a public channel.\n\n"
                "For private channels, do /login. Send /help to know more."
            ),
            reply_markup=reply_markup,
            message_effect_id=5104841245755180586
        )
        return

@app.on_message(filters.command("points"))
async def points_command(client, message):
    user_id = message.chat.id
    user = await users.find_one({"_id": user_id})
    if not user:
        return await message.reply("ℹ️ You have no points yet.")
    
    points = user.get("points", 0)
    total_refs = len(user.get("referrals", []))
    await message.reply(f"💰 You have {points} points.\n👥 Referrals: {total_refs} users")
 
@app.on_message(filters.command("refer"))
async def refer_command(client, message):
    user_id = message.chat.id
    bot_username = (await client.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await message.reply(f"🔗 Your referral link:\n{referral_link}\n\nShare this link to earn points!")


 
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
 
