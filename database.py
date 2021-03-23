import pyclbr
from pydoc import locate

import peewee

from config import conf


class BaseModel(peewee.Model):
    class Meta:
        database = peewee.SqliteDatabase(conf['DATABASE'])


def db_setup():
    db = peewee.SqliteDatabase(conf['DATABASE'])
    db.connect()

    models = []

    for cog in conf['COGS']:
        try:
            module_info = pyclbr.readmodule(f'{cog}.models')
            for i in module_info.values():
                if 'BaseModel' in i.super:
                    models.append(locate(f'{cog}.models.{i.name}'))
        except ModuleNotFoundError:
            pass

    db.create_tables(models)
