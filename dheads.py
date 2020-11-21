import random
import re
from datetime import datetime, timedelta

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands

from config import Config
from models import Game, TextCount

conf = Config()

GUILD = conf['DHEADS']

bot = commands.Bot(command_prefix='?',
                   description='Keeps track of games to play and occasionally p00ps',
                   intents=discord.Intents.all())

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/61.0.3163.100 Safari/537.36'}


async def search_game(title, number_results=10, language_code='en'):
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


async def game_name_from_steam_id(steam_id):
    url = f'https://store.steampowered.com/app/{steam_id}/'
    app_class = 'apphub_AppName'

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if r.status == 200:
                text = await r.read()

        soup = BeautifulSoup(text, 'html.parser')
        app_name_div = soup.find('div', attrs={'class': app_class})
        if app_name_div:
            return app_name_div.text
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
    """Resets the p00p count"""
    a = TextCount.get(text='p00p')
    a.counter = 1
    a.save()
    return await ctx.send('Back to one p00p :cry:')


@bot.command(description='Add a game to the list')
async def add(ctx, *args):
    """
    Adds a game to the list. Searches steam if no URL is provided.
        add Castle Crashers
        add Castle Crashers https://store.steampowered.com/app/204360/Castle_Crashers/
    """

    if not args:
        return await ctx.channel.send(
            'To add a game please supply a game name and optional URL as parameters. e.g "add Castle Crashers" or '
            '"add Castle Crashers http://cannibalsock.com/"')
    game_in = list(args)
    url = game_in.pop(-1) if game_in[-1].lower().startswith('http') else None
    name = ' '.join(game_in)
    steam_id = None
    if not url:
        url = await search_game(name)
    if url and not name:
        # Search for game name if we have a valid steam link
        if 'store.steampowered.com' in url:
            name = [i for i in url.split('/') if i][-1].replace('_', ' ')
            try:
                # if the last bit of the url was a number, then we cant strip the name
                # look up name on steam.com with id
                int(name)
                name = await game_name_from_steam_id(name)
            except ValueError:
                # if it wasn't a number, assume its the game name
                pass
        else:
            name = url
    if url:
        if not url.endswith('/'):
            url += '/'
        steam_id = re.search('\/[0-9]{4,}\/', url)
        if steam_id:
            steam_id = steam_id[0].replace('/', '')
    try:
        Game.get(Game.name == name.lower(), Game.played == False)
        return await ctx.send(f'Looks like "{name}" is already on the list')
    except Game.DoesNotExist:
        g = Game.create(name=name.lower(), added_by=ctx.author.id, url=url, steam_id=steam_id)
        _ = f'Added {g.name.title()} ({g.url})' if g.url else f'Added {g.name.title()}'
        return await ctx.send(_)


@bot.command()
async def remove(ctx, arg):
    """Removes a game from the list"""""
    try:
        to_remove = Game.get(Game.name == arg.lower(), Game.played == False)
        to_remove.played = True
        to_remove.save()
        return await ctx.send(f'Removed {arg}')
    except Game.DoesNotExist:
        to_remove = list(Game.select().where(Game.name % arg, Game.played == False))
        if len(to_remove) > 1 or len(to_remove) < 1:
            return await ctx.send(f'More than one game returned for "{arg}"')
        else:
            to_remove[0].played = True
            to_remove[0].save()
            return await ctx.send(f'Removed {arg}')


@bot.command()
async def games(ctx):
    """A short & tidy list of games"""

    def make_games_content(games_list):
        content = ''
        for g in games_list:
            date_diff = (datetime.now() - g.added_on).days
            date_diff_text = f' (added {(datetime.now() - g.added_on).days} ago)' if date_diff else ''
            if g.url:
                content += f'[{g.name.title()}]({g.url}){date_diff_text}\n'
            else:
                content += f'{g.name.title()}{date_diff_text}\n'
        return content

    embed = discord.Embed(
        title='Current Games List',
        colour=discord.Colour(0xE5E242),
        description='`?add castle crashers`\n`?remove castle crashers`\n`?games`\n`?game_links`'
    )
    recent_games = Game.select().where(Game.added_on >= (datetime.now() - timedelta(days=30)), Game.played == False)
    recent_games_value = make_games_content(recent_games)
    older_games = Game.select().where(Game.added_on < (datetime.now() - timedelta(days=30)), Game.played == False)
    older_games_value = make_games_content(older_games)

    embed.add_field(name='Recent Additions', value=recent_games_value, inline=False) if recent_games_value else None
    embed.add_field(name='Old Games', value=older_games_value, inline=False) if older_games_value else None

    return await ctx.send(embed=embed)


@bot.command()
async def game_links(ctx):
    """A big and messy list of games"""
    for g in Game.select():
        if g.url:
            await ctx.send(f'{g.name.title()} ({g.url})')
        else:
            await ctx.send(f'{g.name.title()}')


@bot.event
async def on_message(message):
    if message.author != bot.user:
        if random.randint(1, 100) == 69:
            _ = ''
            a = TextCount.get(text='p00p')
            for i in range(a.counter):
                _ += 'p00p '
            await message.channel.send(_)
            a.counter += 1
            a.save()
    await bot.process_commands(message)


bot.run(conf['API_SECRET'])
