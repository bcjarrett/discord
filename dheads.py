import discord
from discord.ext import commands

from config import conf
from database import db_setup
from mgmt.cog import reset_message
from mgmt.models import Reset

db_setup()

TOKEN = conf['API_SECRET']

bot = commands.Bot(command_prefix='?',
                   description='Keeps track of games to play and occasionally p00ps. \n'
                               'https://github.com/bcjarrett/discord',
                   intents=discord.Intents.all())

if __name__ == '__main__':
    for extension in conf['COGS']:
        bot.load_extension(f'{extension}.cog')


@bot.event
async def on_ready():
    print(f'\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    print(f'Connected to {[g.name for g in bot.guilds]}')

    # Figure out where we want to send the "booted up" message
    channel_id = Reset.select().order_by(Reset.added_on.desc()).first().channel_id
    channel = bot.get_channel(channel_id)
    last_msg = await channel.history().find(lambda m: m.author.id == bot.user.id)
    startup_msg = 'Successfully Started Up :thumbsup:'
    if last_msg.clean_content == reset_message:
        await last_msg.edit(content=startup_msg)
    else:
        await channel.send(startup_msg)

    await bot.change_presence(activity=discord.Game(name="Oblivion"))


bot.run(TOKEN, bot=True)
