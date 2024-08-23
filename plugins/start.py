import os
import asyncio
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode , ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant , UserNotParticipant, ChatAdminRequired , RPCError

from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, FORCE_SUB_CHANNEL, REQ_JOIN
from helper_func import encode, decode, get_messages, subscribed
from database.database import add_user, del_user, full_userbase, present_user


FORCE_MSG = "Please request to join our private channel using the link below:\n\n{link}"
START_MSG = "Welcome, {first} {last} {username}!"


@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    try:
        # Step 1: Check if the user is already a member of the channel
        try:
            member_status = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
            if member_status.status in ["member", "administrator", "creator"]:
                # User is already a member
                if not await present_user(user_id):
                    try:
                        await add_user(user_id)
                    except Exception as e:
                        print(f"Error adding user to the database: {e}")
                
                # Proceed with the bot's main functionality
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
                        caption = CUSTOM_CAPTION.format(
                            previouscaption="" if not msg.caption else msg.caption.html,
                            filename=msg.document.file_name
                        ) if bool(CUSTOM_CAPTION) and bool(msg.document) else (msg.caption.html if msg.caption else "")
                        reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None

                        try:
                            await msg.copy(
                                chat_id=message.from_user.id,
                                caption=caption,
                                parse_mode="html",
                                reply_markup=reply_markup,
                                protect_content=PROTECT_CONTENT
                            )
                            await asyncio.sleep(0.5)
                        except FloodWait as e:
                            await asyncio.sleep(e.x)
                            await msg.copy(
                                chat_id=message.from_user.id,
                                caption=caption,
                                parse_mode="html",
                                reply_markup=reply_markup,
                                protect_content=PROTECT_CONTENT
                            )
                        except Exception as e:
                            print(f"Error copying message: {e}")
                else:
                    reply_markup = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("😊 About Me", callback_data="about"),
                            InlineKeyboardButton("🔒 Close", callback_data="close")
                        ]
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
        except UserNotParticipant:
            # User is not a member; prompt them to join the channel
            join_link = await client.create_chat_invite_link(chat_id=FORCE_SUB_CHANNEL)
            buttons = [
                [InlineKeyboardButton("Join Channel", url=join_link.invite_link)],
                [InlineKeyboardButton("I've Joined", callback_data="check_membership")]
            ]
            await message.reply(
                text=FORCE_MSG.format(link=join_link.invite_link),
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True
            )
    
    except RPCError as e:
        await message.reply(f"An error occurred: {e}")

@Bot.on_callback_query(filters.regex("check_membership"))
async def check_membership(client: Client, callback_query):
    user_id = callback_query.from_user.id

    try:
        # Verify if the user has joined the channel
        member_status = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        if member_status.status in ["member", "administrator", "creator"]:
            # Add the user to the bot's database if not already present
            if not await present_user(user_id):
                try:
                    await add_user(user_id)
                except Exception as e:
                    print(f"Error adding user to the database: {e}")
            await callback_query.message.edit_text("Thank you for joining! You now have access to the bot's features.")
            # Proceed with the bot's main functionality if needed
        else:
            await callback_query.answer("You haven't joined the channel yet. Please join to continue.", show_alert=True)
    except UserNotParticipant:
        await callback_query.answer("You haven't joined the channel yet. Please join to continue.", show_alert=True)
    except RPCError as e:
        await callback_query.message.edit_text(f"An error occurred: {e}")

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
