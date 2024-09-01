# https://www.youtube.com/channel/UC7tAa4hho37iNv731_6RIOg
import asyncio
import base64
import logging
import os
import random
import re
import string
import time
from datetime import datetime
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from cbb import *
from bot import Bot
from config import (
    ADMINS,
    FORCE_MSG,
    START_MSG,
    CUSTOM_CAPTION,
    IS_VERIFY,
    VERIFY_EXPIRE,
    SHORTLINK_API,
    SHORTLINK_URL,
    DISABLE_CHANNEL_BUTTON,
    PROTECT_CONTENT,
    TUT_VID,
    DB_URI,
    DB_NAME,
    OWNER_ID,
)
from helper_func import subscribed, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time
from database.database import add_user, del_user, full_userbase, present_user ,db_verify_status 
from shortzy import Shortzy
import pytz
# Import Motor for async MongoDB operations
from motor.motor_asyncio import AsyncIOMotorClient

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB Client
mongo_client = AsyncIOMotorClient(DB_URI)
db = mongo_client[DB_NAME]  # Replace with your database name
tokens_collection = db['tokens']  # Collection for token counts

# Set timezone to UTC+5:30
tz = pytz.timezone('Asia/Kolkata')

# Helper Functions for Token Counting
async def increment_token_count(user_id: int):
    """Increments the total token count and the user's token count."""
    today = datetime.now(tz).strftime('%Y-%m-%d')
    # Increment total tokens for today
    await tokens_collection.update_one(
        {'date': today},
        {'$inc': {'today_tokens': 1, 'total_tokens': 1}},
        upsert=True
    )
    # Increment user's token count
    await tokens_collection.update_one(
        {'user_id': user_id},
        {'$inc': {'user_tokens': 1}},
        upsert=True
    )

async def get_today_token_count():
    """Retrieves today's total token count."""
    today = datetime.now(tz).strftime('%Y-%m-%d')
    doc = await tokens_collection.find_one({'date': today})
    return doc['today_tokens'] if doc and 'today_tokens' in doc else 0

async def get_total_token_count():
    """Retrieves the total token count."""
    pipeline = [
        {
            '$group': {
                '_id': None,
                'total': {'$sum': '$total_tokens'}
            }
        }
    ]
    result = await tokens_collection.aggregate(pipeline).to_list(length=1)
    return result[0]['total'] if result else 0

async def get_user_token_count(user_id: int):
    """Retrieves the token count for a specific user."""
    doc = await tokens_collection.find_one({'user_id': user_id})
    return doc['user_tokens'] if doc and 'user_tokens' in doc else 0

# Modify /start Command to Include Token Counts
@Bot.on_message(filters.command("start") & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    owner_id = ADMINS  # Fetch the owner's ID from config
    verify_status = await db_verify_status(user_id)

    # Check if the user is the owner
    if user_id in owner_id:
        # Owner-specific actions
        await message.reply("You are the owner! Additional actions can be added here.")
        return

    # Handle new users
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except Exception as e:
            logger.error(f"Failed to add user: {e}")

    # Handle verification
    if verify_status["is_verified"] and VERIFY_EXPIRE < (
        time.time() - verify_status["verified_time"]
    ):
        await update_verify_status(user_id, is_verified=False)

    if "verify_" in message.text:
        _, token = message.text.split("_", 1)
        if verify_status["verify_token"] != token:
            return await message.reply(
                "Your token is invalid or expired. Try again by clicking /start"
            )
        verify_status["is_verified"] = True
        verify_status["verified_time"] = time.time()
        await increment_token_count(user_id)
        await update_verify_status(user_id, is_verified=True, verified_time=time.time())
        reply_markup = None
        await message.reply(
            f"Your token is successfully verified and valid for 24 hours.",
            reply_markup=reply_markup,
            protect_content=False,
            quote=True,
        )

    elif len(message.text) > 7 and verify_status["is_verified"]:
        try:
            base64_string = message.text.split(" ", 1)[1]
        except:
            return
        _string = await decode(base64_string)
        argument = _string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong..!")
            return
        await temp_msg.delete()

        snt_msgs = []

        for msg in messages:
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name,
                )
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                snt_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT,
                )
                await asyncio.sleep(0.5)
                snt_msgs.append(snt_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                snt_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT,
                )
                snt_msgs.append(snt_msg)
            except:
                pass
    elif verify_status["is_verified"]:

        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("About Me", callback_data="about"),
                    InlineKeyboardButton("Close", callback_data="close"),
                ],
                [
                    InlineKeyboardButton(
                        "Check Token Count", callback_data="check_tokens"
                    )
                ],
            ]
        )
        user_tokens = await get_user_token_count(user_id)

        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None
                if not message.from_user.username
                else "@" + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id,
            )
            + f"\n\n<b>Your Total Token Count:</b> {user_tokens}",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML,
            quote=True,
        )

    else:
        if IS_VERIFY and not verify_status["is_verified"]:
            token = "".join(random.choices(string.ascii_letters + string.digits, k=10))
            verification_link = (
                f"https://telegram.dog/{client.username}?start=verify_{token}"
            )
            await update_verify_status(
                user_id, verify_token=token, link=verification_link
            )
            link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, verification_link)
            btn = [
                [InlineKeyboardButton("Click here", url=link)],
                [InlineKeyboardButton("How to use the bot", url=TUT_VID)],
            ]
            await message.reply(
                f"Your Ads token is expired. Refresh your token and try again.\n\nToken Timeout: {get_exp_time(VERIFY_EXPIRE)}\n\nWhat is the token?\n\nThis is an ads token. If you pass 1 ad, you can use the bot for 24 hours after passing the ad.",
                reply_markup=InlineKeyboardMarkup(btn),
                protect_content=False,
                parse_mode=ParseMode.HTML,
                quote=True,
            )


