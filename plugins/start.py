import asyncio
import logging
import random
import string
import time

from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

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
    OWNER_ID,
    TOKEN_VERIFICATION,
    CREDITS_REQUIRED,
    CREDIT_LINK
)
from helper_func import subscribed, encode, decode, get_messages, get_shortlink, get_verify_status, update_verify_status, get_exp_time
from database.database import (
    add_user, del_user, full_userbase, present_user, db_verify_status, db_update_verify_status,
    db_get_credits, db_decrement_credits, db_add_credits
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
async def auto_delete_message(message_id, chat_id):
    await asyncio.sleep(600)  # 10 minutes
    try:
        await Bot.delete_messages(chat_id, message_id)
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")

async def decrement_credits(user_id):
    # Decrement credits in the database
    await db_decrement_credits(user_id)
"""

async def provide_credits_link(message: Message):
    link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, CREDIT_LINK)
    await message.reply(
        f"Your credits have finished. Please use the following link to get more credits:\n{link}",
        disable_web_page_preview=True,
        quote=True
    )

@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    owner_id = ADMINS  # Fetch the owner's ID from config

    if not await present_user(id):
        try:
            await add_user(id)
        except Exception as e:
            logger.error(f"Failed to add user: {e}")

    verify_status = await db_verify_status(id)
    credits = await db_get_credits(id)  # Check user's credits

    if credits <= 0:
        await provide_credits_link(message)
        return

    if verify_status['is_verified'] and VERIFY_EXPIRE < (time.time() - verify_status['verified_time']):
        await db_update_verify_status(id, is_verified=False)

    if "verify_" in message.text:
        _, token = message.text.split("_", 1)
        if verify_status['verify_token'] != token:
            return await message.reply("Your token is invalid or expired. Try again by clicking /start")
        await db_update_verify_status(id, is_verified=True, verified_time=time.time())
        if verify_status["link"] == "":
            reply_markup = None
        await message.reply(f"Your token has been successfully verified and is valid for: 24 Hours", reply_markup=reply_markup, protect_content=False, quote=True)

    elif len(message.text) > 7 and verify_status['is_verified']:
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
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                await asyncio.sleep(0.5)
                snt_msgs.append(snt_msg)
                asyncio.create_task(auto_delete_message(snt_msg.message_id, snt_msg.chat.id))
                await decrement_credits(id)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                snt_msgs.append(snt_msg)
                asyncio.create_task(auto_delete_message(snt_msg.message_id, snt_msg.chat.id))
                await decrement_credits(id)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                pass

    elif verify_status['is_verified']:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("About Me", callback_data="about"),
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

    else:
        verify_status = await db_verify_status(id)
        if IS_VERIFY and not verify_status['is_verified']:
            short_url = f"adrinolinks.in"
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            await db_update_verify_status(id, verify_token=token, link="")
            link = await get_shortlink(SHORTLINK_URL, SHORTLINK_API, f'https://telegram.dog/{client.username}?start=verify_{token}')
            btn = [
                [InlineKeyboardButton("Click here", url=link)],
                [InlineKeyboardButton('How to use the bot', url=TUT_VID)]
            ]
            await message.reply(f"Your Ads token is expired, refresh your token and try again.\n\nToken Timeout: {get_exp_time(VERIFY_EXPIRE)}\n\nWhat is the token?\n\nThis is an ads token. If you pass 1 ad, you can use the bot for 24 hours after passing the ad.", reply_markup=InlineKeyboardMarkup(btn), protect_content=False, quote=True)

@Bot.on_message(filters.command('credit') & filters.private)
async def credit_command(client: Client, message: Message):
    id = message.from_user.id
    credits = await db_get_credits(id)

    if credits is not None:
        await message.reply(
            f"Your current credit balance is: {credits} credits.\n\nIf you need more credits, use the following link to purchase or earn more:\n{CREDIT_LINK}",
            disable_web_page_preview=True,
            quote=True
        )
    else:
        await message.reply("An error occurred while retrieving your credit information. Please try again later.", quote=True)

async def auto_delete_message(client: Client, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id=client.me.id, message_ids=message_id)
    except Exception as e:
        logging.error(f"Failed to delete message: {e}")

#=====================================================================================##

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a reply to any telegram message without any spaces.</code>"""

#=====================================================================================##

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [InlineKeyboardButton(text="Join Channel", url=client.invitelink)],
        [InlineKeyboardButton(text="Join Channel", url=client.invitelink3)]
    ]
    try:
        buttons.append(
            [InlineKeyboardButton(
                text='Try Again',
                url=f"https://t.me/{client.username}?start={message.command[1]}"
            )]
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
        
        status = f"""<b>Broadcast Completed</b>\n
        <b>Total Users:</b> {total}\n
        <b>Successful:</b> {successful}\n
        <b>Blocked:</b> {blocked}\n
        <b>Deleted:</b> {deleted}\n
        <b>Unsuccessful:</b> {unsuccessful}
        """
        await pls_wait.edit(status)

