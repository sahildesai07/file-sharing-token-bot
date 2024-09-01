# ultroidofficial : YT

from pyrogram import __version__, Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode
from bot import Bot
from config import OWNER_ID, ADMINS, CHANNEL, SUPPORT_GROUP
from database.database import full_userbase
from plugins.start import get_today_token_count, get_total_token_count, get_user_token_count

@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    if data == "about":
        await query.message.edit_text(
            text=f"<b>○ Creator : <a href='tg://user?id={OWNER_ID}'>This Person</a>\n"
                 f"○ Language : <code>Python3</code>\n"
                 f"○ Library : <a href='https://docs.pyrogram.org/'>Pyrogram asyncio {__version__}</a>\n"
                 f"○ Source Code : <a href='https://youtu.be/BeNBEYc-q7Y'>Click here</a>\n"
                 f"○ Channel : @{CHANNEL}\n"
                 f"○ Support Group : @{SUPPORT_GROUP}</b>",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ]
            )
        )
    elif data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except Exception as e:
            print(f"Error deleting reply-to message: {e}")
    elif data == "check_tokens":
        user_id = query.from_user.id
        is_admin = user_id in ADMINS

        # Fetch token counts
        today_tokens = await get_today_token_count()
        total_tokens = await get_total_token_count()
        user_tokens = await get_user_token_count(user_id)

        if is_admin:
            # For admins, optionally display more detailed stats
            users = await full_userbase()
            user_token_details = ""
            for user in users[:100]:  # Limit to first 100 users for brevity
                tokens = await get_user_token_count(user)
                user_token_details += f"User ID: {user} - Tokens: {tokens}\n"
            response = (
                f"<b>🔹 Admin Token Statistics 🔹</b>\n\n"
                f"<b>Today's Token Count:</b> {today_tokens}\n"
                f"<b>Total Token Count:</b> {total_tokens}\n\n"
                f"<b>Top Users:</b>\n{user_token_details}"
            )
        else:
            # For regular users
            response = (
                f"<b>📊 Your Token Statistics 📊</b>\n\n"
                f"<b>Today's Token Count:</b> {today_tokens}\n"
                f"<b>Total Token Count:</b> {total_tokens}\n"
                f"<b>Your Token Count:</b> {user_tokens}"
            )

        await query.answer()
        await query.message.edit_text(
            text=response,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Close", callback_data="close")]]
            )
        )
