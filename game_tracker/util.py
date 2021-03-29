import json
import re

import aiohttp
from bs4 import BeautifulSoup
from dateutil import parser
from config import conf

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/61.0.3163.100 Safari/537.36'}

steam_api_url = conf['STEAM_API_URL']


def content_squinch(content, content_list, length=1000):
    temp_length = 0
    _slice = 0
    for n, i in enumerate(content):
        if len(i) + temp_length < length:
            _slice += 1
            temp_length += len(i)
        else:
            content_list.append(content[0:_slice])
            return content_list, content[_slice:]
    content_list.append(content[0:_slice])
    return content_list, content[_slice:]


def add_field(_embed, name, value, inline):
    if len(value) > 1000:
        content = value.split('\n')
        final_content = []
        while content:
            final_content, content = content_squinch(content, final_content)
        for n, i in enumerate(final_content):
            if n == 0:
                _embed.add_field(name=f'{name}', value='\n'.join(i), inline=inline)
            else:
                _embed.add_field(name=f'\t...(contd.)', value='\n'.join(i), inline=inline)

    else:
        _embed.add_field(name=f'{name}', value=value, inline=inline)


async def search_game(title, number_results=10, language_code='en'):
    google_url = 'https://www.google.com/search?q={}&num={}&hl={}'.format(title.replace(" ", "+") + 'steam game',
                                                                          number_results + 1,
                                                                          language_code)

    async with aiohttp.ClientSession() as session:
        async with session.get(google_url, headers=headers) as r:
            if r.status == 200:
                text = await r.read()
            else:
                text = ''

        soup = BeautifulSoup(text, 'html.parser')
        result_block = soup.find_all('div', attrs={'class': 'g'})
        games = []
        for result in result_block:
            link = result.find('a', href=True)
            title = result.find('h3')
            if link and title:
                games.append(link['href'])
        game = games[0]
        if re.search(r'store\.steampowered\.com/app/[0-9]*', game):
            return game
        else:
            return None


async def parse_steam_game_info(data):
    if data:
        game_name = data['name']
        tags = []
        price = None
        release_date_str = None
        release_date_obj = None

        # Price
        if data['is_free']:
            price = 'Free'
        else:
            try:
                price = data['price_overview']['final_formatted']
            except KeyError:
                pass

        # Tags
        categories = data['categories']
        cats_we_care_about = [1, 9, 38, 39]
        for i in categories:
            for c in cats_we_care_about:
                if c == i['id']:
                    tags.append(i['description'])

        # Release Dates
        try:
            release_date_str = data['release_date']['date']
        except KeyError:
            pass
        try:
            release_date_obj = parser.parse(release_date_str)
        except (parser._parser.ParserError, TypeError):
            pass

        tags = ', '.join(tags)
        return game_name, release_date_str, release_date_obj, price, tags
    return None, None, None, None, None


async def get_steam_game_info(app_id):
    async with aiohttp.ClientSession() as session:

        async with session.get(f'{steam_api_url}{app_id}', headers=headers) as r:
            if r.status == 200:
                text = await r.read()
                content = json.loads(text)

                if content[str(app_id)]['success'] is True:
                    data = content[str(app_id)]['data']
                    return data
            return None


async def update_game(game):
    if game.steam_id:
        app_name, release_date_str, release_date_obj, price, tags = await get_steam_game_info(game.steam_id)
        if release_date_obj:
            game.release_date_obj = release_date_obj
        if release_date_str:
            game.release_date_str = release_date_str
        if tags:
            game.tags = tags
        if price:
            game.price = price
        game.save()


def make_games_content(games_list):
    content = []
    for g in games_list:
        tags = f'({g.simple_tags})' if g.simple_tags else ''
        if g.url:
            content.append(f'[{g.name.title()}]({g.url}) {tags}')
        else:
            content.append(f'{g.name.title()} {tags}')
    return '\n'.join(content)


def add_games_list_to_embed(embed, section):
    """section must be a tuple of the form (header, list_of_game_objects)"""
    content = make_games_content(section[1])
    add_field(embed, name=section[0], value=content, inline=False) if content else None
    return embed
