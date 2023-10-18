import asyncio
import configparser
from Bot_view.bot_polling import BotHandlers

config = configparser.ConfigParser()
config.read("./settings/config.ini")
token = config['Bot']['token']

if __name__ == '__main__':
    bot_handlers = BotHandlers(token)
    asyncio.run(bot_handlers.handlers())