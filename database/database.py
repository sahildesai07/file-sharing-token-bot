import motor.motor_asyncio
from datetime import datetime, timedelta
from config import DB_URI, DB_NAME

# Initialize the MongoDB client and define the database and collection
dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]
user_data = database['users']

# Default structure for verification status
default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': ""
}

# Function to create a new user document template
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

# Function to count total verified users in the database
async def count_verified_users():
    count = await user_data.count_documents({'verify_status.is_verified': True})
    return count

# Function to get the start of the current day
def get_start_of_day():
    now = datetime.now()
    return datetime(now.year, now.month, now.day)

# Function to get the start of the current week
def get_start_of_week():
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    return datetime(start_of_week.year, start_of_week.month, start_of_week.day)

# Function to count the number of users verified today
async def count_verified_users_today():
    start_of_day = get_start_of_day()
    count = await user_data.count_documents({
        'verify_status.is_verified': True,
        'verify_status.verified_time': {'$gte': start_of_day}
    })
    return count

# Function to count the number of users verified in the last 24 hours
async def count_verified_users_last_24h():
    last_24h = datetime.now() - timedelta(hours=24)
    count = await user_data.count_documents({
        'verify_status.is_verified': True,
        'verify_status.verified_time': {'$gte': last_24h}
    })
    return count

# Function to count the number of users verified this week
async def count_verified_users_this_week():
    start_of_week = get_start_of_week()
    count = await user_data.count_documents({
        'verify_status.is_verified': True,
        'verify_status.verified_time': {'$gte': start_of_week}
    })
    return count

# Function to check if a user exists in the database
async def present_user(user_id: int):
    found = await user_data.find_one({'_id': user_id})
    return bool(found)

# Function to add a new user to the database
async def add_user(user_id: int):
    user = new_user(user_id)
    await user_data.insert_one(user)
    return

# Function to get the verification status of a user
async def db_verify_status(user_id):
    user = await user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

# Function to update the verification status of a user
async def db_update_verify_status(user_id, verify):
    await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

# Function to get a list of all user IDs in the database
async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] async for doc in user_docs]
    return user_ids

# Function to delete a user from the database
async def del_user(user_id: int):
    await user_data.delete_one({'_id': user_id})
    return
