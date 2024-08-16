import sys
import glob
import importlib
from pathlib import Path
from pyrogram import idle
import logging
import logging.config
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from Script import script 
from datetime import date, datetime 
import pytz
from aiohttp import web
from PhdLust.server import web_server
import asyncio
from plugins.clone import restart_bots
from PhdLust.bot import StreamBot
from PhdLust.utils.keepalive import ping_server
from PhdLust.bot.clients import initialize_clients

# Logging configurations
logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

ppath = "plugins/*.py"
files = glob.glob(ppath)
StreamBot.start()
loop = asyncio.get_event_loop()

async def start():
    logger.info("Initializing PhdLust Bot...")
    try:
        bot_info = await StreamBot.get_me()
        StreamBot.username = bot_info.username
        logger.info(f"Bot username: {StreamBot.username}")
        
        await initialize_clients()
        logger.info("Clients initialized successfully.")
        
        for name in files:
            try:
                with open(name) as a:
                    patt = Path(a.name)
                    plugin_name = patt.stem.replace(".py", "")
                    plugins_dir = Path(f"plugins/{plugin_name}.py")
                    import_path = "plugins.{}".format(plugin_name)
                    spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
                    load = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(load)
                    sys.modules["plugins." + plugin_name] = load
                    logger.info(f"Plugin imported: {plugin_name}")
            except Exception as e:
                logger.error(f"Failed to import plugin {plugin_name}: {e}")

        if ON_HEROKU:
            asyncio.create_task(ping_server())
            logger.info("Ping server task created for Heroku.")

        me = await StreamBot.get_me()
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")
        app = web.AppRunner(await web_server())
        await StreamBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        logger.info(f"Web server started at {bind_address}:{PORT}")

        if CLONE_MODE:
            await restart_bots()
            logger.info("Clone mode enabled and bots restarted.")
        
        logger.info("Bot Started Powered By @ultroid_Official")
        await idle()
        
    except Exception as e:
        logger.error(f"Error during bot startup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logger.info("Service Stopped. Bye 👋")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
