# https://www.youtube.com/channel/UC7tAa4hho37iNv731_6RIOg
import asyncio
import time
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

def new_user(id):
    return {
        '_id': id,
        'verify_status': {
            'is_verified': False,
            'verified_time': 0,
            'verify_token': "",
            'link': ""
        },
        'verification_counts': {
            'total': 0,
            'today': 0,
            'last_24_hours': 0
        },
        'last_verification': 0  # To store the timestamp of the last verification
    }

async def reset_daily_counts():
    while True:
        await asyncio.sleep(86400)  # Sleep for 24 hours
        await user_data.update_many({}, {'$set': {'verification_counts.today': 0}})
        
async def clean_old_verifications():
    while True:
        current_time = time.time()
        users = await full_userbase()  # Assuming you have a function to get all users
        for user_id in users:
            user_data = await db_verify_status(user_id)
            
            # Ensure 'verification_counts' is initialized
            if 'verification_counts' not in user_data:
                user_data['verification_counts'] = {
                    'total': 0,
                    'last_24_hours': 0,
                    'today': 0
                }

            last_verification = user_data.get('last_verification', 0)
            if user_data['verification_counts']['last_24_hours'] > 0 and current_time - last_verification > 86400:
                user_data['verification_counts']['last_24_hours'] -= 1
                await db_update_verify_status(user_id, user_data)
        
        await asyncio.sleep(3600)  # Run every hour


async def present_user(user_id: int):
    found = await user_data.find_one({'_id': user_id})
    return bool(found)

async def add_user(user_id: int):
    user = new_user(user_id)
    await user_data.insert_one(user)
    return

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
