import discord
from discord.ext import commands

from config import Config
from models import TextCount

conf = Config()

GUILD = conf['DHEADS']

bot = commands.Bot(command_prefix='?', description='A useless bot', intents=discord.Intents.all())


@bot.event
async def on_ready():
    for guild in bot.guilds:
        if guild.id != GUILD:
            bot._connection._remove_guild(guild)
    guild = bot.get_guild(GUILD)

    print(
        f'{bot.user} is only connected to:\n'
        f'{guild.name}(id: {guild.id})\n'
    )


@bot.command(description='Clear p00p counter')
async def clear(ctx):
    """Clears the p00p count"""
    a = TextCount.get(text='p00p')
    a.counter = 1
    a.save()


bot.run(conf['API_SECRET'])
