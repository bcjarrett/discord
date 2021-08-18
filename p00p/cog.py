import random
from statistics import NormalDist

from discord.ext import commands

from util import plural, poop_n
from .models import TextCount


class PoopCog(commands.Cog, name='p00p bot core'):

    async def poop(self, message):
        poop_model = TextCount.get(text='p00p')

        # Positive half-normal dist centered at 0, sd 20. ints only
        num_poops = round(abs(NormalDist(0, 20).inv_cdf(random.random())))
        special_numbers = {
            -1: f'{poop_n(num_poops)}',
            0: 'Ooops, looks like that was just a fart :wind_blowing_face:',
            1: ':poop:',
            69: ':fireworks: :fireworks: 69 :poop: 69 :fireworks: :fireworks: '
                '\nWE DID IT BOYS! GAME OVER! Please stop at the counter on the way out to collect your prize.'
                f'\n{poop_n(69, text=":poop:")}'
        }
        msg = special_numbers.get(num_poops, special_numbers[-1])

        # Increment counter
        poop_model.counter += 1
        poop_model.save()

        poop_model.record_holder = str(message.author.nick)
        await message.channel.send(msg)
        if num_poops > poop_model.max_num:
            poop_model.max_num = num_poops
            poop_model.save()
            await message.channel.send(
                f'Congratulations {message.author.nick}! That\'s a new record! {num_poops} p00ps! Such a big '
                f'boy! :heart_eyes: :heart_eyes: :heart_eyes: ')

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def p00p(self, ctx):
        return await self.poop(ctx)

    @commands.command(description='Clear p00p counter')
    async def clear(self, ctx):
        """Resets the p00p count"""
        poop_model = TextCount.get(text='p00p')
        poop_model.counter = 1
        poop_model.max_num = 0
        poop_model.record_holder = ''
        poop_model.save()
        return await ctx.send(
            '"A one hump camel makes a one hump poop, and a two hump camel makes a two hump poop"')

    @commands.command(description='Display the current p00p count')
    async def count(self, ctx):
        """Displays the current p00p count"""
        count = TextCount.get(text='p00p').counter
        return await ctx.send(f'We\'ve sent {count} p00p{plural(count)}!')

    @commands.command(description='Show the record holder',
                      aliases=['most_poops', 'mostpoops', 'bigshit', 'bigpoop', 'bigpooper', 'bigshitter'])
    async def record(self, ctx):
        """Displays the current p00p record holder"""
        poop_model = TextCount.get(text='p00p')
        max_poop = poop_model.max_num
        owner = poop_model.record_holder
        if owner:
            return await ctx.send(f'Our big loser is currently {owner} with {max_poop} p00p{plural(max_poop)}!'
                                  f'\n:clap: :clap: :clap:')
        else:
            return await ctx.send('No current record, get to p00pin.')

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Send bigger and bigger poops everytime a message is
        In discord :poop: = 💩
        """
        if message.author != self.bot.user:
            # Only send message 5% of the time
            if random.randint(1, 40) == 20:
                await self.p00p(message)


def setup(bot):
    bot.add_cog(PoopCog(bot))
