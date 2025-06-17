# ---------------------------------------------------
# File Name: referral.py
# Description: Handles referral tracking on start param + points & stats.
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

# 🎯 Background: Detect & register referrals ONLY if /start ref_12345678
@app.on_message(filters.command("start"))
async def referral_start_tracker(client, message):
    args = message.text.split()
    if len(args) < 2 or not args[1].startswith("ref_"):
        return  # Let your main /start handler handle it

    user_id = message.chat.id
    try:
        referrer_id = int(args[1].replace("ref_", ""))
    except ValueError:
        return

    # Only process if user is new
    user = await users.find_one({"_id": user_id})
    if not user:
        await users.insert_one({
            "_id": user_id,
            "points": 0,
            "referrals": [],
            "joined_from": referrer_id
        })

        if referrer_id and referrer_id != user_id:
            await users.update_one(
                {"_id": referrer_id},
                {"$inc": {"points": 10}, "$addToSet": {"referrals": user_id}}
            )
            await message.reply_text("🎉 You joined using a referral! Your friend earned 10 points!")

# 🔗 Referral link command
@app.on_message(filters.command("refer"))
async def refer_command(client, message):
    user_id = message.chat.id
    bot_username = (await client.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Copy My Referral Link", url=ref_link)],
        [InlineKeyboardButton("👥 View My Stats", callback_data="view_referrals")]
    ])

    await message.reply_text(
        f"🎁 **Earn Rewards by Referring!**\n\n"
        f"✅ Get **10 points** per new user!\n"
        f"`{ref_link}`",
        reply_markup=keyboard
    )

# 💰 Points viewer
@app.on_message(filters.command("points"))
async def points_command(client, message):
    user_id = message.chat.id
    user = await users.find_one({"_id": user_id})
    if not user:
        return await message.reply("⚠️ You haven't referred anyone yet.")

    total_refs = len(user.get("referrals", []))
    points = user.get("points", 0)

    await message.reply_text(
        f"📊 **Referral Stats**\n\n"
        f"👥 Referrals: `{total_refs}`\n"
        f"💰 Points: `{points}`"
    )

# Button callback: get link
@app.on_callback_query(filters.regex("get_referral_link"))
async def cb_ref_link(client, callback_query):
    user_id = callback_query.from_user.id
    bot_username = (await client.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await callback_query.message.edit_text(
        f"🔗 **Your Referral Link**\n`{ref_link}`\nShare & earn 10 points!"
    )

# Button callback: view stats
@app.on_callback_query(filters.regex("view_referrals"))
async def cb_view_referrals(client, callback_query):
    user_id = callback_query.from_user.id
    user = await users.find_one({"_id": user_id})
    points = user.get("points", 0)
    total_refs = len(user.get("referrals", []))

    await callback_query.message.edit_text(
        f"💼 **Referral Stats**\n\n"
        f"👥 Total Referred: `{total_refs}`\n"
        f"💰 Total Points: `{points}`"
    )
