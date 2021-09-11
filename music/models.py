import peewee

from database import BaseModel


class Playlist(BaseModel):
    name = peewee.CharField(max_length=255)
    spotify_id = peewee.CharField(max_length=255)
    spotify_url = peewee.CharField(max_length=255)
    owner = peewee.CharField(max_length=255)
    image_url = peewee.CharField(max_length=255)

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return self.__str__()

    def get_songs(self):
        query = (Song
                 .select()
                 .join(PlaylistSong)
                 .join(Playlist)
                 .where(Playlist.id == self.id))
        return list(query)


class Song(BaseModel):
    name = peewee.CharField(max_length=255)
    url = peewee.CharField(max_length=255)

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return self.__str__()

    def get_artists(self):
        query = (Artist
                 .select()
                 .join(ArtistSong)
                 .join(Song)
                 .where(Song.id == self.id))
        return query

    @property
    def search_term(self):
        return self.url if self.url else f'{self.name} - {self.get_artists().first()}'


class Artist(BaseModel):
    name = peewee.CharField(max_length=255)

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return self.__str__()

    def get_songs(self):
        query = (Song
                 .select()
                 .join(ArtistSong)
                 .join(Artist)
                 .where(Artist.id == self.id))
        return list(query)


class PlaylistSong(BaseModel):
    playlist = peewee.ForeignKeyField(Playlist)
    song = peewee.ForeignKeyField(Song)


class ArtistSong(BaseModel):
    artist = peewee.ForeignKeyField(Artist)
    song = peewee.ForeignKeyField(Song)
