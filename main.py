import asyncio
import configparser
from Bot_view.bot_polling import BotHandlers

config = configparser.ConfigParser()
try:
    config.read("./Settings/config.ini")
except:
    config.read("./../Settings/config.ini")
token = config['Localmachine_Bot']['token']

# if __name__ == '__main__':
bot_handlers = BotHandlers(token)
asyncio.run(bot_handlers.handlers())