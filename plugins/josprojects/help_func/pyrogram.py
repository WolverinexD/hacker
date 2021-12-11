import logging
import re
from os import environ
from pyrogram import Client

# from pyromod import listen
from plugins.josprojects.help_func import environ


BOT_TOKEN = get_str_key("BOT_TOKEN", required=True)
APP_ID = get_int_key("APP_ID", required=True)
APP_HASH = get_str_key("APP_HASH", required=True)
session_name = BOT_TOKEN.split(":")[0]
pbot = Client(
    session_name,
    api_id=APP_ID,
    api_hash=APP_HASH,
    bot_token=TOKEN,
)

# disable logging for pyrogram [not for ERROR logging]
logging.getLogger("pyrogram").setLevel(level=logging.ERROR)

pbot.start()
