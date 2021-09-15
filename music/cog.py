"""
All credit to https://github.com/joek13/py-music-bot
"""

import asyncio
import logging
import math
import random
import urllib.parse

import discord
import youtube_dl
from discord.ext import commands

from config import conf
from .models import Playlist
from .video import Video
from .spotify import SpotifyPlaylist
from .soundcloud import SoundCloudPlaylist

logger = logging.getLogger(__name__)

# TODO: abstract FFMPEG options into their own file?
FFMPEG_BEFORE_OPTS = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
"""
Command line options to pass to `ffmpeg` before the `-i`.

See https://stackoverflow.com/questions/43218292/youtubedl-read-error-with-discord-py/44490434#44490434 for more 
information.
Also, https://ffmpeg.org/ffmpeg-protocols.html for command line option reference.
"""


async def audio_playing(ctx):
    """Checks that audio is currently playing before continuing."""
    client = ctx.guild.voice_client
    if client and client.channel and client.source:
        return True
    else:
        raise commands.CommandError("Not currently playing any audio.")


async def in_voice_channel(ctx):
    """Checks that the command sender is in the same voice channel as the bot."""
    voice = ctx.author.voice
    bot_voice = ctx.guild.voice_client
    if voice and bot_voice and voice.channel and bot_voice.channel and voice.channel == bot_voice.channel:
        return True
    else:
        raise commands.CommandError(
            "You need to be in the channel to do that.")


async def is_audio_requester(ctx):
    """Checks that the command sender is the song requester."""
    music = ctx.bot.get_cog('Music')
    state = music.get_state(ctx.guild)
    permissions = ctx.channel.permissions_for(ctx.author)
    if permissions.administrator or state.is_requester(ctx.author):
        return True
    else:
        raise commands.CommandError(
            "You need to be the song requester to do that.")


