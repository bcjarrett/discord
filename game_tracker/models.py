import datetime

import peewee

from database import BaseModel


class GamesManager:
    """Helper methods for common queries"""

    def __init__(self):
        self._model = Game
        self.q = self._model.select()

    def new(self):
        self.q = self.q.where(
            self._model.started == 0,
            self._model.finished == 0
        )
        return self

    def old(self):
        self.q = self.q.where(
            self._model.started == 1,
            self._model.finished == 0
        )
        return self

    def released(self):
        self.q = self.q.where(
            self._model.release_date_obj <= (datetime.datetime.now())
        )
        return self

    def party(self):
        self.q = self.q.where(
            self._model.party_game == 1
        )
        return self

    def unreleased(self):
        self.q = self.q.where(
            (self._model.release_date_obj >= (datetime.datetime.now())) | (self._model.release_date_obj.is_null())
        )
        return self

    def finished(self):
        self.q = self.q.where(
            self._model.finished == 1
        )
        return self

    def players(self, num_players):
        if num_players:
            self.q = self.q.where(
                self._model.min_players <= num_players,
                self._model.max_players >= num_players
            )
        return self

    def call(self):
        order_args = [self._model.name]
        if '"started" = 1' in str(self.q):
            order_args.insert(0, -self._model.started_on)
        else:
            order_args.insert(0, self._model.added_on)
        return self.q.order_by(*order_args)


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
    min_players = peewee.IntegerField(default=None)
    max_players = peewee.IntegerField(default=None)
    party_game = peewee.BooleanField(default=False)
    price = peewee.CharField(default=None, null=True)

    @staticmethod
    def manager():
        return GamesManager()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

    @property
    def co_op(self):
        if 'co-op' in str(self.tags).lower() or 'coop' in str(self.tags).lower() or 'co op' in str(self.tags).lower():
            return True
        return False

    @property
    def multiplayer(self):
        if 'multi' in str(self.tags).lower():
            return True
        return False

    @property
    def simple_tags(self):
        price = self.price if (self.price and not self.started) else None
        party = 'Party Game' if self.party_game else None
        release_date = self.release_date_str if self.release_date_str else None

        players = None
        if self.min_players and self.max_players:
            if self.min_players == self.max_players:
                players = f'{self.min_players} players'
            else:
                players = f'{self.min_players}-{self.max_players} players'

        game_type = None

        co_op = self.co_op
        multi = self.multiplayer
        if co_op:
            game_type = 'Co-op'
        elif multi:
            game_type = 'Multiplayer'

        # Hide release date for released games
        if self.release_date_obj:
            if self.release_date_obj < datetime.datetime.now():
                release_date = None

        out_tags = [i for i in [price, game_type, party, players, release_date] if i]
        if out_tags:
            return ', '.join(out_tags)

        # If that all broke, give them whatever we have
        if self.tags:
            return str(self.tags).replace(',', ', ')

        # Or nothing
        return None

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
