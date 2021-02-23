import os

from discord.ext import commands

from .models import Reset

reset_message = f'Next time I\'ll do better...'


class MgmtCommandsCog(commands.Cog, name='Management Commands'):

    @commands.command(aliases=['restart', 'reboot', 'stop_crashing'])
    async def reset(self, ctx):
        """Restarts the bot"""
        await ctx.send(reset_message)
        Reset.create(channel_id=ctx.channel.id)
        async with ctx.typing():
            os.system(r"python reset_bot.py")


def setup(bot):
    bot.add_cog(MgmtCommandsCog(bot))
