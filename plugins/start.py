 # https://www.youtube.com/channel/UC7tAa4hho37iNv731_6RIOg
import asyncio
import base64
import logging
import os
import random
import re
import string
import time

from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import (
    ADMINS,
    FORCE_MSG,
    START_MSG,
    CUSTOM_CAPTION,
    IS_VERIFY,
    DB_NAME,
    DB_URI,
    VERIFY_EXPIRE,
    SHORTLINK_API,
    SHORTLINK_URL,
    DISABLE_CHANNEL_BUTTON,
    PROTECT_CONTENT,
    TUT_VID,
    OWNER_ID,
)
from helper_func import subscribed, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time
from database.database import   add_user, del_user, full_userbase, present_user
from shortzy import Shortzy

"""add time in seconds for waiting before delete 
1 min = 60, 2 min = 60 × 2 = 120, 5 min = 60 × 5 = 300"""
# SECONDS = int(os.getenv("SECONDS", "1200"))

from pymongo import MongoClient
from pytz import timezone
from datetime import datetime, timedelta

# MongoDB setup
client = MongoClient(DB_URI)
db = client[DB_NAME]
verifications_collection = db['verifications']
users_collection = db["users"]
INDIA_TZ = timezone('Asia/Kolkata')

# Constants
IS_VERIFY = True
VERIFY_EXPIRE = 86400  # 24 hours in seconds

async def get_verify_status(user_id):
    user = users_collection.find_one({"user_id": user_id})
    return user if user else {"is_verified": False, "verified_time": 0, "verify_token": "", "link": ""}

async def update_verify_status(user_id, **kwargs):
    users_collection.update_one({"user_id": user_id}, {"$set": kwargs}, upsert=True)

async def add_user(user_id):
    users_collection.insert_one({"user_id": user_id, "is_verified": False, "verified_time": 0, "verify_token": "", "link": ""})

async def present_user(user_id):
    return users_collection.find_one({"user_id": user_id}) is not None

async def increment_verification_count():
    now = datetime.now()
    users_collection.update_one(
        {"date": now.strftime("%Y-%m-%d")},
        {"$inc": {"daily_verified_count": 1, "last_24h_verified_count": 1}},
        upsert=True
    )

async def reset_24h_count():
    users_collection.update_many(
        {},
        {"$set": {"last_24h_verified_count": 0}}
    )

@Client.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message):
    user_id = message.from_user.id

    # Fetch the user's verification status
    verify_status = await get_verify_status(user_id)

    # If the user is verified, show a welcome message
    if verify_status['is_verified']:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("About Me", callback_data="about"),
              InlineKeyboardButton("Close", callback_data="close")]]
        )
        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )

    # If the user is not verified or token is invalid, generate a new token
    else:
        if IS_VERIFY and not verify_status['is_verified']:
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await update_verify_status(user_id, verify_token=token, link="")
            link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{client.username}?start=verify_{token}')
            btn = [
                [InlineKeyboardButton("Click here", url=link)],
                [InlineKeyboardButton('How to use the bot', url="your_tutorial_video_link")]
            ]
            await message.reply(f"Your Ads token is expired, refresh your token and try again.\n\nToken Timeout: {timedelta(seconds=VERIFY_EXPIRE)}\n\nWhat is the token?\n\nThis is an ads token. If you pass 1 ad, you can use the bot for 24 Hour after passing the ad.", reply_markup=InlineKeyboardMarkup(btn), protect_content=False, quote=True)

    # Token verification
    if "verify_" in message.text:
        _, token = message.text.split("_", 1)
        if verify_status['verify_token'] != token:
            return await message.reply("Your token is invalid or Expired. Try again by clicking /start")
        await update_verify_status(user_id, is_verified=True, verified_time=time.time())

        # Increment verification count
        await increment_verification_count()

        await message.reply(f"Your token successfully verified and valid for 24 Hours", protect_content=False, quote=True)

    # Reset the 24h verification count periodically
    now = datetime.now()
    midnight = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=1)
    time_until_midnight = (midnight - now).total_seconds()

    if time_until_midnight <= 1:
        await reset_24h_count()

@Client.on_message(filters.command('count') & filters.private)
async def count_command(client: Client, message):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    data = users_collection.find_one({"date": today})

    if data:
        daily_count = data.get("daily_verified_count", 0)
        last_24h_count = data.get("last_24h_verified_count", 0)
    else:
        daily_count = 0
        last_24h_count = 0

    await message.reply(f"Today's Verified Users: {daily_count}\nLast 24 Hours Verified Users: {last_24h_count}")
 



#=====================================================================================##

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message with out any spaces.</code>"""

#=====================================================================================##

    
    
@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlilneKeyboardButton(
                "Join Channel",
                url = client.invitelink)
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
