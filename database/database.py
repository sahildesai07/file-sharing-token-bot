
from config import DB_URI, DB_NAME
from pymongo import MongoClient

client = MongoClient(DB_URI)
db = client[DB_NAME]
users = db["users"]

async def add_user(id):
    users.insert_one({"_id": id, "limit": 10, "is_verified": False, "verify_token": "", "verified_time": 0})

async def update_user_limit(id, limit):
    users.update_one({"_id": id}, {"$set": {"limit": limit}})

async def get_user_limit(id):
    user = users.find_one({"_id": id})
    return user.get("limit", 0) if user else 0

async def get_verify_status(id):
    user = users.find_one({"_id": id})
    return user if user else {"is_verified": False, "verify_token": "", "verified_time": 0}

async def update_verify_status(id, is_verified=None, verify_token=None, verified_time=None):
    update_fields = {}
    if is_verified is not None:
        update_fields["is_verified"] = is_verified
    if verify_token is not None:
        update_fields["verify_token"] = verify_token
    if verified_time is not None:
        update_fields["verified_time"] = verified_time

    users.update_one({"_id": id}, {"$set": update_fields})
