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


async def get_verify_status(user_id):
    user = user_data.find_one({"user_id": user_id})
    return user if user else {"is_verified": False, "verified_time": 0, "verify_token": "", "link": ""}

async def update_verify_status(user_id, **kwargs):
    user_data.update_one({"user_id": user_id}, {"$set": kwargs}, upsert=True)

async def add_user(user_id):
    user_data.insert_one({"user_id": user_id, "is_verified": False, "verified_time": 0, "verify_token": "", "link": ""})

async def present_user(user_id):
    return user_data.find_one({"user_id": user_id}) is not None

async def increment_verification_count():
    now = datetime.now()
    user_data.update_one(
        {"date": now.strftime("%Y-%m-%d")},
        {"$inc": {"daily_verified_count": 1, "last_24h_verified_count": 1}},
        upsert=True
    )

async def reset_24h_count():
    user_data.update_many(
        {},
        {"$set": {"last_24h_verified_count": 0}}
    )


"""

# Function to check if a user exists in the database
async def present_user(user_id: int):
    found = await user_data.find_one({'_id': user_id})
    return bool(found)

# Function to add a new user to the database
async def add_user(user_id: int):
    user = new_user(user_id)
    await user_data.insert_one(user)
    return
"""
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
