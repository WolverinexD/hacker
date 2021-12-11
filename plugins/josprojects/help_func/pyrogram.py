import logging

from pyrogram import Client

# from pyromod import listen
from plugins.josprojects.help_func import environ

SESSION = environ.get('SESSION', 'Media_search')
API_ID = int(environ['API_ID'])
API_HASH = environ['API_HASH']
BOT_TOKEN = environ['BOT_TOKEN']
pbot = Client(
    session_name,
    api_id=APP_ID,
    api_hash=APP_HASH,
    bot_token=TOKEN,
)

# disable logging for pyrogram [not for ERROR logging]
logging.getLogger("pyrogram").setLevel(level=logging.ERROR)

pbot.start()
