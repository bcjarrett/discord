from abc import ABC
from urllib import parse

from .models import Artist, ArtistSong, Playlist, PlaylistSong, Song


class WebPlaylist(ABC):
    def __init__(self, url):
        self.url = url
        self.cleaned_url = self._clean_url()
        self.name = ''
        self.web_id = ''
        self.owner = ''
        self.image_url = ''
        self.db_playlist = None
        self.error_message = f'Could not find any tracks for {url}. Are you sure it\'s a playlist?'
        self.tracks = []    # [(url, track_name, [artists]), ...]

    @property
    def song_count(self):
        return len(self.tracks)

    def __bool__(self):
        return True if self.tracks else False

    def _clean_url(self):
        url_parse = parse.urlparse(self.url)
        cleaned_url = url_parse._replace(params='')._replace(query='')._replace(fragment='')
        return cleaned_url.geturl()

    def create_or_update_playlist(self):
        db_playlist = Playlist.select().where(Playlist.web_id == self.web_id).first()
        if not db_playlist:
            db_playlist = Playlist.create(
                name=self.name,
                web_id=self.web_id,
                url=self.cleaned_url,
                owner=self.owner,
                image_url=self.image_url
            )
        else:
            db_playlist.update(
                name=self.name,
                url=self.cleaned_url,
                owner=self.owner,
                image_url=self.image_url
            )
        self.db_playlist = db_playlist

    def add_songs_to_db(self):
        # TODO: Does not "sync" songs, only adds new ones - e.g. a song is removed from the web playlist
        if not self.db_playlist:
            self.create_or_update_playlist()

        for track in self.tracks:
            url, name, artists = track
            if name:
                if url:
                    db_track = Song.get_or_create(url=url, defaults={'name': name})
                else:
                    # TODO: Collision on songs with the same name :(
                    db_track = Song.get_or_create(name=name)
                for artist in artists:
                    db_artist = Artist.get_or_create(name=artist)
                    ArtistSong.get_or_create(artist=db_artist[0].id, song=db_track[0].id)
                PlaylistSong.get_or_create(playlist=self.db_playlist.id, song=db_track[0].id)
