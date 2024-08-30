import motor.motor_asyncio
from config import DB_URI, DB_NAME

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

user_data = database['users']
# Define collections
user_collection = database['user_collection']
token_collection = database['tokens']

default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

default_user = {
    '_id': None,
    'verify_status': default_verify,
    'credits': 0  # Default credit amount
}


async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] async for doc in user_docs]
    return user_ids

async def del_user(user_id: int):
    await user_data.delete_one({'_id': user_id})
    return




# Functions to manage users and tokens
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
    result = await user_collection.update_one({"_id": user_id}, {"$set": {"limit": new_limit}})
    if result.modified_count == 0:
        logger.info(f"No document updated for user_id: {user_id}")

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

