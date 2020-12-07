import peewee
import pyclbr
from pydoc import locate
from config import conf

db = peewee.SqliteDatabase(conf['DATABASE'])


# ID and load models
class BaseModel(peewee.Model):
    class Meta:
        database = db


db.connect()

models = []
for cog in conf['COGS']:
    module_info = pyclbr.readmodule(f'{cog}.models')
    for i in module_info.values():
        if 'BaseModel' in i.super:
            print(i.name)
            print(f'{cog}.models.{i.name}')
            models.append(locate(f'{cog}.models.{i.name}'))

print(models)
db.create_tables(models)
