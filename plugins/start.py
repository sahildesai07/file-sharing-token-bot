import os
import asyncio
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, RPCError
from pymongo import MongoClient
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT
from helper_func import encode, decode, get_messages
from database.database import add_user, del_user, full_userbase, present_user

# Define your channel username or ID and join link
FORCE_SUB_CHANNEL = -1002043373014  # Replace with your channel ID
REQ_JOIN_LINK = 'https://t.me/+CtzZboehkKBmNmFk'  # Replace with your channel join link

# MongoDB setup
MONGO_URL = 'mongodb+srv://Cluster0:Cluster0@cluster0.c07xkuf.mongodb.net/?retryWrites=true&w=majority'
mongo_client = MongoClient(MONGO_URL)
db = mongo_client['yose_name']  # Replace with your database name
collection = db['join_requests']  # Replace with your collection name

#Bot = Client("my_bot")

async def check_subscription_status(client: Client, user_id: int):
    try:
        # Check if the user is a member of the channel
        member_status = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        if member_status.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
    except RPCError:
        pass

    # Check MongoDB if the user has a pending request
    existing_request = collection.find_one({"user_id": user_id, "chat_id": FORCE_SUB_CHANNEL})
    if existing_request:
        return True

    return False

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    if not await check_subscription_status(client, user_id):
        await message.reply(
            text="You need to join the channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=REQ_JOIN_LINK)]
            ]),
            quote=True
        )
        return

    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except Exception as e:
            print(f"Error adding user to database: {e}")

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
            except ValueError:
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = list(range(start, end - 1, -1))
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except ValueError:
                return

        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except Exception:
            await message.reply_text("Something went wrong..!")
            return
        await temp_msg.delete()

        for msg in messages:
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None

            try:
                await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
            except Exception:
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
        return

@Bot.on_chat_join_request(filters.chat(FORCE_SUB_CHANNEL))
async def handle_join_request(client: Client, chat_join_request: ChatJoinRequest):
    user_id = chat_join_request.user.id

    user_data = {
        "user_id": user_id,
        "chat_id": FORCE_SUB_CHANNEL,
        "timestamp": chat_join_request.date
    }

    try:
        print(f"Handling join request for user {user_id}...")

        # Check if the user is already a member of the channel
        try:
            member_status = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
            if member_status.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                await client.send_message(
                    chat_id=user_id,
                    text="You are already a member of the channel."
                )
                return
        except RPCError as e:
            print(f"Error checking member status: {e}")
            pass

        # Check MongoDB if the user has a pending request
        existing_request = collection.find_one({"user_id": user_id, "chat_id": FORCE_SUB_CHANNEL})
        if existing_request:
            await client.send_message(
                chat_id=user_id,
                text="Your join request is already pending or has been processed."
            )
            print(f"User {user_id} has an existing request. Data retrieved from MongoDB.")
            return

        # Send the join link if the user is neither in pending nor a member
        await client.send_message(
            chat_id=user_id,
            text="Please join the channel using the link below.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=REQ_JOIN_LINK)]
            ])
        )
        print(f"Sent join link to user {user_id}.")

        # Insert a record into MongoDB for tracking
        collection.insert_one(user_data)
        print(f"Recorded user {user_id} join request data in MongoDB.")

    except Exception as e:
        print(f"An error occurred: {e}")
        await client.send_message(chat_id=user_id, text=f"An error occurred: {e}")

# Additional functionality for handling broadcasts and user management
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
#Bot.run()