class MusicCog(commands.Cog, name='Music'):
    """Bot commands to help play music."""

    def __init__(self, bot):
        self.bot = bot
        self.states = {}
        self.bot.add_listener(self.on_reaction_add, "on_reaction_add")

    def get_state(self, guild):
        """Gets the state for `guild`, creating it if it does not exist."""
        if guild.id in self.states:
            return self.states[guild.id]
        else:
            self.states[guild.id] = GuildState()
            return self.states[guild.id]

    @commands.command(aliases=["stop"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx):
        """Leaves the voice channel, if currently in one."""
        client = ctx.guild.voice_client
        state = self.get_state(ctx.guild)
        if client and client.channel:
            await client.disconnect()
            state.playlist = []
            state.now_playing = None
        else:
            raise commands.CommandError("Not in a voice channel.")

    @commands.command(aliases=["resume", "p"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    @commands.check(is_audio_requester)
    async def pause(self, ctx):
        """Pauses any currently playing audio."""
        client = ctx.guild.voice_client
        self._pause_audio(client)

    def _pause_audio(self, client):
        if client.is_paused():
            client.resume()
        else:
            client.pause()

    @commands.command(aliases=["vol", "v"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    @commands.check(is_audio_requester)
    async def volume(self, ctx, volume: int):
        """Change the volume of currently playing audio (values 0-250)."""
        state = self.get_state(ctx.guild)

        # make sure volume is nonnegative
        if volume < 0:
            volume = 0

        max_vol = conf['MAX_VOLUME']
        if max_vol > -1:  # check if max volume is set
            # clamp volume to [0, max_vol]
            if volume > max_vol:
                volume = max_vol

        client = ctx.guild.voice_client

        state.volume = float(volume) / 100.0
        client.source.volume = state.volume  # update the AudioSource's volume to match

    @commands.command()
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.check(in_voice_channel)
    async def skip(self, ctx):
        """Skips the currently playing song, or votes to skip it."""
        state = self.get_state(ctx.guild)
        client = ctx.guild.voice_client
        if ctx.channel.permissions_for(
                ctx.author).administrator or state.is_requester(ctx.author):
            # immediately skip if requester or admin
            client.stop()
        elif conf["VOTE_SKIP"]:
            # vote to skip song
            channel = client.channel
            self._vote_skip(channel, ctx.author)
            # announce vote
            users_in_channel = len([
                member for member in channel.members if not member.bot
            ])  # don't count bots
            required_votes = math.ceil(
                conf["VOTE_SKIP_RATIO"] * users_in_channel)
            await ctx.send(
                f"{ctx.author.mention} voted to skip ({len(state.skip_votes)}/{required_votes} votes)"
            )
        else:
            raise commands.CommandError("Sorry, vote skipping is disabled.")

    def _vote_skip(self, channel, member):
        """Register a vote for `member` to skip the song playing."""
        logging.info(f"{member.name} votes to skip")
        state = self.get_state(channel.guild)
        state.skip_votes.add(member)
        users_in_channel = len([
            member for member in channel.members if not member.bot
        ])  # don't count bots
        if (float(len(state.skip_votes)) /
            users_in_channel) >= conf["vote_skip_ratio"]:
            # enough members have voted to skip, so skip the song
            logging.info(f"Enough votes, skipping...")
            channel.guild.voice_client.stop()

    def _play_song(self, client, state, song):
        state.now_playing = song
        state.skip_votes = set()  # clear skip votes
        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(song.stream_url, before_options=FFMPEG_BEFORE_OPTS), volume=state.volume)

        def after_playing(err):
            if len(state.playlist) > 0:
                next_song = state.playlist.pop(0)
                self._play_song(client, state, next_song)
            else:
                asyncio.run_coroutine_threadsafe(client.disconnect(),
                                                 self.bot.loop)

        client.play(source, after=after_playing)

    @commands.command(aliases=["np"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def nowplaying(self, ctx):
        """Displays information about the current song."""
        state = self.get_state(ctx.guild)
        message = await ctx.send("", embed=state.now_playing.get_embed())
        await self._add_reaction_controls(message)

    @commands.command(aliases=["q"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def queue(self, ctx):
        """Display the current play queue."""
        # TODO: fails for long lists
        state = self.get_state(ctx.guild)
        await ctx.send(self._queue_text(state.playlist))

    def _queue_text(self, queue):
        """Returns a block of text describing a given song queue."""
        if len(queue) > 0:
            message = [f"{len(queue)} songs in queue:"]
            message += [
                f"  {index + 1}. **{song.title}** (requested by **{song.requested_by.name}**)"
                for (index, song) in enumerate(queue)
            ]  # add individual songs
            return "\n".join(message)
        else:
            return "The play queue is empty."

    @commands.command(aliases=["sq"])
    @commands.guild_only()
    @commands.check(audio_playing)
    async def suffle_queue(self, ctx):
        """Shuffles the current song queue"""
        random.shuffle(self.get_state(ctx.guild).playlist)
        return await ctx.send('Queue Shuffled!')

    @commands.command(aliases=["cq"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_permissions(administrator=True)
    async def clearqueue(self, ctx):
        """Clears the play queue without leaving the channel."""
        state = self.get_state(ctx.guild)
        state.playlist = []

    @commands.command(aliases=["jq"])
    @commands.guild_only()
    @commands.check(audio_playing)
    @commands.has_permissions(administrator=True)
    async def jumpqueue(self, ctx, song: int, new_index: int):
        """Moves song at an index to `new_index` in queue."""
        state = self.get_state(ctx.guild)  # get state for this guild
        if 1 <= song <= len(state.playlist) and 1 <= new_index:
            song = state.playlist.pop(song - 1)  # take song at index...
            state.playlist.insert(new_index - 1, song)  # and insert it.

            await ctx.send(self._queue_text(state.playlist))
        else:
            raise commands.CommandError("You must use a valid index.")

    @commands.command(brief="Plays audio from <url>.")
    @commands.guild_only()
    async def play(self, ctx, *, url, embed=True, song=False):
        """Plays audio or playlist hosted at <url> (or performs a search for <url> and plays the first result)."""
        async with ctx.typing():
            client = ctx.guild.voice_client
            state = self.get_state(ctx.guild)  # get the guild's state

            async def yt_search_add_to_queue():
                try:
                    video = Video(url, ctx.author)
                except youtube_dl.DownloadError as e:
                    logging.warning(f"Error downloading video: {e}")
                    await ctx.send(
                        "There was an error downloading your video, sorry :(.")
                    return
                state.playlist.append(video)
                if embed:
                    message = await ctx.send(
                        "Added to queue.", embed=video.get_embed())
                    await self._add_reaction_controls(message)

            async def yt_search_play():
                channel = ctx.author.voice.channel
                try:
                    video = Video(url, ctx.author)
                except youtube_dl.DownloadError as e:
                    logging.warning(f"Error downloading video: {e}")
                    await ctx.send(
                        "There was an error downloading your video, sorry.")
                    return
                client = await channel.connect()
                self._play_song(client, state, video)
                if embed:
                    message = await ctx.send("", embed=video.get_embed())
                    await self._add_reaction_controls(message)
                logging.info(f"Now playing '{video.title}'")

            if client and client.channel:
                fn = yt_search_add_to_queue
            else:
                if not ctx.author.voice or not ctx.author.voice.channel:
                    raise commands.CommandError(
                        "You need to be in a voice channel to do that.")
                fn = yt_search_play
            if song:
                return await fn()
            else:
                web_playlist = self._import_playlist(url)
                if type(web_playlist) == str:
                    return await fn()
                else:
                    return await self._successful_playlist_import_text(ctx, web_playlist)

    async def on_reaction_add(self, reaction, user):
        """Responds to reactions added to the bot's messages, allowing reactions to control playback."""
        message = reaction.message
        if user != self.bot.user and message.author == self.bot.user:
            try:
                await message.remove_reaction(reaction, user)
            except discord.errors.Forbidden:
                pass
            if message.guild and message.guild.voice_client:
                user_in_channel = user.voice and user.voice.channel and user.voice.channel == \
                                  message.guild.voice_client.channel
                permissions = message.channel.permissions_for(user)
                guild = message.guild
                state = self.get_state(guild)
                if permissions.administrator or (
                        user_in_channel and state.is_requester(user)):
                    client = message.guild.voice_client
                    if reaction.emoji == "⏯":
                        # pause audio
                        self._pause_audio(client)
                    elif reaction.emoji == "⏭":
                        # skip audio
                        client.stop()
                    elif reaction.emoji == "⏮":
                        state.playlist.insert(
                            0, state.now_playing
                        )  # insert current song at beginning of playlist
                        client.stop()  # skip ahead
                elif reaction.emoji == "⏭" and conf[
                    "vote_skip"] and user_in_channel and message.guild.voice_client and \
                        message.guild.voice_client.channel:
                    # ensure that skip was pressed, that vote skipping is
                    # enabled, the user is in the channel, and that the bot is
                    # in a voice channel
                    voice_channel = message.guild.voice_client.channel
                    self._vote_skip(voice_channel, user)
                    # announce vote
                    channel = message.channel
                    users_in_channel = len([
                        member for member in voice_channel.members
                        if not member.bot
                    ])  # don't count bots
                    required_votes = math.ceil(
                        conf["vote_skip_ratio"] * users_in_channel)
                    await channel.send(
                        f"{user.mention} voted to skip ({len(state.skip_votes)}/{required_votes} votes)"
                    )

    async def _add_reaction_controls(self, message):
        """Adds a 'control-panel' of reactions to a message that can be used to control the bot."""
        CONTROLS = ["⏮", "⏯", "⏭"]
        for control in CONTROLS:
            await message.add_reaction(control)

    async def _add_multiple_songs(self, ctx, song_list, playlist_title, max_length=20):
        for song in song_list[:max_length]:
            logging.info(f'Adding {song} to the queue')
            async with ctx.typing():
                await self.play(ctx, url=song, embed=False, song=True)
        embed = discord.Embed(
            title=f'**{playlist_title}** added to queue')
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.avatar_url)
        message = await ctx.send("", embed=embed)
        await self._add_reaction_controls(message)

    def _search_for_playlist(self, ctx, playlist_name):
        try:
            playlist = Playlist.get(name=playlist_name)
        except Playlist.DoesNotExist:
            playlists = Playlist.select().where(Playlist.name.contains(playlist_name))
            if len(playlists) == 0:
                return 'No matching playlist found'
            if len(playlists) == 1:
                playlist = playlists.first()
            else:
                message = [f"**Found Multiple Matching Playlists - Please Specify:**"]
                message += [
                    f"  {index + 1}. **{playlist.name}** "
                    for (index, playlist) in enumerate(playlists)
                ]
                return "\n".join(message)
        return playlist

    @staticmethod
    async def _return_pl_search_message(ctx, message):
        return await ctx.send(message)

    async def _play_playlist(self, ctx, playlist, shuffle=False):
        songs = playlist.get_songs()
        logger.debug(f'Adding songs to playlist {songs}')
        song_list = [i.search_term for i in songs]
        if shuffle:
            random.shuffle(song_list)
        await self._add_multiple_songs(ctx, song_list, playlist.name)

    @commands.command(aliases=["pl"])
    async def playlist(self, ctx, *, playlist_name):
        """Adds the first 20 songs from the selected playlist to the queue"""
        logger.info(f'Searching for playlist "{playlist_name}"')
        playlist = self._search_for_playlist(ctx, playlist_name)
        if type(playlist) == str:
            logger.warning(f'Error finding playlist {playlist.error_message}')
            return await self._return_pl_search_message(ctx, playlist.error_message)
        else:
            return await self._play_playlist(ctx, playlist)

    @commands.command(aliases=['spl'])
    async def shuffle_playlist(self, ctx, *, playlist_name):
        """Shuffles a playlist"""
        playlist = self._search_for_playlist(ctx, playlist_name)
        await self._play_playlist(ctx, playlist, shuffle=True)

    @commands.command(aliases=["pls"])
    async def playlists(self, ctx):
        """Lists available playlists"""
        playlists = list(Playlist.select())
        message = [f"**Available Playlists:**"]
        message += [
            f"  {index + 1}. **{playlist.name}** "
            for (index, playlist) in enumerate(playlists)
        ]
        await ctx.send("\n".join(message))

    async def _successful_playlist_import_text(self, ctx, web_playlist):
        embed = discord.Embed(
            title=f'Successfully imported {web_playlist.name}!')
        embed.description = f'Added {web_playlist.song_count} songs to the database\n'
        embed.description += f'Play your new playlist by sending the command \n?pl {web_playlist.name}'
        if web_playlist.image_url:
            embed.set_image(url=web_playlist.image_url)
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.avatar_url)
        await ctx.send('', embed=embed)
        return await self._play_playlist(ctx, web_playlist.db_playlist)

    @commands.command(aliases=['import', 'impl'])
    async def import_playlist(self, ctx, url):
        """Imports a new playlist from a spotify URL"""
        web_playlist = self._import_playlist(url)
        if type(web_playlist) == str:
            return await ctx.send(web_playlist)
        else:
            return await self._successful_playlist_import_text(ctx, web_playlist)

    @staticmethod
    def _import_playlist(url):
        """Imports a new playlist from a spotify URL"""
        url_parse = urllib.parse.urlparse(url)
        cleaned_url = url_parse._replace(params='')._replace(query='')._replace(fragment='')
        logger.info(f'Attempting to import playlist from {url}')
        if url_parse.netloc == 'open.spotify.com':
            web_playlist = SpotifyPlaylist(url)
        elif url_parse.netloc == 'soundcloud.com':
            web_playlist = SoundCloudPlaylist(url)
        else:
            logger.warning(f'Cannot download playlist from {url}')
            return f'Failed to import playlist, please check your URL. ' \
                   f'Only spotify and soundcloud are currently supported'
        if web_playlist:
            logger.info(f'Adding playlist songs to database')
            web_playlist.add_songs_to_db()
            return web_playlist
        else:
            return f'Failed to download playlist: {web_playlist.error_message}\nThis is probably a Ben problem.'

    @commands.command(aliases=['upl'])
    async def update_playlist(self, ctx, *, playlist_name, playlist=None):
        """Updates an existing playlist"""
        playlist = self._search_for_playlist(ctx, playlist_name)
        if type(playlist) == str:
            return await self._return_pl_search_message(ctx, playlist)
        else:
            old_num_songs = len(playlist.get_songs())
            spotify_playlist = SpotifyPlaylist(playlist.spotify_url)
            logging.info(f'Updating {playlist.name}')
            spotify_playlist.add_songs_to_db()
            playlist = self._search_for_playlist(ctx, playlist_name)
            new_num_songs = len(playlist.get_songs())
            if old_num_songs == new_num_songs:
                return await ctx.send(f'No new songs to import')
            else:
                embed = discord.Embed(
                    title=f'Successfully imported {spotify_playlist.name}!')
                embed.description = f'Imported {new_num_songs - old_num_songs} new songs to the database\n'
                embed.description += f'Play your new playlist by sending the command \n?pl {spotify_playlist.name}'
                if spotify_playlist.image_url:
                    embed.set_image(url=spotify_playlist.image_url)
                embed.set_footer(
                    text=f"Requested by {ctx.author.name}",
                    icon_url=ctx.author.avatar_url)
                return await ctx.send('', embed=embed)


class GuildState:
    """Helper class managing per-guild state."""

    def __init__(self):
        self.volume = 1.0
        self.playlist = []
        self.skip_votes = set()
        self.now_playing = None

    def is_requester(self, user):
        return self.now_playing.requested_by == user


def setup(bot):
    bot.add_cog(MusicCog(bot))
