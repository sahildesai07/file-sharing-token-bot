
from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCE_SUB_CHANNEL, CHANNEL_ID, PORT

# modified by @ultroidxTeam (TG)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        try:
            await super().start()
            usr_bot_me = await self.get_me()
            self.uptime = datetime.now()

            for i in range(1, 5):
                force_sub_channel = globals().get(f"FORCE_SUB_CHANNEL_{i}")
                if force_sub_channel:
                    await self.handle_force_sub_channel(i, force_sub_channel)

            await self.test_db_channel()

            self.set_parse_mode(ParseMode.HTML)
            self.LOGGER(__name__).info("Bot Running..!")
            self.LOGGER(__name__).info(f""" \n\n       
(っ◔◡◔)っ ♥ ULTROIDOFFICIAL ♥
░╚════╝░░╚════╝░╚═════╝░╚════╝░
                                          """)
            # Start web server
            await self.start_web_server()

        except Exception as e:
            self.LOGGER(__name__).error(f"Error during bot startup , need help ? t.me/ultroidofficial_chat: {e}")
            sys.exit(1)

    async def handle_force_sub_channel(self, idx, force_sub_channel):
        try:
            link = (await self.get_chat(force_sub_channel)).invite_link
            if not link:
                await self.export_chat_invite_link(force_sub_channel)
                link = (await self.get_chat(force_sub_channel)).invite_link
            setattr(self, f"invitelink{idx}", link)
        except Exception as e:
            self.LOGGER(__name__).warning(f"Error handling FORCE_SUB_CHANNEL_{idx} , need help ? t.me/ultroidofficial_chat : {e}")

    async def test_db_channel(self):
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            test_msg = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test_msg.delete()
            self.db_channel = db_channel
        except Exception as e:
            self.LOGGER(__name__).warning(f"Error testing DB channel , need help ? t.me/ultroidofficial_chat: {e}")

    async def start_web_server(self):
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        try:
            await super().stop()
            self.LOGGER(__name__).info("Bot stopped.")
        except Exception as e:
            self.LOGGER(__name__).error(f"Error while stopping bot , need help ? t.me/ultroidofficial_chat : {e}")
