import peewee
import datetime

DATABASE = 'test.db'

db = peewee.SqliteDatabase(DATABASE)


class BaseModel(peewee.Model):
    class Meta:
        database = db


class TextCount(BaseModel):
    text = peewee.CharField()
    counter = peewee.IntegerField()


class Game(BaseModel):
    name = peewee.CharField()
    added_by = peewee.CharField()
    added_on = peewee.DateTimeField(default=datetime.datetime.now)
    played = peewee.BooleanField(default=False)
    url = peewee.CharField(null=False)


db.connect()
db.create_tables([TextCount, Game])
