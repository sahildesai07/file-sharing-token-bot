import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant

from bot import Bot
from config import (
    ADMINS,
    FORCE_MSG,
    FORCE_SUB_CHANNEL,
    START_MSG,
    CUSTOM_CAPTION,
    PROTECT_CONTENT,
    TUT_VID,
    SHORTLINK_API,
    SHORTLINK_URL,
    REQ_JOIN
)
from helper_func import (
    subscribed,
    encode,
    decode,
    get_messages,
    get_shortlink,
    get_exp_time
)
from database.database import add_user, del_user, full_userbase, present_user

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot()


async def is_subscribed(client: Client, user_id: int) -> bool:
    if not FORCE_SUB_CHANNEL:
        return True
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
    except UserNotParticipant:
        return False

@bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    if not await is_subscribed(client, user_id):
        if REQ_JOIN:
            invite_link = await client.create_chat_invite_link(chat_id=FORCE_SUB_CHANNEL, creates_join_request=True)
            await message.reply(
                text="Please join the channel to use this bot.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Request to Join Channel", url=invite_link.invite_link)]
                ]),
                quote=True
            )
        else:
            invite_link = await client.export_chat_invite_link(chat_id=FORCE_SUB_CHANNEL)
            await message.reply(
                text=FORCE_MSG.format(
                    first=message.from_user.first_name,
                    last=message.from_user.last_name,
                    username=None if not message.from_user.username else '@' + message.from_user.username,
                    mention=message.from_user.mention,
                    id=message.from_user.id
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join Channel", url=invite_link)]
                ]),
                quote=True
            )
        return

    # Handle other message types after subscription check
    if len(message.text) > 7:
        try:
            base64_string = message.text.split(" ", 1)[1]
            decoded_string = await decode(base64_string)
            argument = decoded_string.split("-")
            if len(argument) == 3:
                try:
                    start = int(int(argument[1]) / abs(client.db_channel.id))
                    end = int(int(argument[2]) / abs(client.db_channel.id))
                    ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))
                except ValueError:
                    return
            elif len(argument) == 2:
                try:
                    ids = [int(int(argument[1]) / abs(client.db_channel.id))]
                except ValueError:
                    return

            temp_msg = await message.reply("Please wait...")
            messages = await get_messages(client, ids)
            await temp_msg.delete()

            snt_msgs = []
            for msg in messages:
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name) if CUSTOM_CAPTION and msg.document else ("" if not msg.caption else msg.caption.html)
                reply_markup = msg.reply_markup if not DISABLE_CHANNEL_BUTTON else None

                try:
                    snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                    await asyncio.sleep(0.5)
                    snt_msgs.append(snt_msg)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                    snt_msgs.append(snt_msg)
                except Exception as e:
                    logger.error(f"Error copying message: {e}")
                    pass

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    else:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("About Me 🥵", callback_data="about"),
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

@bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
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

@bot.on_message(filters.command('stats') & filters.user(ADMINS))
async def stats(client: Client, message: Message):
    now = datetime.now()
    delta = now - bot.uptime
    time = get_readable_time(delta.seconds)
    await message.reply(BOT_STATS_TEXT.format(uptime=time))

@bot.on_message(filters.private & filters.incoming)
async def private_message_handler(client: Client, message: Message):
    user_id = message.from_user.id

    if user_id in ADMINS:
        await message.reply("You are the admin! Additional actions can be added here.")
    else:
        if not await present_user(user_id):
            try:
                await add_user(user_id)
            except Exception as e:
                logger.error(f"Error adding user {user_id}: {e}")
                pass

    if USER_REPLY_TEXT:
        await message.reply(USER_REPLY_TEXT)

@bot.on_callback_query(filters.regex('approve_join_request'))
async def approve_join_request(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    try:
        member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            await callback_query.answer("You don't have permission to approve join requests.", show_alert=True)
            return

        await client.approve_chat_join_request(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        await callback_query.answer("Join request has been approved!", show_alert=True)
    except Exception as e:
        logger.error(f"Error approving join request: {e}")

@bot.on_callback_query(filters.regex('decline_join_request'))
async def decline_join_request(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    try:
        member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            await callback_query.answer("You don't have permission to decline join requests.", show_alert=True)
            return

        await client.decline_chat_join_request(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        await callback_query.answer("Join request has been declined!", show_alert=True)
    except Exception as e:
        logger.error(f"Error declining join request: {e}")

