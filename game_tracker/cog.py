import re
from datetime import datetime

import aiohttp
import discord
from dateutil import parser
from bs4 import BeautifulSoup
from discord.ext import commands

from .models import Game

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/61.0.3163.100 Safari/537.36'}


def content_squinch(content, content_list, length=1000):
    temp_length = 0
    _slice = 0
    for n, i in enumerate(content):
        if len(i) + temp_length < length:
            _slice += 1
            temp_length += len(i)
        else:
            content_list.append(content[0:_slice])
            return content_list, content[_slice:]
    content_list.append(content[0:_slice])
    return content_list, content[_slice:]


def _add_field(_embed, name, value, inline):
    if len(value) > 1000:
        content = value.split('\n')
        final_content = []
        while content:
            final_content, content = content_squinch(content, final_content)
        for n, i in enumerate(final_content):
            if n == 0:
                _embed.add_field(name=f'{name}', value='\n'.join(i), inline=inline)
            else:
                _embed.add_field(name=f'\t...(contd.)', value='\n'.join(i), inline=inline)

    else:
        _embed.add_field(name=f'{name}', value=value, inline=inline)


async def search_game(title, number_results=10, language_code='en'):
    google_url = 'https://www.google.com/search?q={}&num={}&hl={}'.format(title.replace(" ", "+") + 'steam game',
                                                                          number_results + 1,
                                                                          language_code)

    async with aiohttp.ClientSession() as session:
        async with session.get(google_url, headers=headers) as r:
            if r.status == 200:
                text = await r.read()
            else:
                text = ''

        soup = BeautifulSoup(text, 'html.parser')
        result_block = soup.find_all('div', attrs={'class': 'g'})
        games = []
        for result in result_block:
            link = result.find('a', href=True)
            title = result.find('h3')
            if link and title:
                games.append(link['href'])
        game = games[0]
        if re.search(r'store\.steampowered\.com/app/[0-9]*', game):
            return game
        else:
            return None


