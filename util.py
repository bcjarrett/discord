from config import conf


def plural(in_num):
    return '' if in_num == 1 else 's'


def populous_channel(ctx):
    channels = {(i, len(ctx.bot.get_channel(i).members)) for i in conf['VC_IDS']}
    return max(channels, key=lambda x: x[1])[0]


def poop_n(num_poops, text='p00p'):
    poops = [text for i in range(num_poops)]
    return ' '.join(poops)
