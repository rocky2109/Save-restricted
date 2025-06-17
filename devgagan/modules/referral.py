
# ---------------------------------------------------
# File Name: referral.py
# Description: Handles user referrals, points, and invite link sharing.
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

# /start command patched for referral handling
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    user_id = message.chat.id
    args = message.text.split()
    referrer_id = None

    # Detect referral
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].replace("ref_", ""))
        except:
            pass

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

    # UI Response
    bot_username = (await client.get_me()).username
    mention = message.from_user.mention if message.from_user else "there"
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Earn More Points", callback_data="get_referral_link")],
        [InlineKeyboardButton("👥 My Referrals", callback_data="view_referrals")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]  # coming soon
    ])

    await message.reply_text(
        f"👋 Hello {mention}!

"
        "🎯 Earn 10 points for every friend you invite!
"
        "🧩 Use /refer to get your link or tap the buttons below.",
        reply_markup=reply_markup
    )

@app.on_message(filters.command("refer"))
async def refer_command(client, message):
    user_id = message.chat.id
    bot_username = (await client.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Copy My Referral Link", url=referral_link)],
        [InlineKeyboardButton("👥 View My Stats", callback_data="view_referrals")]
    ])

    await message.reply_text(
        f"🎁 Share this link with your friends and earn 10 points when they join!

`{referral_link}`",
        reply_markup=reply_markup
    )

@app.on_message(filters.command("points"))
async def points_command(client, message):
    user_id = message.chat.id
    user = await users.find_one({"_id": user_id})
    if not user:
        return await message.reply("⚠️ You haven't referred anyone yet.")

    points = user.get("points", 0)
    total_refs = len(user.get("referrals", []))
    await message.reply(
        f"💰 **Your Points:** `{points}`
"
        f"👥 **Referrals:** `{total_refs}` user(s)"
    )

@app.on_callback_query(filters.regex("get_referral_link"))
async def cb_ref_link(client, callback_query):
    user_id = callback_query.from_user.id
    bot_username = (await client.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await callback_query.message.edit_text(
        f"🔗 Your referral link:
`{ref_link}`

Share and earn 10 points for every verified join!"
    )

@app.on_callback_query(filters.regex("view_referrals"))
async def cb_ref_stats(client, callback_query):
    user_id = callback_query.from_user.id
    user = await users.find_one({"_id": user_id})
    points = user.get("points", 0)
    referrals = user.get("referrals", [])

    await callback_query.message.edit_text(
        f"💼 **Referral Stats**

"
        f"👥 Total Referred: `{len(referrals)}`
"
        f"💰 Total Points: `{points}`"
    )
