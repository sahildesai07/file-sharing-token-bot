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
from database.database import present_user ,get_previous_token , set_previous_token , del_user, full_userbase , add_user, get_user_limit, update_user_limit, store_token, verify_token , user_collection , token_collection 
import uuid
from shortzy import Shortzy

shortzy = Shortzy(api_key=SHORTLINK_API, base_site=SHORTLINK_URL)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

START_COMMAND_LIMIT = 15  # Default limit for new users
LIMIT_INCREASE_AMOUNT = 10  # Amount by which the limit is increased after verification
AUTO_DELETE_DELAY = 600  # Time in seconds after which messages will be deleted (600 seconds = 10 minutes)

# Load Shortzy settings from config
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "api.shareus.io")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "PUIAQBIFrydvLhIzAOeGV8yZppu2")

# Initialize Shortzy
async def get_shortlink(url, api, link):
    shortzy = Shortzy(api_key=api, base_site=url)
    verification_link = await shortzy.convert(link)
    return verification_link

async def delete_message_after_delay(message: Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")

@Client.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    # Ensure user exists in the database
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass

    # Retrieve user data
    user_data = await user_collection.find_one({"_id": user_id})
    user_limit = user_data.get("limit", 10)
    previous_token = user_data.get("previous_token")

    # Generate a new token only if previous_token is not available
    if not previous_token:
        previous_token = str(uuid.uuid4())
        await user_collection.update_one({"_id": user_id}, {"$set": {"previous_token": previous_token}}, upsert=True)

    # Generate the verification link
    verification_link = f"https://t.me/{client.username}?start=verify_{previous_token}"
    shortened_link = get_shortlink(SHORTLINK_URL, SHORTLINK_API, f"https://t.me/{client.username}?start=verify_{previous_token}")
    """
    # Use Shortzy to shorten the verification link
    try:
        shortened_link = shortzy.shorten(verification_link)
    except Exception as e:
        await message.reply_text(f"Error shortening the link: {str(e)}")
        return
    """
    # Check if the user is providing a verification token
    if len(message.text) > 7 and "verify_" in message.text:
        provided_token = message.text.split("verify_", 1)[1]
        if provided_token == previous_token:
            # Verification successful, increase limit by 10
            await update_user_limit(user_id, user_limit + 10)
            confirmation_message = await message.reply_text("Your limit has been successfully increased by 10!")
            asyncio.create_task(delete_message_after_delay(confirmation_message, AUTO_DELETE_DELAY))
            return
        else:
            error_message = await message.reply_text("Invalid verification token. Please try again.")
            asyncio.create_task(delete_message_after_delay(error_message, AUTO_DELETE_DELAY))
            return

    # If the limit is reached, prompt the user to use the verification link
    if user_limit <= 0:
        limit_message = await message.reply_text(f"Your limit has been reached. Use the following link to increase your limit: {shortened_link}")
        asyncio.create_task(delete_message_after_delay(limit_message, AUTO_DELETE_DELAY))
        return

    # Deduct 1 from the user's limit and continue with the normal start command process
    await update_user_limit(user_id, user_limit - 1)

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return
        string = await decode(base64_string)
        argument = string.split("-")
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

        for msg in messages:
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html,
                                                filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                sent_message = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML,
                                              reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                asyncio.create_task(delete_message_after_delay(sent_message, AUTO_DELETE_DELAY))
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                sent_message = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML,
                                              reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                asyncio.create_task(delete_message_after_delay(sent_message, AUTO_DELETE_DELAY))
            except:
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
        welcome_message = await message.reply_text(
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
        asyncio.create_task(delete_message_after_delay(welcome_message, AUTO_DELETE_DELAY))
        return

@Client.on_message(filters.command('check') & filters.private)
async def check_command(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        user_limit = await get_user_limit(user_id)
        limit_message = await message.reply_text(f"Your current limit is {user_limit}.")
        asyncio.create_task(delete_message_after_delay(limit_message, AUTO_DELETE_DELAY))
    except Exception as e:
        logger.error(f"Error in check_command: {e}")
        error_message = await message.reply_text("An error occurred while checking your limit.")
        asyncio.create_task(delete_message_after_delay(error_message, AUTO_DELETE_DELAY))

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
