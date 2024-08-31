import motor.motor_asyncio
from config import DB_URI, DB_NAME

# Database client and setup
dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]
user_data = database['users']

# Default verification status
default_verify = {
    'is_verified': False,
    'verified_time': 0,
    'verify_token': "",
    'link': "",
    'verify_count': 0
}

# Create a new user schema
def new_user(user_id):
    return {
        '_id': user_id,
        'verify_status': default_verify
    }

# Check if a user exists in the database
async def present_user(user_id: int):
    found = await user_data.find_one({'_id': user_id})
    return bool(found)

# Add a new user to the database
async def add_user(user_id: int):
    user = new_user(user_id)
    await user_data.insert_one(user)

# Retrieve verification status of a user
async def db_verify_status(user_id):
    user = await user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

# Count the number of users who have verified their tokens
async def count_verified_users():
    verified_count = await user_data.count_documents({'verify_status.is_verified': True})
    return verified_count

# Update the user's verification status
async def db_update_verify_status(user_id, verify):
    # Increment verify_count each time the user verifies their token
    current_status = await db_verify_status(user_id)
    new_count = current_status.get('verify_count', 0) + 1
    verify['verify_count'] = new_count
    await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})

# Retrieve all users from the database
async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] async for doc in user_docs]
    return user_ids

# Delete a user from the database
async def del_user(user_id: int):
    await user_data.delete_one({'_id': user_id})
