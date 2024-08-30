import asyncio
import base64
import logging
import os
import random
import string

from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
#from motor.motor_asyncio import AsyncIOMotorClient
from bot import Bot
from config import *
from helper_func import subscribed, encode, decode, get_messages
from database.database import del_user, full_userbase , add_user, get_user_limit, update_user_limit, store_token, verify_token

from shortzy import Shortzy

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

START_COMMAND_LIMIT = 15  # Default limit for new users
LIMIT_INCREASE_AMOUNT = 10  # Amount by which the limit is increased after verification

"""
# Initialize MongoDB client and database
mongo_client = AsyncIOMotorClient(DB_URI)
db = mongo_client[DB_NAME]
user_collection = db['user_collection']
token_collection = db['tokens']
"""

def generate_token():
    """Generate a random token."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

@Client.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await user_collection.find_one({"_id": user_id}):
        await add_user(user_id)

    user_limit = await get_user_limit(user_id)
    
    if user_limit <= 0:
        await message.reply_text("Your limit has been reached. Use /limit to increase your limit.")
        return

    await update_user_limit(user_id, user_limit - 1)

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            decoded_string = await decode(base64_string)
            argument = decoded_string.split("-")
            
            if len(argument) == 3:
                try:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                    ids = range(start, end + 1) if start <= end else []
                except:
                    return
            elif len(argument) == 2:
                try:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                except:
                    return
            else:
                ids = []
            
            temp_msg = await message.reply("Please wait...")
            try:
                messages = await get_messages(client, ids)
            except:
                await message.reply_text("Something went wrong..!")
                return
            await temp_msg.delete()

            for msg in messages:
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name) if CUSTOM_CAPTION and msg.document else "" if not msg.caption else msg.caption.html

                reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None

                try:
                    await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                    await asyncio.sleep(0.5)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                except Exception as e:
                    logger.error(f"Error copying message: {e}")
                    pass
        return

    else:

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("😊 About Me", callback_data="about"),
                InlineKeyboardButton("🔒 Close", callback_data="close")
            ]
        ]
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

@Client.on_message(filters.command('limit') & filters.private)
async def limit_command(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        token = generate_token()
        await store_token(user_id, token)

        verification_link = f"https://t.me/{client.username}?start=limit_{token}"

        await message.reply_text(f"Your current limit is {await get_user_limit(user_id)}. Increase your limit using the link below:\n{verification_link}")
    except Exception as e:
        logger.error(f"Error in limit_command: {e}")
        await message.reply_text("An error occurred while generating the verification link.")

@Client.on_message(filters.regex(r'^/start limit_(\w+)$') & filters.private)
async def verify_token_command(client: Client, message: Message):
    user_id = message.from_user.id
    token = message.text.split('limit_')[1]

    try:
        if await verify_token(user_id, token):
            user_limit = await get_user_limit(user_id)
            new_limit = user_limit + LIMIT_INCREASE_AMOUNT
            await update_user_limit(user_id, new_limit)

            await message.reply_text(f"Your limit has been increased by {LIMIT_INCREASE_AMOUNT}. Your new limit is {new_limit}.")
        else:
            await message.reply_text("Invalid or already used token.")
    except Exception as e:
        logger.error(f"Error in verify_token_command: {e}")
        await message.reply_text("An error occurred during token verification.")

@Client.on_message(filters.command('check') & filters.private)
async def check_command(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        user_limit = await get_user_limit(user_id)
        await message.reply_text(f"Your current limit is {user_limit}.")
    except Exception as e:
        logger.error(f"Error in check_command: {e}")
        await message.reply_text("An error occurred while checking your limit.")

#=====================================================================================##

WAIT_MSG = "<b>Processing ...</b>"
REPLY_ERROR = "<code>Use this command as a reply to any telegram message without any spaces.</code>"

#=====================================================================================##

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(text="Join Channel", url=client.invitelink),
            InlineKeyboardButton(text="Join Channel", url=client.invitelink2),
        ],
        [
            InlineKeyboardButton(text="Join Channel", url=client.invitelink3),
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
