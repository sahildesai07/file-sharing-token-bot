
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
            'verified_time': "",
            'verify_token': "",
            'link': ""
        }
    }

async def count_verified_users_24hr_and_today():
    now = time.time()
    start_of_today = time.mktime(datetime.date.today().timetuple())

    # Get the count of users who verified in the last 24 hours
    count_24hr = await db.count_documents({
        'verified_time': {'$gte': now - 86400},  # Last 24 hours
        'is_verified': True
    })

    # Get the count of users who verified today
    count_today = await db.count_documents({
        'verified_time': {'$gte': start_of_today},
        'is_verified': True
    })

    return count_24hr, count_today

async def get_token_verification_stats():
    today_date = datetime.datetime.utcnow().date()
    yesterday_date = today_date - datetime.timedelta(days=1)

    # Count the verifications from yesterday and today
    verifications_today = await db.count_documents({'verified_date': today_date})
    verifications_last_24_hours = await db.count_documents({'verified_time': {'$gte': time.time() - 86400}})

    return verifications_today, verifications_last_24_hours


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
