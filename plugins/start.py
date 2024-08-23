import os
import asyncio
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode , ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton , ParseMode
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant , UserNotParticipant, ChatAdminRequired , RPCError

from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, FORCE_SUB_CHANNEL, REQ_JOIN
from helper_func import encode, decode, get_messages, subscribed
from database.database import add_user, del_user, full_userbase, present_user


FORCE_MSG = "Please request to join our private channel using the link below:\n\n{link}"
START_MSG = "Welcome, {first} {last} {username}!"

# Generate a join request link
async def generate_join_request_link(client):
    chat = await client.get_chat(FORCE_SUB_CHANNEL)
    link = await client.create_chat_invite_link(chat.id, member_limit=1)
    return link.invite_link

# Check if the user has a pending join request
async def is_join_request_pending(client, user_id):
    try:
        join_requests = await client.get_chat_join_requests(chat_id=FORCE_SUB_CHANNEL)
        for request in join_requests:
            if request.user.id == user_id:
                return True
        return False
    except RPCError as e:
        print(f"Error fetching join requests: {e}")
        return False

# Start command logic if the user’s join request is pending
@app.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    if await is_join_request_pending(client, user_id):
        if not await present_user(user_id):
            try:
                await add_user(user_id)
            except Exception as e:
                print(f"Error adding user: {e}")
        
        text = message.text
        if len(text) > 7:
            try:
                base64_string = text.split(" ", 1)[1]
            except IndexError:
                return

            # Assuming decode and get_messages are defined elsewhere
            string = await decode(base64_string)
            argument = string.split("-")
            if len(argument) == 3:
                try:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                except ValueError:
                    return
                
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
            elif len(argument) == 2:
                try:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                except ValueError:
                    return

            temp_msg = await message.reply("Please wait...")
            try:
                messages = await get_messages(client, ids)
            except Exception as e:
                await message.reply_text("Something went wrong..!")
                return
            
            await temp_msg.delete()

            for msg in messages:
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name) if bool(CUSTOM_CAPTION) & bool(msg.document) else "" if not msg.caption else msg.caption.html
                reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None

                try:
                    await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                    await asyncio.sleep(0.5)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                except Exception as e:
                    print(f"Error copying message: {e}")
        else:
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("😊 About Me", callback_data="about"),
                 InlineKeyboardButton("🔒 Close", callback_data="close")]
            ])
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
    else:
        join_request_link = await generate_join_request_link(client)
        buttons = [
            [InlineKeyboardButton("Request to Join", url=join_request_link),
             InlineKeyboardButton("Try Again", url=f"https://t.me/{client.username}?start={message.command[1]}")]
        ]
        await message.reply(
            text=FORCE_MSG.format(link=join_request_link),
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
            except Exception as e:
                unsuccessful += 1
                print(f"Error broadcasting message to {chat_id}: {e}")
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
