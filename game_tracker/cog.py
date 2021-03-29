import re
from datetime import datetime

import discord
from discord.ext import commands

from .models import Game
from .util import add_games_list_to_embed, get_steam_game_info, parse_steam_game_info, search_game, \
    update_game


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
        Adds a new game to the list, takes optional parameters [-name -max -min -name -url -party]

            add Castle Crashers
            add Castle Crashers https://store.steampowered.com/app/204360/Castle_Crashers/

            # Minimum 3 players, Max 4, is Party Game Flag On
            add Castle Crashers -url=https://store.steampowered.com/app/204360/Castle_Crashers/ -min=3 -max=4 -party=1
        """

        name, url, min_players, max_players = None, None, None, None
        party = 0
        release_date_obj, release_date_str, steam_id, price, tags = None, None, None, None, None

        if not args:
            return await ctx.channel.send(
                'To add a game please supply a game name and optional URL as parameters. e.g "add Castle Crashers" or '
                '"add Castle Crashers -url=http://cannibalsock.com/"')

        # Why use argparse when you can write our own!
        kwargs = {}
        not_kwargs = []
        for a in args:
            if a.startswith('--') or a.startswith('-'):
                a = a.lstrip('--').lstrip('-')
                kwargs[a.split('=')[0]] = a.split('=')[1]
            else:
                not_kwargs.append(a)
        args = not_kwargs

        if kwargs:
            name = kwargs.get('name', None)
            url = kwargs.get('url', None)
            min_players = kwargs.get('min', None)
            max_players = kwargs.get('max', None)
            party = bool(kwargs.get('party', 0))

        # Lazy validation
        if (max_players and not min_players) or (min_players and not max_players):
            return await ctx.send(f'Error: -max and -min must be supplied as a pair')
        try:
            int(max_players)
            int(min_players)
        except ValueError:
            return await ctx.send(f'Error: -max and -min must be integers')

        # broken for games that start with http
        if not url:
            for a in args:
                if a.startswith('http'):
                    url = a
        if not name:
            name = ' '.join([i for i in args if not i.startswith('http')])

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
                    data = await get_steam_game_info(steam_id)
                    _name, release_date_str, release_date_obj, price, tags = await parse_steam_game_info(data)
            else:
                _name = url
            if _name and not name:
                name = _name

        # print(name, url, steam_id, min_players, max_players, party)

        if list(Game.select().where(
            (Game.name == name.lower()) |
            ((Game.steam_id == steam_id) & Game.steam_id.is_null(False)) |
            (Game.url == url))
        ):
            return await ctx.send(f'Looks like "{name}" is already on the list')

        g = Game.create(name=name.lower(), added_by=ctx.author.id, url=url, steam_id=steam_id,
                        release_date_str=release_date_str, release_date_obj=release_date_obj, price=price, tags=tags,
                        min_players=min_players, max_players=max_players, party=party)
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
    async def games(self, ctx, num_players=None):
        """A list of games to play"""
        embed = self._embed('Master Games List')
        new_released_games = Game.manager().new().released().players(num_players).call()
        unreleased_games = Game.manager().unreleased().players(num_players).call()
        started_games = Game.manager().old().players(num_players).call()

        for i in [('New', new_released_games),
                  ('Keep Playing', started_games),
                  ('Unreleased', unreleased_games)]:
            add_games_list_to_embed(embed, i)

        return await ctx.send(embed=embed)

    @commands.command()
    async def party(self, ctx, num_players=None):
        """A list of party games to play"""
        embed = self._embed('Party Games List')
        released_party_games = Game.manager().new().party().released().players(num_players).call()
        unreleased_party_games = Game.manager().unreleased().party().players(num_players).call()
        started_party_games = Game.manager().old().party().players(num_players).call()

        for i in [('Play Now!', released_party_games),
                  ('Play Again!', started_party_games),
                  ('Play Soon!', unreleased_party_games), ]:
            add_games_list_to_embed(embed, i)
        return await ctx.send(embed=embed)

    @commands.command()
    async def finished(self, ctx, *args):
        """A list of finished games"""
        embed = discord.Embed(
            title='Finished Games',
            colour=discord.Colour(0xE5E242),
        )
        finished_games = Game.manager().finished().call()
        add_games_list_to_embed(embed, ('All Done', finished_games))

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

    @commands.command(aliases=['on_sale', 'onsale', 'discount'])
    async def sale(self, ctx, num_players=None):
        games = Game.manager().released().new().players(num_players).call()
        on_sale = []
        async with ctx.typing():
            for g in games:
                if g.steam_id:
                    steam_data = await get_steam_game_info(g.steam_id)
                    if steam_data['price_overview']['discount_percent'] != 0:
                        on_sale.append(g)

        if on_sale:
            embed = discord.Embed(
                title='Bargain Games',
                colour=discord.Colour(0xE5E242),
            )
            add_games_list_to_embed(embed, ('On sale:', on_sale))
            return await ctx.send(embed=embed)
        else:
            return await ctx.send(f'Nothing on sale right now')


def setup(bot):
    bot.add_cog(GameTrackerCog(bot))
