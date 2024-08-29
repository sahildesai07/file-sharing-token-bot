import pymongo
from config import DB_URI, DB_NAME

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

user_data = database['users']

# Check if user exists
async def present_user(user_id: int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

# Add a new user with an initial usage count of 0
async def add_user(user_id: int):
    user_data.insert_one({'_id': user_id, 'usage_count': 0})
    return

# Get the full list of users
async def full_userbase():
    user_docs = user_data.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])
    return user_ids

# Delete a user
async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return

# Get the current usage count for a user
async def get_usage_count(user_id: int):
    user = user_data.find_one({'_id': user_id})
    if user and 'usage_count' in user:
        return user['usage_count']
    return 0

# Increment the usage count for a user
async def increment_usage_count(user_id: int):
    user_data.update_one({'_id': user_id}, {'$inc': {'usage_count': 1}})
    return

# Reset the usage count for a user
async def reset_usage_count(user_id: int):
    user_data.update_one({'_id': user_id}, {'$set': {'usage_count': 0}})
    return
