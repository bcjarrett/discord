import re
from datetime import datetime

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands

from .models import Game

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
        name = ' '.join(game_in)
        steam_id = None
        if not url:
            async with ctx.typing():
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
            steam_id = re.search(r'/[0-9]{4,}/', url)
            if steam_id:
                steam_id = steam_id[0].replace('/', '')
        try:
            Game.get(Game.name == name.lower(), Game.started == False)
            return await ctx.send(f'Looks like "{name}" is already on the list')
        except Game.DoesNotExist:
            g = Game.create(name=name.lower(), added_by=ctx.author.id, url=url, steam_id=steam_id)
            _ = f'Added {g.name.title()} ({g.url})' if g.url else f'Added {g.name.title()}'
            return await ctx.send(_)

    @commands.command()
    async def finish(self, ctx, *args):
        """Marks a game as finished"""""
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
            content = ''
            for g in games_list:
                if g.url:
                    content += f'[{g.name.title()}]({g.url}){g.recent_activity}\n'
                else:
                    content += f'{g.name.title()}{g.recent_activity}\n'
            return content

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

        embed.add_field(name='New Games', value=new_games_value, inline=False) if new_games_value else None
        embed.add_field(name='Games in Progress', value=started_games_value, inline=False) if started_games_value else None

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

        embed.add_field(name='Finished Games', value=finished_games_value, inline=False) if finished_games_value else None

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