from config import conf


def plural(in_num):
    return '' if in_num == 1 else 's'


def populous_channel(ctx):
    channels = {(i, len(ctx.bot.get_channel(i).members)) for i in conf['VC_IDS']}
    return max(channels, key=lambda x: x[1])[0]
