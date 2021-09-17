import logging
import os
import random

# import discord
from discord.ext import commands

from util import populous_channel
from .models import Reset

logger = logging.getLogger(__name__)

reset_message = f'Next time I\'ll do better...'


class MgmtCommandsCog(commands.Cog, name='Management Commands'):

    @commands.command(aliases=['restart', 'reboot', 'stop_crashing'])
    async def reset(self, ctx):
        """Restarts the bot. Please don't do this."""
        logger.info('Resetting bot')
        await ctx.send(reset_message)
        Reset.create(channel_id=ctx.channel.id)
        async with ctx.typing():
            os.system(r"python reset_bot.py")

    @commands.command(aliases=['random'])
    async def random_user(self, ctx):
        """Selects a random user from the most populous voice channel"""
        voice_channel = ctx.bot.get_channel(populous_channel(ctx))
        members = list(voice_channel.members)
        chosen = random.choice(members)
        snd = chosen.nick if chosen.nick else chosen
        await ctx.send(snd)

    # @commands.command()
    # async def check(self, ctx):
    #     g = Reset.create(channel_id=ctx.channel.id)
    #     channel = ctx.channel.id
    #     await ctx.bot.get_channel(channel).send('found it')
    #     await ctx.send(f'{1}')
    #
    # @commands.command()
    # async def vcid(self, ctx):
    #
    #     for i in conf['VC_IDS']:
    #         voice_channel = ctx.bot.get_channel(i)
    #
    #         members = voice_channel.members
    #         member_names = '\n'.join([x.name for x in members])
    #
    #         embed = discord.Embed(title="{} member(s) in {}".format(len(members), voice_channel.name),
    #                               description=member_names,
    #                               color=discord.Color.blue())
    #
    #         return await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(MgmtCommandsCog(bot))
