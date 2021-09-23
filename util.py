def plural(in_num):
    return '' if in_num == 1 else 's'


def populous_channel(ctx):
    channels = {(i, len(i.members)) for i in ctx.guild.voice_channels}
    return max(channels, key=lambda x: x[1])[0]


def poop_n(num_poops, text='p00p'):
    poops = [text for i in range(num_poops)]
    return ' '.join(poops)
