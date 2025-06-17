# ---------------------------------------------------
# File Name: referral.py
# Description: Handles referral link sharing, stats, and buttons.
# Author: Criminal Cool & ChatGPT
# ---------------------------------------------------

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from devgagan import app
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB

# MongoDB setup
tclient = AsyncIOMotorClient(MONGO_DB)
tdb = tclient["telegram_bot"]
users = tdb["users"]

# 🔗 Helper: Generate referral link
async def get_referral_link(user_id, client):
    bot_username = (await client.get_me()).username
    return f"https://t.me/{bot_username}?start=ref_{user_id}"

# 🎁 /refer - Get your personal referral link
@app.on_message(filters.command("refer"))
async def refer_command(client, message):
    user_id = message.chat.id
    referral_link = await get_referral_link(user_id, client)

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Copy My Referral Link", url=referral_link)],
        [InlineKeyboardButton("👥 View My Stats", callback_data="view_referrals")]
    ])

    await message.reply_text(
        f"🎁 **Earn Rewards by Referring!**\n\n"
        f"✅ Get **10 points** for every new user who joins with your link!\n\n"
        f"`{referral_link}`",
        reply_markup=reply_markup
    )

# 💰 /points - Check your referral stats
@app.on_message(filters.command("points"))
async def points_command(client, message):
    user_id = message.chat.id
    user = await users.find_one({"_id": user_id})
    if not user:
        return await message.reply("⚠️ You haven't referred anyone yet.")

    points = user.get("points", 0)
    referrals = user.get("referrals", [])

    await message.reply_text(
        f"📊 **Referral Stats**\n\n"
        f"👥 Referrals: `{len(referrals)}`\n"
        f"💰 Points: `{points}`"
    )

# 📲 Callback: Get referral link (button)
@app.on_callback_query(filters.regex("get_referral_link"))
async def cb_ref_link(client, callback_query):
    user_id = callback_query.from_user.id
    ref_link = await get_referral_link(user_id, client)

    await callback_query.message.edit_text(
        f"🔗 **Your Referral Link**\n\n"
        f"`{ref_link}`\n\n"
        f"📢 Share this and earn **10 points** per verified join!"
    )

# 📊 Callback: View stats (button)
@app.on_callback_query(filters.regex("view_referrals"))
async def cb_ref_stats(client, callback_query):
    user_id = callback_query.from_user.id
    user = await users.find_one({"_id": user_id})
    points = user.get("points", 0)
    referrals = user.get("referrals", [])

    await callback_query.message.edit_text(
        f"💼 **Referral Stats**\n\n"
        f"👥 Total Referred: `{len(referrals)}`\n"
        f"💰 Total Points: `{points}`\n\n"
        f"🚀 Keep sharing to unlock more features!"
    )
