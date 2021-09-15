import logging.config
import sys

import discord
from discord.ext import commands

from config import conf
from database import db_setup
from mgmt.cog import reset_message
from mgmt.models import Reset

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


@bot.event
async def on_ready():
    logger.info(f'\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    logger.info(f'Connected to {[g.name for g in bot.guilds]}')

    # Figure out where we want to send the "booted up" message
    try:
        channel_id = Reset.select().order_by(Reset.added_on.desc()).first().channel_id
        channel = bot.get_channel(channel_id)
        last_msg = await channel.history().find(lambda m: m.author.id == bot.user.id)
        startup_msg = 'Successfully Started Up :thumbsup:'
        if last_msg.clean_content == reset_message:
            await last_msg.edit(content=startup_msg)
        else:
            await channel.send(startup_msg)
    except AttributeError:
        pass

    await bot.change_presence(activity=discord.Game(name="Oblivion"))


bot.run(TOKEN, bot=True)
