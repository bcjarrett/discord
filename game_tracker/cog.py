import re
from datetime import datetime

import discord
from discord.ext import commands

from .models import Game
from .util import _add_games_list_to_embed, get_steam_game_info, search_game, update_game


class GameTrackerCog(commands.Cog, name='Game Tracker'):

    @staticmethod
    def _embed(title):
        return discord.Embed(
            title=title,
            colour=discord.Colour(0xE5E242),
        )

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
        embed = self._embed('Master Games List')
        new_released_games = Game.manager().new().released().call()
        unreleased_games = Game.manager().unreleased().call()
        started_games = Game.manager().started().call()

        for i in [('New', new_released_games),
                  ('Keep Playing', started_games),
                  ('Unreleased', unreleased_games)]:
            _add_games_list_to_embed(embed, i)

        return await ctx.send(embed=embed)

    @commands.command()
    async def party(self, ctx):
        """A list of party games to play"""
        embed = self._embed('Party Games List')
        released_party_games = Game.manager().new().party().released().call()
        unreleased_party_games = Game.manager().unreleased().party().call()
        started_party_games = Game.manager().old().party().call()

        for i in [('Play Now!', released_party_games),
                  ('Play Again!', started_party_games),
                  ('Play Soon!', unreleased_party_games), ]:
            _add_games_list_to_embed(embed, i)
        return await ctx.send(embed=embed)

    @commands.command()
    async def players(self, ctx, num_players):
        """A list of games to filtered by number of players"""
        embed = self._embed('Party Games List')
        released_party_games = Game.manager().new().released().players(num_players).call()
        unreleased_party_games = Game.manager().unreleased().players(num_players).call()
        started_party_games = Game.manager().old().players(num_players).call()

        for i in [('Play Now!', released_party_games),
                  ('Play Again!', started_party_games),
                  ('Play Soon!', unreleased_party_games), ]:
            _add_games_list_to_embed(embed, i)
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
