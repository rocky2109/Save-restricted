# ---------------------------------------------------
# File Name: users_db.py
# Description: User management system with ban functionality
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-06-20
# Version: 2.1.0
# License: MIT License
# ---------------------------------------------------

from datetime import datetime, timedelta
from config import MONGO_DB
from motor.motor_asyncio import AsyncIOMotorClient as MongoCli

mongo = MongoCli(MONGO_DB)
db = mongo.users
users_collection = db.users_db
ban_collection = db.user_bans

class UserDB:
    @staticmethod
    async def get_users():
        """Get all active users"""
        return [user['user_id'] async for user in users_collection.find({"status": "active"})]

    @staticmethod
    async def get_user(user_id: int):
        """Check if user exists"""
        return await users_collection.find_one({"user_id": user_id})

    @staticmethod
    async def add_user(user_id: int):
        """Add new user with default settings"""
        if not await UserDB.get_user(user_id):
            await users_collection.insert_one({
                "user_id": user_id,
                "status": "active",
                "join_date": datetime.now(),
                "last_active": datetime.now(),
                "upload_count": 0
            })

    @staticmethod
    async def update_activity(user_id: int):
        """Update user's last active timestamp"""
        await users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()},
             "$inc": {"upload_count": 1}}
        )

    @staticmethod
    async def ban_user(
        user_id: int,
        admin_id: int,
        reason: str = "Violation of terms",
        days: int = 0
    ):
        """Ban user with optional temporary duration"""
        ban_data = {
            "user_id": user_id,
            "admin_id": admin_id,
            "reason": reason,
            "ban_date": datetime.now(),
            "days": days,
            "unban_date": datetime.now() + timedelta(days=days) if days else None,
            "is_active": True
        }
        await ban_collection.insert_one(ban_data)
        await users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"status": "banned"}}
        )

    @staticmethod
    async def unban_user(user_id: int):
        """Remove user ban"""
        await ban_collection.update_one(
            {"user_id": user_id, "is_active": True},
            {"$set": {"is_active": False}}
        )
        await users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"status": "active"}}
        )

    @staticmethod
    async def is_banned(user_id: int) -> bool:
        """Check if user is currently banned"""
        # Check for active bans
        active_ban = await ban_collection.find_one({
            "user_id": user_id,
            "is_active": True,
            "$or": [
                {"unban_date": None},
                {"unban_date": {"$gt": datetime.now()}}
            ]
        })
        
        # Auto-unban if temporary ban expired
        if active_ban and active_ban.get("unban_date"):
            if datetime.now() > active_ban["unban_date"]:
                await UserDB.unban_user(user_id)
                return False
                
        return bool(active_ban)

    @staticmethod
    async def get_ban_info(user_id: int):
        """Get detailed ban information"""
        return await ban_collection.find_one({
            "user_id": user_id,
            "is_active": True
        }, sort=[("ban_date", -1)])

    @staticmethod
    async def get_user_stats(user_id: int):
        """Get user statistics"""
        user = await users_collection.find_one({"user_id": user_id})
        if not user:
            return None
            
        ban_info = await UserDB.get_ban_info(user_id) if user.get("status") == "banned" else None
        
        return {
            "user_id": user_id,
            "status": user.get("status", "active"),
            "join_date": user.get("join_date"),
            "last_active": user.get("last_active"),
            "upload_count": user.get("upload_count", 0),
            "ban_info": ban_info
        }
