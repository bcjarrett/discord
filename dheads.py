import discord
from discord.ext import commands

from config import conf

TOKEN = conf['API_SECRET']

initial_extensions = [
    'cogs.p00p',
    'cogs.game_tracker',
]

bot = commands.Bot(command_prefix='?',
                   description='Keeps track of games to play and occasionally p00ps. \n'
                               'https://github.com/bcjarrett/discord',
                   intents=discord.Intents.all())

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    print(f'\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    print(f'Connected to {[g.name for g in bot.guilds]}')
    await bot.change_presence(activity=discord.Game(name="Oblivion"))


bot.run(TOKEN, bot=True)
