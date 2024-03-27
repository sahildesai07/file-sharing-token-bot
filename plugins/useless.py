from bot import Bot


from config import ultroidxTeam_ADMINS, ultroidxTeam_botSTATS, USER_REPLY_TEXT
from datetime import datetime
from helper_func import get_readable_time

import asyncio
import time
from datetime import datetime
from pyrogram import Client, filters, __version__
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import ultroidxTeam_ADMINS, ultroidxTeam_Timeout
from database import full_userbase, db_verify_status

@Bot.on_message(filters.command('stats') & filters.user(ultroidxTeam_ADMINS))
async def stats(bot: Bot, message: Message):
    now = datetime.now()
    delta = now - bot.uptime
    time = get_readable_time(delta.seconds)
    await message.reply(ultroidxTeam_botSTATS.format(uptime=time))


@Bot.on_message(filters.private & filters.incoming)
async def useless(_,message: Message):
    if USER_REPLY_TEXT:
        await message.reply(USER_REPLY_TEXT)


# 1. Total Verify User Data Command (Admin Command)
@Bot.on_message(filters.command('totalverify') & filters.user(ultroidxTeam_ADMINS))
async def total_verify_users(_, message: Message):
    users = await full_userbase()
    total_verified_users = 0
    verified_users_data = []

    for user_id in users:
        verify_status = await db_verify_status(user_id)
        if verify_status['is_verified']:
            total_verified_users += 1
            verified_users_data.append(f"User ID: {user_id}\nVerified Time: {datetime.fromtimestamp(verify_status['verified_time']).strftime('%Y-%m-%d %H:%M:%S')}")

    if verified_users_data:
        await message.reply(f"Total Verified Users: {total_verified_users}\n\nVerified Users Data:\n\n" + "\n\n".join(verified_users_data))
    else:
        await message.reply("No verified users found.")

# 2. Check Info Command (User Command)
@Bot.on_message(filters.command('info') & filters.private)
async def user_info(_, message: Message):
    user_id = message.from_user.id
    verify_status = await db_verify_status(user_id)

    if verify_status['is_verified']:
        verified_time = datetime.fromtimestamp(verify_status['verified_time']).strftime('%Y-%m-%d %H:%M:%S')
        token_timeout = get_readable_time(ultroidxTeam_Timeout - (time.time() - verify_status['verified_time']))
        await message.reply(f"Token Timeout: {token_timeout}\nVerified Time: {verified_time}")
    else:
        await message.reply("You are not verified yet.")

# 3. Deletion Timer Feature
async def delete_message(message: Message, delay: int):
    await asyncio.sleep(delay)
    await message.delete()

@Bot.on_message(filters.private)
async def delete_after_10min(_, message: Message):
    await delete_message(message, 600)  # 600 seconds = 10 minutes

