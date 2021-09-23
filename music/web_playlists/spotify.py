import logging

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import SPOTIFY_REDIRECT_URI, SPOTIFY_CLIENT_SECRET, SPOTIFY_CLIENT_ID
from .playlists import WebPlaylist, PlaylistException

logger = logging.getLogger(__name__)


class SpotifyPlaylist(WebPlaylist):
    def __init__(self, url):
        super().__init__(url)
        self.sp = self._spotify()
        self.data = {}
        self.uri = ''
        self.tracks = []
        self.error_message = ''
        self._get_data()

    @staticmethod
    def _spotify():
        scope = "user-library-read"
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                scope=scope,
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI
            )
        )

    def _get_data(self):
        try:
            self.data = self.sp.playlist(self.cleaned_url)
            self.name = self.data['name']
            self.owner = self.data['owner']['display_name']
            self.name = f'{self.name} - {self.owner} (Spotify)'
            self.uri = self.data['uri']
            self.web_id = self.data['id']
            self.url = self.data['external_urls']['spotify']
            self.image_url = self._parse_image_url()
            self.tracks = self._get_tracks()
        except spotipy.exceptions.SpotifyException as e:
            self.error_message = e
            raise PlaylistException(f'Spotipy Error: {e}')

    @staticmethod
    def _reduce_song(song):
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
        track_info = []
        for track in tracks:
            track = self._reduce_song(track)
            name = track[0]
            artists = track[1]
            url = None
            track_info.append((url, name, artists))
        return track_info

    def _parse_image_url(self):
        try:
            return self.data['images'][0]['url']
        except:
            return None
