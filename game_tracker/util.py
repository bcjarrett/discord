import re
import json
import aiohttp
from bs4 import BeautifulSoup
from dateutil import parser

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/61.0.3163.100 Safari/537.36'}


steam_api_url = f'https://store.steampowered.com/api/appdetails?language=en&lang=en&appids='


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


def _add_field(_embed, name, value, inline):
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


async def get_steam_game_info(app_id):
    async with aiohttp.ClientSession() as session:

        async with session.get(f'{steam_api_url}{app_id}', headers=headers) as r:
            if r.status == 200:
                text = await r.read()
                content = json.loads(text)

                if content[str(app_id)]['success'] is True:
                    data = content[str(app_id)]['data']
                    tags = []
                    game_name = data['name']
                    is_free = data['is_free']
                    if is_free:
                        tags.append('Free')
                    else:
                        try:
                            price = data['price_overview']['final_formatted']
                            tags.append(price)
                        except KeyError:
                            pass
                    categories = data['categories']
                    cats_we_care_about = [1, 9, 38, 39]
                    for i in categories:
                        for c in cats_we_care_about:
                            if c == i['id']:
                                tags.append(i['description'])
                    release_date_str = data['release_date']['date']
                    try:
                        release_date_obj = parser.parse(release_date_str)
                    except (parser._parser.ParserError, TypeError):
                        release_date_obj = None

                    tags = ', '.join(tags)
                    return game_name, release_date_str, release_date_obj, tags
            return None, None, None, None


async def update_game(game, x=0):
    banned_chars = 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя€₴'
    x = x
    if game.steam_id:
        app_name, release_date_str, release_date_obj, tags = await get_steam_game_info(game.steam_id)
        if any(match in tags for match in [i for i in banned_chars]):
            x += 1
            print(app_name, x)
            await update_game(game, x=x)
        if release_date_obj:
            game.release_date_obj = release_date_obj
        if release_date_str:
            game.release_date_str = release_date_str
        if tags:
            game.tags = tags
        game.save()
