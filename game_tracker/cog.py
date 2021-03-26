import re
from datetime import datetime

import discord
from discord.ext import commands

from .models import Game
from .util import _add_field, get_steam_game_info, search_game, update_game


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
        price = None
        tags = None
        name = ' '.join(game_in)

        if not url:
            async with ctx.typing():
                url = await search_game(name)
        if url:
            # Search steam for game info
            if 'store.steampowered.com' in url:
                if not url.endswith('/'):
                    url += '/'
                steam_id = re.search(r'/[0-9]{4,}/', url)
                if steam_id:
                    steam_id = steam_id[0].replace('/', '')

                async with ctx.typing():
                    _name, release_date_str, release_date_obj, price, tags = await get_steam_game_info(steam_id)
            else:
                _name = url
            if _name:
                name = _name

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
                        release_date_str=release_date_str, release_date_obj=release_date_obj, price=price, tags=tags)
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
                tags = f'({g.simple_tags})' if g.simple_tags else ''
                if g.url:
                    content.append(f'[{g.name.title()}]({g.url}) {tags}')
                else:
                    content.append(f'{g.name.title()} {tags}')
            return '\n'.join(content)

        embed = discord.Embed(
            title='Current Games List',
            colour=discord.Colour(0xE5E242),
            # description='`?add castle crashers`\n`?remove castle crashers`\n`?start castle
            # crashers`\n`?games`\n`?game_links`'
        )
        new_released_games = Game.select().where(
            Game.release_date_obj <= (datetime.now()),
            Game.started == False,
            Game.finished == False
        ).order_by(-Game.added_on, Game.name)
        unreleased_games = Game.select().where(
            (Game.release_date_obj >= (datetime.now())) | (Game.release_date_obj.is_null()),
            ).order_by(-Game.added_on, Game.name)
        started_games = Game.select().where(
            # Game.added_on >= (datetime.now() - timedelta(days=30)),
            Game.started == True,
            Game.finished == False
        ).order_by(-Game.started_on, Game.name)
        new_released_games_value = make_games_content(new_released_games)
        unreleased_games_value = make_games_content(unreleased_games)
        started_games_value = make_games_content(started_games)
        _add_field(embed, name='New Games', value=new_released_games_value, inline=False) if new_released_games_value else None
        _add_field(embed, name='Games in Progress', value=started_games_value,
                   inline=False) if started_games_value else None
        _add_field(embed, name='Unreleased Games', value=unreleased_games_value, inline=False) if unreleased_games_value else None

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

    @commands.command(aliases=['update', ])
    async def update_games(self, ctx):
        """Updates all release dates for steam games"""
        async with ctx.typing():
            for g in Game.select().where(Game.finished != True):
                await update_game(g)
        await ctx.send(f'Game info updated')


def setup(bot):
    bot.add_cog(GameTrackerCog(bot))
