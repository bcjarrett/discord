import logging.config
import sys

import discord
from discord.ext import commands

from config import conf
from database import db_setup

logging.config.dictConfig(conf['LOGGING_CONFIG'])
logger = logging.getLogger('dheads')


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, Exception):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

logger.info('Setting up Database')
db_setup()

TOKEN = conf['API_SECRET']

bot = commands.Bot(command_prefix='?',
                   description='Keeps track of games to play among other things. \n'
                               'https://github.com/bcjarrett/discord',
                   intents=discord.Intents.all())

if __name__ == '__main__':
    for extension in conf['COGS']:
        bot.load_extension(f'{extension}.cog')

bot.run(TOKEN, bot=True)
