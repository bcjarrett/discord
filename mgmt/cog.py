import logging.config
import os
import random

import discord
from discord.ext import commands, tasks

from config import BOT_STATUS
from util import populous_channel
from .models import Reset

logger = logging.getLogger(__name__)

reset_message = f'Next time I\'ll do better...'


class MgmtCommandsCog(commands.Cog, name='Management Commands'):

    def __init__(self, bot):
        self.bot = bot
        self.update_status.start()

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

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f'Logged in as: {self.bot.user.name} - {self.bot.user.id}')
        logger.info(f'Version: {discord.__version__}')
        logger.info(f'Connected to {[g.name for g in self.bot.guilds]}')

        try:
            channel_id = Reset.select().order_by(Reset.added_on.desc()).first().channel_id
            channel = self.bot.get_channel(channel_id)
            last_msg = await channel.history().find(lambda m: m.author.id == self.bot.user.id)
            startup_msg = 'Successfully Started Up :thumbsup:'
            if last_msg.clean_content == reset_message:
                await last_msg.edit(content=startup_msg)
            else:
                await channel.send(startup_msg)
        except AttributeError:
            pass

    @tasks.loop(seconds=10)
    async def update_status(self):
        await self.bot.change_presence(activity=discord.Game(name=random.choice(BOT_STATUS)))

    @update_status.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(MgmtCommandsCog(bot))
