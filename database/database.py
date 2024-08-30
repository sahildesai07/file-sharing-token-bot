from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME , START_COMMAND_LIMIT
from datetime import datetime, timedelta

mongo_client = AsyncIOMotorClient(DB_URI)
db = mongo_client[DB_NAME]

user_collection = db['user_collection']
token_collection = db['tokens']
user_data = db['users']

verification_log_collection = db['verification_logs']

async def log_verification(user_id):
    await verification_log_collection.insert_one({
        "user_id": user_id,
        "timestamp": datetime.utcnow()
    })


async def get_verification_count(timeframe):
    current_time = datetime.utcnow()
    
    if timeframe == "24h":
        start_time = current_time - timedelta(hours=24)
    elif timeframe == "today":
        start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    elif timeframe == "monthly":
        start_time = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    count = await verification_log_collection.count_documents({
        "timestamp": {"$gte": start_time, "$lt": current_time}
    })
    
    return count

async def cleanup_old_logs():
    expiry_time = datetime.utcnow() - timedelta(hours=24)
    await verification_log_collection.delete_many({
        "timestamp": {"$lt": expiry_time}
    })
    
async def get_previous_token(user_id):
    user_data = await user_collection.find_one({"_id": user_id})
    return user_data.get("previous_token", None)

async def set_previous_token(user_id, token):
    await user_collection.update_one({"_id": user_id}, {"$set": {"previous_token": token}})
    
async def add_user(user_id):
    await user_collection.insert_one({
        "_id": user_id,
        "limit": START_COMMAND_LIMIT
    })
"""
async def present_user(user_id : int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)
    """

async def present_user(user_id):
    user_data = await user_collection.find_one({"_id": user_id})
    return user_data is not None

async def full_userbase():
    user_docs = user_collection.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return

async def get_user_limit(user_id):
    user_data = await user_collection.find_one({"_id": user_id})
    if user_data:
        return user_data.get('limit', 0)
    return 0

async def update_user_limit(user_id, new_limit):
    await user_collection.update_one({"_id": user_id}, {"$set": {"limit": new_limit}})

async def store_token(user_id, token):
    await token_collection.insert_one({
        "user_id": user_id,
        "token": token,
        "used": False
    })

async def verify_token(user_id, token):
    token_data = await token_collection.find_one({"user_id": user_id, "token": token, "used": False})
    if token_data:
        await token_collection.update_one({"_id": token_data['_id']}, {"$set": {"used": True}})
        return True
    return False


