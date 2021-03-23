import datetime

import peewee

from database import BaseModel


class Reset(BaseModel):
    added_on = peewee.DateTimeField(default=datetime.datetime.now)
    channel_id = peewee.BigIntegerField(null=False)

    def __str__(self):
        return str(self.channel_id)

    def __repr__(self):
        return self.__str__()
