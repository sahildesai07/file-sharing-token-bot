from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME , START_COMMAND_LIMIT

mongo_client = AsyncIOMotorClient(DB_URI)
db = mongo_client[DB_NAME]

user_collection = db['user_collection']
token_collection = db['tokens']

async def add_user(user_id):
    await user_collection.insert_one({
        "_id": user_id,
        "limit": START_COMMAND_LIMIT
    })

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


