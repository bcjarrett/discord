import discord
from discord.ext import commands

from config import Config
from models import TextCount, Game

conf = Config()

GUILD = conf['TEST_SERVER']

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
    a = TextCount.get(text='butt')
    a.counter = 1
    a.save()


@bot.command(description='Add a game to the list')
async def add_game(ctx, *args):
    """
    Adds a game to the list. Takes an optional parameter URL
        add_game Castle Crashers
        add_game Castle Crashers https://store.steampowered.com/app/204360/Castle_Crashers/
    """

    game_in = list(args)
    url = game_in.pop(-1) if game_in[-1].lower().startswith('http') else None
    name = ' '.join(game_in)
    Game.create(name=name, added_by=ctx.author.id, url=url)


bot.run(conf['API_SECRET'])
