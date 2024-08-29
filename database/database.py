import pymongo
from config import DB_URI, DB_NAME, USER_LIMIT

# Initialize MongoDB client
dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

# Collection reference
user_data = database['users']

# Function to add a new user
async def add_user(user_id):
    user = {
        "_id": user_id,
        "is_verified": False,
        "verify_token": "",
        "verified_time": None,
        "limit": USER_LIMIT  # Initialize with default limit
    }
    user_data.insert_one(user)

# Function to check if user exists
async def present_user(user_id):
    user = user_data.find_one({"_id": user_id})
    return user is not None

async def db_verify_status(user_id):
    user = await user_data.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

async def db_update_verify_status(user_id, verify):
    await user_data.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})


# Function to get user's verification status and limits
async def get_verify_status(user_id):
    user = user_data.find_one({"_id": user_id})
    return {
        "is_verified": user.get("is_verified", False),
        "verify_token": user.get("verify_token", ""),
        "verified_time": user.get("verified_time", None),
        "limit": user.get("limit", USER_LIMIT)
    }

# Function to update user's verification status
async def update_verify_status(user_id, is_verified=None, verify_token=None, verified_time=None):
    update_data = {}
    if is_verified is not None:
        update_data["is_verified"] = is_verified
    if verify_token is not None:
        update_data["verify_token"] = verify_token
    if verified_time is not None:
        update_data["verified_time"] = verified_time
    if update_data:
        user_data.update_one({"_id": user_id}, {"$set": update_data})

# Function to decrement user's limit
async def decrement_user_limit(user_id):
    user_data.update_one({"_id": user_id}, {"$inc": {"limit": -1}})

# Function to get user's current limit
async def get_user_limit(user_id):
    user = user_data.find_one({"_id": user_id})
    return user.get("limit", USER_LIMIT)

# Function to reset user's limits after verification
async def reset_user_limits(user_id):
    user_data.update_one({"_id": user_id}, {"$set": {"limit": USER_LIMIT}})
