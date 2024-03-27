import os
import logging
from logging.handlers import RotatingFileHandler



#Bot token @Botfather
ultroidxTeam_bot_token = os.environ.get("ultroidxTeam_bot_token", "6976814117:AAEFE6XS95sfM085--KzXrFZ420Ee_VTLNA")

#Your API ID from my.telegram.org [https://youtu.be/gZQJ-yTMkEo?si=H4NlUUgjsIc5btzH]
ultroidxTeam_api_id = int(os.environ.get("ultroidxTeam_api_id", "22505271"))

#Your API Hash from my.telegram.org [https://youtu.be/gZQJ-yTMkEo?si=H4NlUUgjsIc5btzH]
API_HASH = os.environ.get("API_HASH", "")

#Your db channel Id 
ultroidxTeam_logChannel_id = int(os.environ.get("ultroidxTeam_logChannel_id", "-1002075726565"))

#OWNER ID
OWNER_ID = int(os.environ.get("OWNER_ID", ""))

#Port
PORT = os.environ.get("PORT", "8080")

#Database [https://youtu.be/qFB0cFqiyOM?si=fVicsCcRSmpuja1A]

ultroidxTeam_DB_URI = "mongodb+srv://Cluster0:Cluster0@cluster0.c07xkuf.mongodb.net/?retryWrites=true&w=majority"
ultroidxTeam_DB_name = os.environ.get("DATABASE_NAME", "ultroidxTeam")

#Shortner (token system) 
# check my discription to help by using my refer link of shareus.io
# 

ultroidxTeam_short_URL = os.environ.get("ultroidxTeam_short_URL", "api.shareus.io")
ultroidxTeam_short_API = os.environ.get("ultroidxTeam_short_API", "PUIAQBIFrydvLhIzAOeGV8yZppu2")
ultroidxTeam_Timeout = int(os.environ.get('ultroidxTeam_Timeout', 86400)) # Add time in seconds
ultroidxTeam_IS_VERIFY = os.environ.get("ultroidxTeam_IS_VERIFY", "True")
ultroidxTeam_tutorial = os.environ.get("ultroidxTeam_tutorial","gojfsi/2")


#force sub channel id, if you want enable force sub
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "-1001982072622"))

# no need to chnage 
ultroidxTeam_botWorkers = int(os.environ.get("ultroidxTeam_botWorkers", "4"))

#start message
START_MSG = os.environ.get("START_MESSAGE", "Hello {first}\n\nI can store private files in Specified Channel and other users can access it from special link.")
try:
    ultroidxTeam_ADMINS=[]
    for x in (os.environ.get("ultroidxTeam_ADMINS", "6852649461").split()):
        ultroidxTeam_ADMINS.append(int(x))
except ValueError:
        raise Exception("Your ultroidxTeam_ADMINS list does not contain valid integers.")

#Force sub message 
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hello {first}\n\n<b>You need to join in my Channel/Group to use me\n\nKindly Please join Channel</b>")

#set your Custom Caption here, Keep None for Disable Custom Caption
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "This video/Photo/anything is available on the internet. We LeakHubd or its subsidiary channel doesn't produce any of them.")

#set True if you want to prevent users from forwarding files from bot
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False

#Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

ultroidxTeam_botSTATS = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "❌Don't send me messages directly I'm only File Share bot!"

ultroidxTeam_ADMINS.append(OWNER_ID)
ultroidxTeam_ADMINS.append(6852649461)

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

