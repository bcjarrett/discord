import random

from discord.ext import commands

from util import plural
from .models import TextCount


def poop_n(num_poops):
    poops = ['p00p' for i in range(num_poops)]
    return ' '.join(poops)


class PoopCog(commands.Cog, name='p00p bot core'):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(description='Clear p00p counter')
    async def clear(self, ctx):
        """Resets the p00p count"""
        a = TextCount.get(text='p00p')
        a.counter = 1
        a.save()
        return await ctx.send('Back to one p00p :cry:')

    @commands.command(description='Display the current p00p count')
    async def count(self, ctx):
        """Displays the current p00p count"""
        count = TextCount.get(text='p00p').counter
        return await ctx.send(f'Currently at {count} p00p{plural(count)}')

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Send bigger and bigger poops everytime a message is
        In discord :poop: = 💩
        """

        if message.author != self.bot.user:
            if random.randint(40, 70) == 69:
                current_poop_count = TextCount.get(text='p00p')
                await message.channel.send(poop_n(current_poop_count))
                current_poop_count.counter += 1
                current_poop_count.save()


def setup(bot):
    bot.add_cog(PoopCog(bot))
