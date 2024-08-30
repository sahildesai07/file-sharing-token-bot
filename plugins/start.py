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
from pymongo import MongoClient
from bot import Bot
from config import *
from helper_func import *
from database.database import  del_user, full_userbase #, present_user , add_user
from shortzy import Shortzy

client = MongoClient(DB_URI)
db = client[DB_NAME]
user_collection = db['users']
token_collection = db['tokens']

# Define limits
START_COMMAND_LIMIT = 15  # Default limit for new users
LIMIT_INCREASE_AMOUNT = 10  # Amount by which the limit is increased after verification

# Utility function to check if the user exists in the database
async def present_user(user_id):
    return user_collection.find_one({"_id": user_id})

# Utility function to add a new user with the default limit
async def add_user(user_id):
    user_collection.insert_one({
        "_id": user_id,
        "limit": START_COMMAND_LIMIT
    })

# Utility function to get the user's current limit
async def get_user_limit(user_id):
    user_data = await present_user(user_id)
    if user_data:
        return user_data['limit']
    return START_COMMAND_LIMIT

# Utility function to update the user's limit
async def update_user_limit(user_id, new_limit):
    user_collection.update_one({"_id": user_id}, {"$set": {"limit": new_limit}})

# Utility function to generate a random token for verification
def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Main start command handler
@Client.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if user exists in the database; if not, add them
    if not await present_user(user_id):
        await add_user(user_id)

    # Get the user's current limit
    user_limit = await get_user_limit(user_id)
    
    # If the user has no limit left, prompt them to increase it
    if user_limit <= 0:
        await message.reply_text("Your limit has been reached. Use /limit to increase your limit.")
        return

    # Decrease the user's limit by 1 each time they use the /start command
    await update_user_limit(user_id, user_limit - 1)

    text = message.text
    if len(text) > 7:
        try:
            # Decode the base64 string to retrieve the original arguments
            base64_string = text.split(" ", 1)[1]
        except:
            return

        string = await decode(base64_string)
        argument = string.split("-")
        
        # Determine the range of message IDs to retrieve
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return

            ids = range(start, end + 1) if start <= end else range(end, start + 1)
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return

        # Send a temporary "Please wait..." message while fetching the original messages
        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong..!")
            return

        await temp_msg.delete()

        for msg in messages:
            # Customize the caption if needed
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name
                )
            else:
                caption = "" if not msg.caption else msg.caption.html

            reply_markup = msg.reply_markup if DISABLE_CHANNEL_BUTTON else None

            try:
                # Copy the message to the user's chat
                await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                await asyncio.sleep(0.5)  # Prevent hitting rate limits
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
            except:
                pass
        return
    else:
        # Default response if the /start command is used without arguments
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
        return

# Limit command handler to generate and store a verification token
@Client.on_message(filters.command('limit') & filters.private)
async def limit_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_limit = await get_user_limit(user_id)

    # Generate a verification link using a random token
    token = generate_token()
    verification_link = f"https://telegram.dog/{client.username}?start=limit_{token}"

    # Store the token in the database with the user_id for later verification
    token_collection.insert_one({
        "user_id": user_id,
        "token": token,
        "used": False  # To track if the token has already been used
    })

    await message.reply_text(f"Your current limit is {user_limit}. You can increase your limit by using the link below:\n{verification_link}")

# Token verification handler to increase the user's limit
@Client.on_message(filters.regex(r'^/start limit_(\w+)$') & filters.private)
async def verify_token_command(client: Client, message: Message):
    user_id = message.from_user.id
    token = message.text.split('limit_')[1]

    # Check if the token is valid and hasn't been used
    token_data = token_collection.find_one({"user_id": user_id, "token": token, "used": False})
    if not token_data:
        await message.reply_text("Invalid or already used token.")
        return

    # Increase the user's limit
    user_limit = await get_user_limit(user_id)
    new_limit = user_limit + LIMIT_INCREASE_AMOUNT
    await update_user_limit(user_id, new_limit)

    # Mark the token as used
    token_collection.update_one({"_id": token_data['_id']}, {"$set": {"used": True}})

    await message.reply_text(f"Your limit has been increased by {LIMIT_INCREASE_AMOUNT}. Your new limit is {new_limit}.")

        
#=====================================================================================##

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message with out any spaces.</code>"""

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
            #InlineKeyboardButton(text="Join Channel", url=client.invitelink4),
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
