
import motor.motor_asyncio
from config import DB_URI, DB_NAME
from datetime import datetime, timedelta

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
            'verified_time': "",
            'verify_token': "",
            'link': ""
        }
    }



async def count_verified_users():
    count = user_data.count_documents({'is_verified': True})
    return count

def get_start_of_day():
    now = datetime.now()
    return datetime(now.year, now.month, now.day)

def get_start_of_week():
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    return datetime(start_of_week.year, start_of_week.month, start_of_week.day)

async def count_verified_users_today():
    start_of_day = get_start_of_day()
    count = user_data.count_documents({'is_verified': True, 'verified_time': {'$gte': start_of_day}})
    return count

async def count_verified_users_last_24h():
    last_24h = datetime.now() - timedelta(hours=24)
    count = user_data.count_documents({'is_verified': True, 'verified_time': {'$gte': last_24h}})
    return count

async def count_verified_users_this_week():
    start_of_week = get_start_of_week()
    count = user_data.count_documents({'is_verified': True, 'verified_time': {'$gte': start_of_week}})
    return count

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
