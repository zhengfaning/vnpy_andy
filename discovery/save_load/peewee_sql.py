from peewee import (
    AutoField,
    CharField,
    Database,
    DateTimeField,
    FloatField,
    Model,
    IntegerField,
    MySQLDatabase,
    PostgresqlDatabase,
    SqliteDatabase,
    chunked
)
import datetime

path = "./test_db.db"
db = SqliteDatabase(path)


class BaseModel(Model):
    class Meta:
        database = db


class IDTable(BaseModel):
    sid = AutoField()
    symbol = CharField(null=False)
    exchange = CharField(null=False)
    year = IntegerField(null=False)
    ohlc_ratio = IntegerField(null=False)
    minutes_per_day = IntegerField(null=False)
    calendar_name = CharField(null=False)
    start_session = DateTimeField(null=False)
    end_session = DateTimeField(null=False)
    version = IntegerField(null=False)

    class Meta:
        database = db
        table_name = 'bcolz_meta'
        indexes = (
            # create a unique on from/to/date
            (('symbol', 'exchange', 'year'), True),)


db.create_tables([IDTable])


def insert():
    model = IDTable.insert(
        symbol='goog',
        exchange='smart',
        year=2019,
        start_session=datetime.datetime(2019,9,15),
        end_session=datetime.datetime(2019,11,15),
        calendar_name='NYSE',
        ohlc_ratio=1000,
        minutes_per_day=390,
        version=3
    )
    r = model.execute()
    model = IDTable.insert(name='goog', exchange='smart', year=2019)
    model = IDTable.insert(name='goog', exchange='smart', year=2016)
    r = model.execute()
    print(r)

def get():
    try:
        row = IDTable.get(IDTable.symbol == 'goog', IDTable.exchange == 'smart', IDTable.year == 2019)
        print(row)
    except:
        print('e')

def modify():
    try:
        row = IDTable.get(IDTable.symbol == 'goog', IDTable.exchange == 'smart', IDTable.year == 2019)
        row.end_session = datetime.datetime(2019,12,15)
        row.save()
        print(row)
    except:
        print('e')

modify()
