from motor.motor_asyncio import AsyncIOMotorClient as MongoCli
from config import MONGO_DB

mongo = MongoCli(MONGO_DB)
ref_db = mongo.referrals.ref_db

async def get_points(user_id: int) -> int:
    doc = await ref_db.find_one({"_id": user_id})
    return doc.get("points", 0) if doc else 0

async def add_points(user_id: int, amount: int = 1):
    await ref_db.update_one(
        {"_id": user_id},
        {"$inc": {"points": amount}},
        upsert=True
    )

async def mark_referred(user_id: int):
    await ref_db.update_one(
        {"_id": user_id},
        {"$set": {"referred": True}},
        upsert=True
    )

async def was_referred(user_id: int) -> bool:
    doc = await ref_db.find_one({"_id": user_id})
    return doc.get("referred", False) if doc else False

async def consume_points(user_id: int, required: int) -> bool:
    current = await get_points(user_id)
    if current >= required:
        await ref_db.update_one({"_id": user_id}, {"$inc": {"points": -required}})
        return True
    return False
