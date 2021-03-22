from database import BaseModel
import peewee


class TextCount(BaseModel):
    text = peewee.CharField()
    counter = peewee.IntegerField()
    max_num = peewee.IntegerField()
    record_holder = peewee.CharField()
