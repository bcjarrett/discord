import json
import sys
import logging

logger = logging.getLogger(__name__)

# Secrets
DHEADS = None
TEST_SERVER = None
DISCORD_API_SECRET = None
STEAM_API_KEY = None
STEAM_API_DOMAIN = None
SPOTIFY_CLIENT_ID = None
SPOTIFY_CLIENT_SECRET = None
SPOTIFY_REDIRECT_URI = None

# Define attached cogs here
COGS = [
    'p00p',
    'game_tracker',
    'music',
    'mgmt'
]

# Database
DATABASE = 'dheads.db'
STEAM_API_URL = 'https://store.steampowered.com/api/appdetails?language=en&lang=en&appids='
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'stream': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': './log.log'
        }
    },
    'loggers': {
        '': {
            'handlers': ['stream', 'file'],
            'level': 'INFO',
            'propagate': False
        },
    }
}

# Music settings
MAX_VOLUME = 250
VOTE_SKIP = True
VOTE_SKIP_RATIO = .5
SOUNDCLOUD_BASE_URL = 'https://soundcloud.com'

# Status Options
BOT_STATUS = [
    'Extreme Jelking 2069',
    'Fart Master',
    'Furious Butt Rubbers',
    'Hairy Pooper',
    'Magic Muffin Tops',
    'The Cavern of Smells',
    'Smelly Belly',
    'Fantasy Farts',
    'Pie Party!',
    'Bashful Butt Pirates',
    'Fudge Packers EXPRESS',
    'Barndoor Bandits',
    'Butthole Bargain Hunter',
    'Grundle Bundlers',
]

# Load secrets.json

_config_module = sys.modules[__name__]
try:
    with open('secrets.json') as env:
        json_secrets = json.loads(env.read())
        for k, v in json_secrets.items():
            setattr(_config_module, k, v)
except (IOError, json.decoder.JSONDecodeError) as e:
    logger.error(f'Failed to load JSON secrets file: {e}')
    pass
