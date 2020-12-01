import datetime

import peewee

from util import plural
from config import conf

DATABASE = conf['DB_NAME']

db = peewee.SqliteDatabase(DATABASE)


class BaseModel(peewee.Model):
    class Meta:
        database = db


class TextCount(BaseModel):
    text = peewee.CharField()
    counter = peewee.IntegerField()


# New Games
class Game(BaseModel):
    name = peewee.CharField()
    added_by = peewee.CharField()
    added_on = peewee.DateTimeField(default=datetime.datetime.now)
    started = peewee.BooleanField(default=False)
    started_on = peewee.DateTimeField(null=True)
    finished = peewee.BooleanField(default=False)
    finished_on = peewee.DateTimeField(null=True)
    url = peewee.CharField(null=True)
    steam_id = peewee.BigIntegerField(null=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    @property
    def recent_activity(self):
        if not self.started:
            flag = 'added'
        elif not self.finished:
            flag = 'started'
        else:
            flag = 'finished'

        prop = flag + '_on'
        date_diff = (datetime.datetime.now() - getattr(self, prop)).days
        return f' ({flag} {date_diff} day{plural(date_diff)} ago)' if date_diff else ''

    @staticmethod
    def get_game(in_str):
        in_str = in_str.lower()
        try:
            return 1, Game.get(Game.name == in_str, Game.finished == False)
        except Game.DoesNotExist:
            game = list(Game.select().where(Game.name.contains(in_str), Game.finished == False))
            if len(game) > 1:
                return 0, f'More than one game returned for "{in_str}": {[i.name for i in game]}'
            if len(game) == 1:
                return 1, game[0]
            if len(game) == 0:
                return 0, f'No matching game for "{in_str}"'


db.connect()
db.create_tables([TextCount, Game])
