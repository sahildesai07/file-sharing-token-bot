import os
import logging
from logging.handlers import RotatingFileHandler

START_COMMAND_LIMIT = 15  # Default limit for new users
LIMIT_INCREASE_AMOUNT = 10  # Amount by which the limit is increased after verification
AUTO_DELETE_DELAY = 600  # Time in seconds after which messages will be deleted (600 seconds = 10 minutes)

#Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "7130558359zEJz_JUK8s5DWzv-bRFiLVrX4")

#Your API ID & API HASH from my.telegram.org [https://youtu.be/gZQJ-yTMkEo?si=H4NlUUgjsIc5btzH]
#Your API ID from my.telegram.org
APP_ID = int(os.environ.get("APP_ID", "22505271"))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "c89a94fcfda4bc06524d0903977fc81e")

#Your db channel Id
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002043373014"))

#OWNER ID
OWNER_ID = int(os.environ.get("OWNER_ID", "6695586027"))

#Port
PORT = os.environ.get("PORT", "8080")

#Database 
#Database [https://youtu.be/qFB0cFqiyOM?si=fVicsCcRSmpuja1A]
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://Cluster0:Cluster0@cluster0.c07xkuf.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = os.environ.get("DATABASE_NAME", "test")
DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb+srv://Cluster0:Cluster0@cluster0.c07xkuf.mongodb.net/?retryWrites=true&w=majority")

#force sub channel id, if you want enable force sub
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "0"))
FORCE_SUB_CHANNEL2 = int(os.environ.get("FORCE_SUB_CHANNEL2", "0"))
FORCE_SUB_CHANNEL3 = int(os.environ.get("FORCE_SUB_CHANNEL3", "0"))
FORCE_SUB_CHANNEL4 = int(os.environ.get("FORCE_SUB_CHANNEL4", "0"))

#Shortner (token system) 
# check my discription to help by using my refer link of shareus.io

SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "api.shareus.io") 
SHORTLINK_API = os.environ.get("SHORTLINK_API", "PUIAQBIFrydvLhIzAOeGV8yZppu2")
VERIFY_EXPIRE = int(os.environ.get('VERIFY_EXPIRE', 86400)) # Add time in seconds
IS_VERIFY = os.environ.get("IS_VERIFY", "True")
TUT_VID = os.environ.get("TUT_VID", "https://t.me/Ultroid_Official/18")



TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

#start message
START_MSG = os.environ.get("START_MESSAGE", "Hello {first}\n\nI can store private files in Specified Channel and other users can access it from special link.")
try:
    ADMINS=[]
    for x in (os.environ.get("ADMINS", "6695586027 7125905015").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")

# In your config.py or at the top of your script
# REQ_JOIN = True  # or False, depending on your requirement
REQ_JOIN = os.environ.get("REQ_JOIN", True)


#Force sub message 
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hello {first}\n\n<b>You need to join in my Channel/Group to use me\n\nKindly Please join Channel</b>")

#set your Custom Caption here, Keep None for Disable Custom Caption
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)

#set True if you want to prevent users from forwarding files from bot
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False

#Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "❌Don't send me messages directly I'm only File Share bot!"

ADMINS.append(OWNER_ID)
ADMINS.append(6695586027)

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
