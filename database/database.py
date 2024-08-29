import motor.motor_asyncio
from config import DB_URI, DB_NAME

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

user_data = database['users']

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

def new_user(id):
    return {
        '_id': id,
        'verify_status': default_verify,
        'credits': 0  # Default credit amount
    }

async def present_user(user_id: int):
    found = await user_data.find_one({'_id': user_id})
    return bool(found)
"""
async def add_user(user_id: int):
    user = new_user(user_id)
    await user_data.insert_one(user)
    return
"""

async def db_verify_status(user_id):
    user = await user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

async def db_update_verify_status(user_id, verify):
    await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] async for doc in user_docs]
    return user_ids

async def del_user(user_id: int):
    await user_data.delete_one({'_id': user_id})
    return

# Credit management functions

async def get_credits(user_id: int):
    user = await user_data.find_one({'_id': user_id})
    if user:
        return user.get('credits', 0)
    return 0

async def update_credits(user_id: int, new_credits: int):
    await user_data.update_one({'_id': user_id}, {'$set': {'credits': new_credits}})
    return

async def increment_credits(user_id: int, amount: int):
    user = await user_data.find_one({'_id': user_id})
    if user:
        current_credits = user.get('credits', 0)
        new_credits = current_credits + amount
        await update_credits(user_id, new_credits)
    return

async def decrement_credits(user_id: int, amount: int):
    user = await user_data.find_one({'_id': user_id})
    if user:
        current_credits = user.get('credits', 0)
        new_credits = max(current_credits - amount, 0)
        await update_credits(user_id, new_credits)
    return

from pymongo import MongoClient

# MongoDB setup
#client = MongoClient("mongodb+srv://Cluster0:Cluster0@cluster0.c07xkuf.mongodb.net/?retryWrites=true&w=majority")
#db = client.bot_database
#users_collection = db.users

async def add_user(user_id):
    users_collection.update_one({'_id': user_id}, {'$set': {'credits': 0}}, upsert=True)

async def get_user_credits(user_id):
    user = users_collection.find_one({'_id': user_id})
    if user:
        return user.get('credits', 0)
    return 0

async def update_user_credits(user_id, amount):
    users_collection.update_one({'_id': user_id}, {'$inc': {'credits': amount}}, upsert=True)

async def add_user_credits(user_id, amount):
    await update_user_credits(user_id, amount)

