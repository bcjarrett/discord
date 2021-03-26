import datetime

import peewee

from database import BaseModel


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
    release_date_str = peewee.CharField(default=None, null=True)
    release_date_obj = peewee.DateTimeField(default=None, null=True)
    tags = peewee.CharField(default=None, null=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    @property
    def simple_tags(self):
        price = None
        coop = False
        release_date = None
        multi = False
        out_tags = []
        tags = str(self.tags).split(',')

        # TODO: Refactor
        if self.release_date_obj:
            if self.release_date_obj > datetime.datetime.now():
                if self.release_date_str:
                    release_date = self.release_date_str
                elif self.release_date_obj:
                    release_date = self.release_date_obj

        if not self.release_date_obj:
            if self.release_date_str:
                release_date = self.release_date_str
            elif self.release_date_obj:
                release_date = self.release_date_obj

        if '$' in tags[0] and not self.started:
            price = tags[0]
        if 'co-op' in str(self.tags).lower() or 'coop' in str(self.tags).lower() or 'co op' in str(self.tags).lower():
            coop = 'Co-op'
        if 'multi' in str(self.tags).lower() and not coop:
            multi = 'Multiplayer'

        out_tags = [i for i in [price, coop, multi, release_date] if i]
        if out_tags:
            return ', '.join(out_tags)

        if self.tags:
            return str(self.tags).replace(',', ', ')

        return None

    # Not used
    # @property
    # def recent_activity(self):
    #     if not self.started:
    #         flag = 'added'
    #     elif not self.finished:
    #         flag = 'started'
    #     else:
    #         flag = 'finished'
    #
    #     prop = flag + '_on'
    #     date_diff = (datetime.datetime.now() - getattr(self, prop)).days
    #     return f' ({flag} {date_diff} day{plural(date_diff)} ago)' if date_diff else ''

    @staticmethod
    def get_game(in_str):
        in_str = in_str.lower()
        if not in_str:
            return 0, f'Please supply a game name'
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
