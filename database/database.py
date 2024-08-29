import motor.motor_asyncio
import time
from config import DB_URI, DB_NAME

#MONGO_DB_URL = 'your_mongodb_connection_string_here'
client = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]
users_collection = db['users']

async def add_user(user_id):
    user_data = {
        "_id": user_id,
        "limits": 10,  # Initial limit for the user
        "is_verified": False,
        "verified_time": None,
        "verify_token": None,
        "created_at": time.time()
    }
    await users_collection.insert_one(user_data)

async def present_user(user_id):
    user = await users_collection.find_one({"_id": user_id})
    return bool(user)

async def get_verify_status(user_id):
    user = await users_collection.find_one({"_id": user_id})
    if user:
        return {
            "is_verified": user.get("is_verified", False),
            "verified_time": user.get("verified_time"),
            "verify_token": user.get("verify_token"),
            "limits": user.get("limits", 0)
        }
    return None

async def update_verify_status(user_id, is_verified=None, verified_time=None, verify_token=None, limits=None):
    update_data = {}
    if is_verified is not None:
        update_data["is_verified"] = is_verified
    if verified_time is not None:
        update_data["verified_time"] = verified_time
    if verify_token is not None:
        update_data["verify_token"] = verify_token
    if limits is not None:
        update_data["limits"] = limits

    await users_collection.update_one({"_id": user_id}, {"$set": update_data})

async def decrement_user_limit(user_id):
    await users_collection.update_one({"_id": user_id}, {"$inc": {"limits": -1}})

async def get_user_limit(user_id):
    user = await users_collection.find_one({"_id": user_id})
    if user:
        return user.get("limits", 0)
    return 0

async def reset_user_limits(user_id, new_limit=10):
    await users_collection.update_one({"_id": user_id}, {"$set": {"limits": new_limit}})
