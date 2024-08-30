import asyncio
import base64
import logging
import os
import random
import string
from datetime import datetime, timedelta
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import *
from helper_func import subscribed, encode, decode, get_messages
from database.database import (
    log_verification, get_verification_count, cleanup_old_logs, present_user,
    get_previous_token, set_previous_token, del_user, full_userbase, add_user,
    get_user_limit, update_user_limit, store_token, verify_token, user_collection,
    token_collection
)
import uuid
from shortzy import Shortzy

# Initialize Shortzy
shortzy = Shortzy(api_key=SHORTLINK_API, base_site=SHORTLINK_URL)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_shortlink(url, api, link):
    try:
        verification_link = await shortzy.convert(link)
        return verification_link
    except Exception as e:
        logger.error(f"Error generating short link: {str(e)}")
        return link

async def delete_message_after_delay(message: Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")

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
		
@Client.on_message(filters.command('count') & filters.private)
async def count_command(client: Client, message: Message):
    try:
        # Get the count of users who used a token in the last 24 hours
        last_24h_count = await get_verification_count("24h")

        # Get the count of users who used a token today
        today_count = await get_verification_count("today")

        count_message = (
            f"Token usage stats:\n"
            f"Last 24 hours: {last_24h_count} users\n"
            f"Today's token users: {today_count} users"
        )
        
        response_message = await message.reply_text(count_message)
        asyncio.create_task(delete_message_after_delay(response_message, AUTO_DELETE_DELAY))

    except Exception as e:
        logger.error(f"Error in count_command: {e}")
        error_message = await message.reply_text("An error occurred while retrieving count data.")
        asyncio.create_task(delete_message_after_delay(error_message, AUTO_DELETE_DELAY))

@Client.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    # Ensure user exists in the database
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except Exception as e:
            logger.error(f"Error adding user: {e}")

    # Retrieve user data
    user_data = await user_collection.find_one({"_id": user_id})
    user_limit = user_data.get("limit", START_COMMAND_LIMIT)
    previous_token = user_data.get("previous_token")

    # Generate a new token only if previous_token is not available
    if not previous_token:
        previous_token = str(uuid.uuid4())
        await user_collection.update_one({"_id": user_id}, {"$set": {"previous_token": previous_token}}, upsert=True)

    # Generate the verification link
    verification_link = f"https://t.me/{client.username}?start=verify_{previous_token}"
    shortened_link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, verification_link)

    # Check if the user is providing a verification token
    if len(message.text) > 7 and "verify_" in message.text:
        provided_token = message.text.split("verify_", 1)[1]
        if provided_token == previous_token:
            # Verification successful, increase limit by 10
            await update_user_limit(user_id, user_limit + LIMIT_INCREASE_AMOUNT)
            await log_verification(user_id)
            confirmation_message = await message.reply_text("Your limit has been successfully increased by 10! , use /check cmd check your credits")
            asyncio.create_task(delete_message_after_delay(confirmation_message, AUTO_DELETE_DELAY))
            return
        else:
            error_message = await message.reply_text("Invalid verification token. Please try again.")
            asyncio.create_task(delete_message_after_delay(error_message, AUTO_DELETE_DELAY))
            return

    # If the limit is reached, prompt the user to use the verification link
    if user_limit <= 0:
        limit_message = "Your limit has been reached , use /check cmd check your credits. Use the following link to increase your limit "
        buttons = []

        try:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text='Increase LIMIT',
                        url=shortened_link
                    )
                ]
            )
        except IndexError:
            logger.error("IndexError: message.command[1] is missing or invalid")

        # Ensure message.command has at least 2 elements before accessing message.command[1]
        try:
            try_again_button = InlineKeyboardButton(
                'Try Again',
                url=f"https://t.me/{client.username}?start=default"
            )
            buttons.append([try_again_button])
        except IndexError:
            logger.error("IndexError: message.command[1] is missing or invalid")
            buttons.append(
                [
                    InlineKeyboardButton('Try Again', url=f"https://t.me/{client.username}?start=default")
                ]
            )

        buttons.append(
            [
                InlineKeyboardButton('Verification Tutorial', url=TUT_VID)
            ]
        )
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(limit_message, reply_markup=reply_markup, protect_content=False, quote=True)
        asyncio.create_task(delete_message_after_delay(message, AUTO_DELETE_DELAY))
        return

    # Deduct 1 from the user's limit and continue with the normal start command process
    await update_user_limit(user_id, user_limit - 1)

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except IndexError:
            return
        
        string = await decode(base64_string)
        argument = string.split("-")
        
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except Exception as e:
                logger.error(f"Error parsing arguments: {e}")
                return
            
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = list(range(start, end - 1, -1))
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                logger.error(f"Error parsing arguments: {e}")
                return
        
        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await message.reply_text("Something went wrong..!")
            logger.error(f"Error getting messages: {e}")
            return
        
        await temp_msg.delete()

        for msg in messages:
            caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html,
                                            filename=msg.document.file_name) if bool(CUSTOM_CAPTION) & bool(msg.document) else "" if not msg.caption else msg.caption.html

            reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None

            try:
                sent_message = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                asyncio.create_task(delete_message_after_delay(sent_message, AUTO_DELETE_DELAY))
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                sent_message = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                asyncio.create_task(delete_message_after_delay(sent_message, AUTO_DELETE_DELAY))
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



#=========================================================================================##

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



