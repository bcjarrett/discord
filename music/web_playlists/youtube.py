import logging
from urllib import parse

from pytube import Playlist as PyTubePlaylist

from .playlists import PlaylistException, WebPlaylist

logger = logging.getLogger(__name__)


class YoutubePlaylist(WebPlaylist):
    def __init__(self, url):
        super().__init__(url)
        self.web_id = self._get_playlist_id()
        self.data = self._get_playlist_data()
        self.tracks = self._get_tracks()
        self.name = f'{self.data.title} - {self.owner} (YouTube)'
        self.owner = self.data.owner
        self.image_url = None

    def _get_playlist_id(self):
        url_parse = parse.urlparse(self.url)
        try:
            url_query = url_parse.query.split('&')
            list_info = [i for i in url_query if i[:5] == 'list='][0]
            return list_info.split('=')[1]
        except (ValueError, IndexError):
            self.error_message = 'Unable to parse url for playlist id'
            raise PlaylistException(self.error_message)

    def _clean_url(self):
        url_parse = parse.urlparse(self.url)
        playlist_id = self._get_playlist_id()
        cleaned_url = url_parse._replace(params='')._replace(query=f'list={playlist_id}')._replace(fragment='')
        return cleaned_url.geturl()

    def _get_playlist_data(self):
        try:
            return PyTubePlaylist(self.cleaned_url)
        except KeyError:
            self.error_message = 'Unable to parse url for playlist id'
            raise PlaylistException(self.error_message)

    def _get_tracks(self):  # return [(url, track_name, [artists]), ...]
        videos = self.data.videos
        video_info = []
        for video in videos:
            url = video.watch_url
            track_name = video.title
            artist = [video.author]
            video_info.append((url, track_name, artist))
        return video_info
