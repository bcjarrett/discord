import logging
import re

import bs4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from .playlists import WebPlaylist

logger = logging.getLogger(__name__)


class SoundCloudPlaylist(WebPlaylist):
    def __init__(self, url):
        super().__init__(url)
        self.base_url = 'https://soundcloud.com'
        self.web_id = self.cleaned_url
        self.bs = self._get_beautiful_soup()
        self.tracks = self._get_tracks()
        self.owner = self._get_owner()
        self.name = self._get_name()
        self.image_url = self._get_image_url()

    def _get_beautiful_soup(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options, executable_path='chromedriver.exe')
        driver.get(self.url)
        html = driver.page_source
        soup = bs4.BeautifulSoup(html, features='lxml')
        driver.quit()
        return soup

    def _get_owner(self):
        try:
            _owner = self.bs.find('h2', {'class': 'soundTitle__username'}).find('a').string.strip()
        except AttributeError:
            _owner = ''
        return _owner

    def _get_image_url(self):
        regex = r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][" \
                r"0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1," \
                r"4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1," \
                r"5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1," \
                r"4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1," \
                r"5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[" \
                r"0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0," \
                r"1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1," \
                r"4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0," \
                r"1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(" \
                r"?:/[\w\.-]*)*/?)\b"
        urls = re.findall(regex,
                          self.bs.find('div', {'class': 'fullHero__artwork'}).find('span',
                                                                                   {'class': 'sc-artwork'}).attrs.get(
                              'style'))[0]
        if urls:
            return urls
        else:
            return None

    def _get_tracks(self):
        try:
            artist = self.bs.find('a', {'class': 'userBadge__usernameLink'}).find('span').string
        except AttributeError:
            artist = None
        tracks = self.bs.find_all('div', {'class': 'trackItem__content'})
        track_info = []
        for t in tracks:
            if not artist:
                artist = t.find('a').string
            song_name = t.find_all('a')[-1].string
            url = t.find_all('a')[-1].attrs.get('href', '').split('?')[0]
            track_info.append(
                (
                    f'{self.base_url}{url}',
                    song_name,
                    [artist],
                )
            )
        return track_info

    def _get_name(self):
        _name = self.bs.find('h1', {'class': 'soundTitle__title'}).find('span').string
        return f'{_name} - {self.owner} (SoundCloud)'
