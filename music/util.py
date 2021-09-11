import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import conf
from .models import Artist, ArtistSong, Playlist, PlaylistSong, Song


class SpotifyPlaylist:
    def __init__(self, url):
        self.sp = self._spotify()
        self.url = url
        self.data = {}
        self.name = ''
        self.uri = ''
        self.owner = ''
        self.db_name = ''
        self.id = ''
        self.image_url = ''
        self.tracks = []
        self.song_count = 0
        self.db_playlist = None
        self.error_message = ''
        self._get_data()

    def __bool__(self):
        return True if self.data else False

    @staticmethod
    def _spotify():
        scope = "user-library-read"
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=scope,
                client_id=conf['SPOTIFY_CLIENT_ID'],
                client_secret=conf['SPOTIFY_CLIENT_SECRET'],
                redirect_uri=conf['SPOTIFY_REDIRECT_URI']
            )
        )

    def _get_data(self):
        try:
            self.data = self.sp.playlist(self.url)
            self.name = self.data['name']
            self.uri = self.data['uri']
            self.owner = self.data['owner']['display_name']
            self.db_name = f'{self.name} - {self.owner}'
            self.id = self.data['id']
            self.url = self.data['external_urls']['spotify']
            self.image_url = self._parse_image_url()
            self.tracks = self._get_tracks()
            self.song_count = len(self.tracks)
        except spotipy.exceptions.SpotifyException as e:
            self.error_message = e

    @staticmethod
    def reduce_song(song):
        try:
            song = song['track']
        except:
            song = None
        if song:
            name = None
            artist_list = []
            try:
                name = song['name']
            except KeyError:
                name = None
            try:
                artists = song['artist']
            except KeyError:
                try:
                    artists = song['artists']
                except KeyError:
                    artists = None
            if artists:
                for i in artists:
                    try:
                        artist_list.append(i['name'])
                    except KeyError:
                        pass
            artist_list = list(set(artist_list))
            return name, artist_list

    def _get_tracks(self):
        offset = 0
        tracks = []
        while True:

            response = self.sp.playlist_items(self.uri,
                                              offset=offset,
                                              fields='items.track',
                                              additional_types=['track'])
            if len(response['items']) == 0:
                break

            tracks += response['items']

            offset = offset + len(response['items'])
        return tracks

    def _parse_image_url(self):
        try:
            return self.data['images'][0]['url']
        except:
            return None

    def create_or_update_playlist(self):
        db_playlist = Playlist.select().where(Playlist.spotify_id == self.id).first()
        if not db_playlist:
            db_playlist = Playlist.create(
                name=self.db_name,
                spotify_id=self.id,
                spotify_url=self.url,
                owner=self.owner,
                image_url=self.image_url
            )
        else:
            db_playlist.update(
                name=self.db_name,
                spotify_url=self.url,
                owner=self.owner,
                image_url=self.image_url
            )
        self.db_playlist = db_playlist

    def add_songs_to_db(self):
        if not self.db_playlist:
            self.create_or_update_playlist()

        for track in self.tracks:
            track = self.reduce_song(track)
            if track:
                db_track = Song.get_or_create(name=track[0])
                for art in track[1]:
                    artist = Artist.get_or_create(name=art)
                    ArtistSong.get_or_create(artist=artist[0].id, song=db_track[0].id)
                PlaylistSong.get_or_create(playlist=self.db_playlist.id, song=db_track[0].id)
