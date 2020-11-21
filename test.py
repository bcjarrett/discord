import re

import discord

from discord.ext import commands
from bs4 import BeautifulSoup

from config import Config
from models import TextCount, Game

import aiohttp

conf = Config()

GUILD = conf['TEST_SERVER']

bot = commands.Bot(command_prefix='?', description='A useless bot', intents=discord.Intents.all())


async def search_game(title, number_results=10, language_code='en'):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/61.0.3163.100 Safari/537.36'}
    google_url = 'https://www.google.com/search?q={}&num={}&hl={}'.format(title.replace(" ", "+") + 'steam game',
                                                                          number_results + 1,
                                                                          language_code)

    async with aiohttp.ClientSession() as session:
        async with session.get(google_url, headers=headers) as r:
            if r.status == 200:
                text = await r.read()

        soup = BeautifulSoup(text, 'html.parser')
        result_block = soup.find_all('div', attrs={'class': 'g'})
        games = []
        for result in result_block:
            link = result.find('a', href=True)
            title = result.find('h3')
            if link and title:
                games.append(link['href'])
        game = games[0]
        if re.search('store\.steampowered\.com\/app\/[0-9]*', game):
            return game
        else:
            return None


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
async def add(ctx, *args):
    """
    Adds a game to the list. Takes an optional parameter URL
        add_game Castle Crashers
        add_game Castle Crashers https://store.steampowered.com/app/204360/Castle_Crashers/
    """

    game_in = list(args)
    url = game_in.pop(-1) if game_in[-1].lower().startswith('http') else None
    name = ' '.join(game_in)
    if not url:
        url = await search_game(name)
    Game.create(name=name, added_by=ctx.author.id, url=url)


@bot.command



@bot.command()
async def test(ctx, *args):
    embed = discord.Embed(
        title='Title',
        colour=discord.Colour(0xE5E242),
        url=f"https://www.kingsmathsschool.com/weekly-maths-challenge/'slug'",
        description='description',
    )

    embed.set_image(url='http://static.cannibalsock.com/img/cannibalsock.png')
    embed.set_thumbnail(
        url="http://static.cannibalsock.com/img/cannibalsock.png"
    )
    embed.set_author(name="King's Maths School")
    embed.set_footer(
        text=f"Challenge Released: date | Category: cat"
    )
    # return await ctx.send(embed=embed)
    return await ctx.send(content='https://store.steampowered.com/app/204360/Castle_Crashers/')


bot.run(conf['API_SECRET'])
