import pymongo
import time
from config import DB_URI, DB_NAME

# Database connection
client = pymongo.MongoClient(DB_URI)
db = client[DB_NAME]

# Users collection
users_collection = db['users']
verifications_collection = db['verifications']

async def add_user(user_id: int):
    """Add a new user to the database."""
    users_collection.insert_one({'user_id': user_id, 'join_date': time.time()})

async def del_user(user_id: int):
    """Delete a user from the database."""
    users_collection.delete_one({'user_id': user_id})

async def full_userbase():
    """Return the full list of users."""
    return [user['user_id'] for user in users_collection.find()]

async def present_user(user_id: int):
    """Check if a user is already in the database."""
    return users_collection.find_one({'user_id': user_id})

async def get_verify_status(user_id: int):
    """Retrieve the verification status of a user."""
    user_data = users_collection.find_one({'user_id': user_id})
    if not user_data:
        return {"is_verified": False, "verify_token": None, "link": None, "verified_time": 0}
    return {
        "is_verified": user_data.get("is_verified", False),
        "verify_token": user_data.get("verify_token", None),
        "link": user_data.get("link", ""),
        "verified_time": user_data.get("verified_time", 0)
    }

async def update_verify_status(user_id: int, is_verified: bool = False, verify_token: str = None, verified_time: float = 0, link: str = ""):
    """Update the verification status of a user."""
    update_data = {
        "is_verified": is_verified,
        "verified_time": verified_time,
        "verify_token": verify_token,
        "link": link
    }
    users_collection.update_one({"user_id": user_id}, {"$set": update_data}, upsert=True)

async def add_verification_data(user_id: int, token: str, verified_time: float):
    """Add a verification entry to the database."""
    verifications_collection.insert_one({
        "user_id": user_id,
        "token": token,
        "verified_time": verified_time
    })

async def get_token_verification_stats():
    """Retrieve all verification statistics."""
    return list(verifications_collection.find())

async def count_verified_users_24hr_and_today():
    """Count users who verified their tokens in the last 24 hours."""
    now = time.time()
    last_24_hours = now - 86400
    today = time.time() - time.time() % 86400
    return {
        "last_24_hours": verifications_collection.count_documents({"verified_time": {"$gte": last_24_hours}}),
        "today": verifications_collection.count_documents({"verified_time": {"$gte": today}})
    }


async def db_verify_status(user_id):
    user = await users_collection.find_one({'_id': user_id})
    if user:
        return user.get('verify_status', default_verify)
    return default_verify

async def db_update_verify_status(user_id, verify):
    await users_collection.update_one({'_id': user_id}, {'$set': {'verify_status': verify}})
