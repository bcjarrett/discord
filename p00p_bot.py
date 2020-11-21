import random

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


@bot.event
async def on_message(message):
    if random.randint(1, 70) == 69:
        if str(message.author) == conf["p00c"]:
            _ = ''
            a = TextCount.get(text='p00p')
            for i in range(a.counter):
                _ += 'p00p '
            await message.channel.send(_)
            a.counter += 1
            a.save()


bot.run(conf['API_SECRET'])
