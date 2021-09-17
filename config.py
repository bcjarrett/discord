import json


class Config:

    def __init__(self):
        try:
            with open('secrets.json') as env:
                self.json_secrets = json.loads(env.read())
        except (IOError, json.decoder.JSONDecodeError):
            self.json_secrets = None

    def __getitem__(self, item):
        try:
            return self.json_secrets[item]
        except KeyError:
            raise KeyError(f'{item} is not in the secrets file')

    def __setitem__(self, key, value):
        self.json_secrets[key] = value


conf = Config()

# Define attached cogs here
conf['COGS'] = [
    'p00p',
    # 'game_tracker',
    'music',
    'mgmt'
]

# Database
conf['DATABASE'] = 'dheads.db'

conf['VC_IDS'] = [
    793590574598717449,
    813923491388194837,
    797607599138406480,
    805533627537686578,
    797624713165144124,
    818280367618261002
]

conf['STEAM_API_URL'] = 'https://store.steampowered.com/api/appdetails?language=en&lang=en&appids='

conf['LOGGING_CONFIG'] = {
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
conf['MAX_VOLUME'] = 250
conf['VOTE_SKIP'] = True
conf['VOTE_SKIP_RATIO'] = .5