# Handle Callback Queries for Token Count
@Bot.on_callback_query(filters.regex(r"^check_tokens$"))
async def check_tokens_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    is_admin = user_id in ADMINS

    # Fetch token counts
    today_tokens = await get_today_token_count()
    total_tokens = await get_total_token_count()
    user_tokens = await get_user_token_count(user_id)

    if is_admin:
        # For admins, optionally display more detailed stats
        users = await full_userbase()
        user_token_details = ""
        for user in users[:10]:  # Limit to first 10 users for brevity
            tokens = await get_user_token_count(user)
            user_token_details += f"User ID: {user} - Tokens: {tokens}\n"
        response = (
            f"<b>🔹 Admin Token Statistics 🔹</b>\n\n"
            f"<b>Today's Token Count:</b> {today_tokens}\n"
            f"<b>Total Token Count:</b> {total_tokens}\n\n"
            f"<b>Top Users:</b>\n{user_token_details}"
        )
    else:
        # For regular users
        response = (
            f"<b>📊 Your Token Statistics 📊</b>\n\n"
            f"<b>Today's Token Count:</b> {today_tokens}\n"
            f"<b>Total Token Count:</b> {total_tokens}\n"
            f"<b>Your Token Count:</b> {user_tokens}"
        )

    await callback_query.answer()
    await callback_query.message.edit_text(
        text=response,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data="close")]]
        )
    )


# Existing /start Not Joined Handler
@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(
                "Join Channel",
                url=client.invitelink
            )
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text='Try Again',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text=FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
        disable_web_page_preview=True
    )

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message with out any spaces.</code>"""

# Existing /users Command for Admins
@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Client, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

# Existing /broadcast Command for Admins
@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Client, message: Message):
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

# Add a New Command /tokencount for Users and Admins
@Bot.on_message(filters.command('tokencount') & filters.private)
async def token_count_command(client: Client, message: Message):
    user_id = message.from_user.id
    is_admin = user_id in ADMINS

    # Fetch token counts
    today_tokens = await get_today_token_count()
    total_tokens = await get_total_token_count()
    user_tokens = await get_user_token_count(user_id)

    if is_admin:
        # For admins, optionally display more detailed stats
        users = await full_userbase()
        user_token_details = ""
        for user in users[:10]:  # Limit to first 10 users for brevity
            tokens = await get_user_token_count(user)
            user_token_details += f"User ID: {user} - Tokens: {tokens}\n"
        response = (
            f"<b>🔹 Admin Token Statistics 🔹</b>\n\n"
            f"<b>Today's Token Count:</b> {today_tokens}\n"
            f"<b>Total Token Count:</b> {total_tokens}\n\n"
            f"<b>Top Users:</b>\n{user_token_details}"
        )
    else:
        # For regular users
        response = (
            f"<b>📊 Your Token Statistics 📊</b>\n\n"
            f"<b>Today's Token Count:</b> {today_tokens}\n"
            f"<b>Total Token Count:</b> {total_tokens}\n"
            f"<b>Your Token Count:</b> {user_tokens}"
        )

    await message.reply_text(
        text=response,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Close", callback_data="close")]]
        )
    )