async def get_steam_game_info(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as r:
            if r.status == 200:
                text = await r.read()

        soup = BeautifulSoup(text, 'html.parser')
        try:
            app_name = soup.find('div', attrs={'class': 'apphub_AppName'}).text
        except AttributeError:
            app_name = None
        try:
            release_date = soup.find('div', attrs={'class': 'release_date'}).find('div', attrs={'class': 'date'}).text
        except AttributeError:
            release_date = None

        return app_name, release_date


class GameTrackerCog(commands.Cog, name='Game Tracker'):

    @commands.command(description='Add a game to the list')
    async def add(self, ctx, *args):
        """
        Adds a new game to the list
        URL as optional parameter, searches steam if no URL is provided

            add Castle Crashers
            add Castle Crashers https://store.steampowered.com/app/204360/Castle_Crashers/
        """

        if not args:
            return await ctx.channel.send(
                'To add a game please supply a game name and optional URL as parameters. e.g "add Castle Crashers" or '
                '"add Castle Crashers http://cannibalsock.com/"')
        game_in = list(args)
        url = game_in.pop(-1) if game_in[-1].lower().startswith('http') else None
        release_date_obj = None
        release_date_str = None
        steam_id = None
        name = ' '.join(game_in)
        if not url:
            async with ctx.typing():
                url = await search_game(name)
        if url:
            # Search steam for game info
            if 'store.steampowered.com' in url:
                _name, release_date_str = await get_steam_game_info(url)
                try:
                    release_date_obj = parser.parse(release_date_str)
                except (parser._parser.ParserError, TypeError):
                    pass
            else:
                _name = url
            if _name:
                name = _name

            # Pull out the steamID for some reason
            if not url.endswith('/'):
                url += '/'
            steam_id = re.search(r'/[0-9]{4,}/', url)
            if steam_id:
                steam_id = steam_id[0].replace('/', '')

        # Check if game already in db in some other form
        # this should be a filter but i don't want to look up how to do that with peewee
        for check in [
            lambda: Game.get(Game.name == name.lower()),
            lambda: Game.get(Game.steam_id == steam_id),
            lambda: Game.get(Game.url == url),
        ]:
            try:
                _ = check()
                return await ctx.send(f'Looks like "{name}" is already on the list')
            except Game.DoesNotExist:
                continue

        g = Game.create(name=name.lower(), added_by=ctx.author.id, url=url, steam_id=steam_id,
                        release_date_str=release_date_str, release_date_obj=release_date_obj)
        _ = f'Added {g.name.title()} ({g.url})' if g.url else f'Added {g.name.title()}'
        return await ctx.send(_)

    @commands.command()
    async def finish(self, ctx, *args):
        """Marks a game as finished"""
        game_title = ' '.join(list(args))
        game = Game.get_game(game_title)
        if game[0]:
            game[1].started = True
            game[1].finished = True
            game[1].finished_on = datetime.now()
            game[1].save()
            return await ctx.send(f'Marked {game_title} as finished')
        else:
            return await ctx.send(game[1])

    @commands.command()
    async def start(self, ctx, *args):
        """Marks a game as started"""
        game_title = ' '.join(list(args))
        game = Game.get_game(game_title)
        if game[0]:
            game[1].started = True
            game[1].started_on = datetime.now()
            game[1].save()
            return await ctx.send(f'Started {game_title}')
        else:
            return await ctx.send(game[1])

    @commands.command(hidden=True)
    async def delete(self, ctx, *args):
        """Deletes a game. Cannot be undone"""
        game_title = ' '.join(list(args))
        game = Game.get_game(game_title)
        if ctx.author.id == 488728306359730186:
            if game[0]:
                game[1].delete_instance()
                return await ctx.send(f'Deleted {game_title} from database')
            else:
                return await ctx.send(game[1])
        else:
            return await ctx.send(f'Delete can only be performed by db admin')

    @commands.command()
    async def games(self, ctx):
        """A list of games to play"""

        def make_games_content(games_list):
            content = []
            for g in games_list:
                if g.url:
                    content.append(f'[{g.name.title()}]({g.url}){g.recent_activity}')
                else:
                    content.append(f'{g.name.title()}{g.recent_activity}')
            return '\n'.join(content)

        embed = discord.Embed(
            title='Current Games List',
            colour=discord.Colour(0xE5E242),
            # description='`?add castle crashers`\n`?remove castle crashers`\n`?start castle
            # crashers`\n`?games`\n`?game_links`'
        )
        new_games = Game.select().where(
            # Game.added_on >= (datetime.now() - timedelta(days=30)),
            Game.started == False,
            Game.finished == False
        ).order_by(-Game.added_on, Game.name)
        started_games = Game.select().where(
            # Game.added_on >= (datetime.now() - timedelta(days=30)),
            Game.started == True,
            Game.finished == False
        ).order_by(-Game.started_on, Game.name)
        new_games_value = make_games_content(new_games)
        started_games_value = make_games_content(started_games)
        _add_field(embed, name='New Games', value=new_games_value, inline=False) if new_games_value else None
        _add_field(embed, name='Games in Progress', value=started_games_value,
                   inline=False) if started_games_value else None

        return await ctx.send(embed=embed)

    @commands.command()
    async def finished(self, ctx):
        """A list of finished games"""

        def make_games_content(games_list):
            content = ''
            for g in games_list:
                if g.url:
                    content += f'[{g.name.title()}]({g.url}){g.recent_activity}\n'
                else:
                    content += f'{g.name.title()}{g.recent_activity}\n'
            return content

        embed = discord.Embed(
            title='Finished Games',
            colour=discord.Colour(0xE5E242),
        )
        finished_games = Game.select().where(
            Game.started == True,
            Game.finished == True
        ).order_by(-Game.finished_on, Game.name)
        finished_games_value = make_games_content(finished_games)

        embed.add_field(name='Finished Games', value=finished_games_value,
                        inline=False) if finished_games_value else None

        return await ctx.send(embed=embed)

    @commands.command()
    async def game_links(self, ctx):
        """Spams the URLs so you can see pictures"""
        for g in Game.select():
            if g.url:
                await ctx.send(f'{g.name.title()} ({g.url})')
            else:
                await ctx.send(f'{g.name.title()}')


def setup(bot):
    bot.add_cog(GameTrackerCog(bot))
