""""""
import datetime
from typing import List, Optional, Sequence, Type
import pandas as pd
from peewee import (
    AutoField,
    CharField,
    Database,
    DateTimeField,
    FloatField,
    Model,
    MySQLDatabase,
    PostgresqlDatabase,
    SqliteDatabase,
    chunked,
    IntegerField
)
from pandas_market_calendars import get_calendar
from vnpy.trader.constant import Exchange, Interval, EXCHANGE_CALENDAR
from vnpy.trader.object import BarData, TickData
from vnpy.trader.utility import get_file_path, get_folder_path
from .database import BaseDatabaseManager, Driver
from vnpy.bcolz_table.minute_bars import (
    BcolzMinuteBarWriter, 
    BcolzMinuteBarReader, 
    BcolzMinuteBarMetadata,
    minute_to_session_label,
    BcolzMinuteOverlappingData,
    US_EQUITIES_MINUTES_PER_DAY,
    OHLC_RATIO
)
import pytz
from dateutil.tz import tzlocal

local_tz = tzlocal()

def get_date_range(calendar, start_date: pd.Timestamp, end_date: pd.Timestamp):
    
    count = end_date.year - start_date.year 
    base_year = start_date.year
    pair = []
    
    for i in range(count + 1):
        year = base_year + i
        if i == 0:
            # start_t = start_date
            start_t = minute_to_session_label(calendar, start_date, direction='previous')
        else:
            start_t = datetime.datetime(year=year, month=1, day=1)
        
        if i == count:
            # end_t = end_date + datetime.timedelta(hours=1)
            end_t = minute_to_session_label(calendar, end_date)
        else:
            end_t = datetime.datetime(year=year+1, month=1, day=1) - datetime.timedelta(seconds=1)
        
        schedule = calendar.schedule(start_t, end_t)
        pair.append((schedule.market_open[0], schedule.market_close[-1]))
    return pair

def init(driver: Driver, settings: dict):

    database = settings["database"]
    store_path = str(get_folder_path('db_store'))
    path = str(get_file_path(database))
    db = SqliteDatabase(path)
    bcolz_meta, bar, tick = init_models(db, driver)
    return SqlManager(store_path, bcolz_meta, bar, tick)

class ModelBase(Model):
    def to_dict(self):
        return self.__data__
        

def init_models(db: Database, driver: Driver):

    class BcolzMeta(ModelBase):
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
                (('symbol', 'exchange', 'year'), True),
            )

    class DbBarData:
        """
        Candlestick bar data for database storage.

        Index is defined unique with datetime, interval, symbol
        """
        fields = ['open', 'open_int', 'high', 'low', 'close', 'volume']
        @staticmethod
        def from_bar(bar: BarData):
            """
            Generate DbBarData object from BarData.
            """
            db_bar = dict(
                index = bar.datetime,
                volume = bar.volume,
                open_int = bar.open_interest,
                open = bar.open_price,
                high = bar.high_price,
                low = bar.low_price,
                close = bar.close_price
            )

            return db_bar

        def to_bar(self, symbol, exchange, data):
            """
            Generate BarData object from DbBarData.
            """
            bar = BarData(
                symbol=self.symbol,
                exchange=Exchange(self.exchange),
                datetime=data.datetime,
                interval=Interval(Interval.MINUTE),
                volume=data.volume,
                open_price=data.open,
                high_price=data.high,
                open_interest=data.open_int,
                low_price=data.low,
                close_price=data.close,
                gateway_name="DB",
            )
            return bar

        # @staticmethod
        # def save_all(objs: List["DbBarData"]):
        #     """
        #     save a list of objects, update if exists.
        #     """
        #     dicts = [i.to_dict() for i in objs]
        #     with db.atomic():
        #         if driver is Driver.POSTGRESQL:
        #             for bar in dicts:
        #                 DbBarData.insert(bar).on_conflict(
        #                     update=bar,
        #                     conflict_target=(
        #                         DbBarData.symbol,
        #                         DbBarData.exchange,
        #                         DbBarData.interval,
        #                         DbBarData.datetime,
        #                     ),
        #                 ).execute()
        #         else:
        #             for c in chunked(dicts, 50):
        #                 DbBarData.insert_many(
        #                     c).on_conflict_replace().execute()

    class DbTickData:
        """
        Tick data for database storage.

        Index is defined unique with (datetime, symbol)
        """

        id = AutoField()

        symbol: str = CharField()
        exchange: str = CharField()
        datetime: datetime = DateTimeField()

        name: str = CharField()
        volume: float = FloatField()
        open_interest: float = FloatField()
        last_price: float = FloatField()
        last_volume: float = FloatField()
        limit_up: float = FloatField()
        limit_down: float = FloatField()

        open_price: float = FloatField()
        high_price: float = FloatField()
        low_price: float = FloatField()
        pre_close: float = FloatField()

        bid_price_1: float = FloatField()
        bid_price_2: float = FloatField(null=True)
        bid_price_3: float = FloatField(null=True)
        bid_price_4: float = FloatField(null=True)
        bid_price_5: float = FloatField(null=True)

        ask_price_1: float = FloatField()
        ask_price_2: float = FloatField(null=True)
        ask_price_3: float = FloatField(null=True)
        ask_price_4: float = FloatField(null=True)
        ask_price_5: float = FloatField(null=True)

        bid_volume_1: float = FloatField()
        bid_volume_2: float = FloatField(null=True)
        bid_volume_3: float = FloatField(null=True)
        bid_volume_4: float = FloatField(null=True)
        bid_volume_5: float = FloatField(null=True)

        ask_volume_1: float = FloatField()
        ask_volume_2: float = FloatField(null=True)
        ask_volume_3: float = FloatField(null=True)
        ask_volume_4: float = FloatField(null=True)
        ask_volume_5: float = FloatField(null=True)

        # class Meta:
        #     database = db
        #     indexes = ((("symbol", "exchange", "datetime"), True),)

        @staticmethod
        def from_tick(tick: TickData):
            """
            Generate DbTickData object from TickData.
            """
            db_tick = DbTickData()

            db_tick.symbol = tick.symbol
            db_tick.exchange = tick.exchange.value
            db_tick.datetime = tick.datetime
            db_tick.name = tick.name
            db_tick.volume = tick.volume
            db_tick.open_interest = tick.open_interest
            db_tick.last_price = tick.last_price
            db_tick.last_volume = tick.last_volume
            db_tick.limit_up = tick.limit_up
            db_tick.limit_down = tick.limit_down
            db_tick.open_price = tick.open_price
            db_tick.high_price = tick.high_price
            db_tick.low_price = tick.low_price
            db_tick.pre_close = tick.pre_close

            db_tick.bid_price_1 = tick.bid_price_1
            db_tick.ask_price_1 = tick.ask_price_1
            db_tick.bid_volume_1 = tick.bid_volume_1
            db_tick.ask_volume_1 = tick.ask_volume_1

            if tick.bid_price_2:
                db_tick.bid_price_2 = tick.bid_price_2
                db_tick.bid_price_3 = tick.bid_price_3
                db_tick.bid_price_4 = tick.bid_price_4
                db_tick.bid_price_5 = tick.bid_price_5

                db_tick.ask_price_2 = tick.ask_price_2
                db_tick.ask_price_3 = tick.ask_price_3
                db_tick.ask_price_4 = tick.ask_price_4
                db_tick.ask_price_5 = tick.ask_price_5

                db_tick.bid_volume_2 = tick.bid_volume_2
                db_tick.bid_volume_3 = tick.bid_volume_3
                db_tick.bid_volume_4 = tick.bid_volume_4
                db_tick.bid_volume_5 = tick.bid_volume_5

                db_tick.ask_volume_2 = tick.ask_volume_2
                db_tick.ask_volume_3 = tick.ask_volume_3
                db_tick.ask_volume_4 = tick.ask_volume_4
                db_tick.ask_volume_5 = tick.ask_volume_5

            return db_tick

        def to_tick(self):
            """
            Generate TickData object from DbTickData.
            """
            tick = TickData(
                symbol=self.symbol,
                exchange=Exchange(self.exchange),
                datetime=self.datetime,
                name=self.name,
                volume=self.volume,
                open_interest=self.open_interest,
                last_price=self.last_price,
                last_volume=self.last_volume,
                limit_up=self.limit_up,
                limit_down=self.limit_down,
                open_price=self.open_price,
                high_price=self.high_price,
                low_price=self.low_price,
                pre_close=self.pre_close,
                bid_price_1=self.bid_price_1,
                ask_price_1=self.ask_price_1,
                bid_volume_1=self.bid_volume_1,
                ask_volume_1=self.ask_volume_1,
                gateway_name="DB",
            )

            if self.bid_price_2:
                tick.bid_price_2 = self.bid_price_2
                tick.bid_price_3 = self.bid_price_3
                tick.bid_price_4 = self.bid_price_4
                tick.bid_price_5 = self.bid_price_5

                tick.ask_price_2 = self.ask_price_2
                tick.ask_price_3 = self.ask_price_3
                tick.ask_price_4 = self.ask_price_4
                tick.ask_price_5 = self.ask_price_5

                tick.bid_volume_2 = self.bid_volume_2
                tick.bid_volume_3 = self.bid_volume_3
                tick.bid_volume_4 = self.bid_volume_4
                tick.bid_volume_5 = self.bid_volume_5

                tick.ask_volume_2 = self.ask_volume_2
                tick.ask_volume_3 = self.ask_volume_3
                tick.ask_volume_4 = self.ask_volume_4
                tick.ask_volume_5 = self.ask_volume_5

            return tick

        @staticmethod
        def save_all(objs: List["DbTickData"]):
            dicts = [i.to_dict() for i in objs]
            with db.atomic():
                if driver is Driver.POSTGRESQL:
                    for tick in dicts:
                        DbTickData.insert(tick).on_conflict(
                            update=tick,
                            conflict_target=(
                                DbTickData.symbol,
                                DbTickData.exchange,
                                DbTickData.datetime,
                            ),
                        ).execute()
                else:
                    for c in chunked(dicts, 50):
                        DbTickData.insert_many(c).on_conflict_replace().execute()

    db.connect()
    db.create_tables([BcolzMeta])
    return BcolzMeta, DbBarData, DbTickData


class SqlManager(BaseDatabaseManager):

    def __init__(self, store_path, bcolz_meta: Type[Model], class_bar: Type[Model], class_tick: Type[Model]):
        self.store_path = store_path
        self.bcolz_meta = bcolz_meta
        self.class_bar = class_bar
        self.class_tick = class_tick

    

    def load_tick_data(
        self, symbol: str, exchange: Exchange, start: datetime, end: datetime
    ) -> Sequence[TickData]:
        s = (
            self.class_tick.select()
                .where(
                (self.class_tick.symbol == symbol)
                & (self.class_tick.exchange == exchange.value)
                & (self.class_tick.datetime >= start)
                & (self.class_tick.datetime <= end)
            )
            .order_by(self.class_tick.datetime)
        )

        data = [db_tick.to_tick() for db_tick in s]
        return data

    def save_bar_data(self, datas: Sequence[BarData]):
        if datas.__len__() == 0:
            return
        first = datas[0]
        symbol = first.symbol
        exchange = first.exchange
        calendar_name = EXCHANGE_CALENDAR[exchange]
        ds = [self.class_bar.from_bar(i) for i in datas]
        df = pd.DataFrame(ds)
        df.set_index(['index'], inplace=True)
        df.index = df.index.tz_localize(local_tz).tz_convert('UTC')
        start = df.index[0]
        end = df.index[-1]
        calendar = get_calendar(calendar_name)
        start_session = minute_to_session_label(calendar, start)
        end_session = minute_to_session_label(calendar, end)
        
        pair = get_date_range(calendar, start, end)

        for p in pair:
            year = p[0].year
            save_data = df.truncate(p[0], p[1])
            sid = None
            try:
                meta = self.bcolz_meta.get(self.bcolz_meta.symbol==symbol, self.bcolz_meta.exchange==exchange.value, self.bcolz_meta.year==year)
                sid = meta.sid
                meta_inst = BcolzMinuteBarMetadata.open(meta)
                writer = BcolzMinuteBarWriter.open( self.store_path, meta_inst)        
                writer.write_sid(sid, save_data)
                update = None
                if meta_inst.start_session > start_session:
                    meta.start_session = start_session
                    update = True
                if meta_inst.end_session < end_session:
                    meta.end_session = end_session
                    update = True
                if update is not None:
                    meta.save()


            except self.bcolz_meta.DoesNotExist:
                # BcolzMeta.insert(name='goog', exchange='smart', year=2018)
                meta = BcolzMinuteBarMetadata(OHLC_RATIO, calendar, start_session, end_session, US_EQUITIES_MINUTES_PER_DAY)
                r = self.bcolz_meta.insert(
                    symbol=symbol, 
                    exchange=exchange.value,
                    year=year, 
                    start_session=start_session.to_pydatetime(), 
                    end_session=end_session.to_pydatetime(),
                    calendar_name=calendar_name,
                    ohlc_ratio=OHLC_RATIO,
                    minutes_per_day=US_EQUITIES_MINUTES_PER_DAY,
                    version=meta.version
                    )
                sid = r.execute()
                writer = BcolzMinuteBarWriter(
                    self.store_path,
                    calendar,
                    p[0],
                    p[1],
                    US_EQUITIES_MINUTES_PER_DAY,
                )
                writer.write_sid(sid, save_data)    
            except BcolzMinuteOverlappingData:
                print('error')
            
        # self.class_bar.save_all(ds)
    def load_bar_data(
            self,
            symbol: str,
            exchange: Exchange,
            interval: Interval,
            start: datetime,
            end: datetime,
        ) -> Sequence[BarData]:
        calendar_name = EXCHANGE_CALENDAR[exchange]
        calendar = get_calendar(calendar_name)
        start_date = pd.Timestamp(start).tz_convert(pytz.utc)
        end_date = pd.Timestamp(end).tz_convert(pytz.utc)
        # start_session = minute_to_session_label(calendar, start)
        # end_session = minute_to_session_label(calendar, end)
        pair = get_date_range(calendar, start_date, end_date)
        final_data = []
        fields = self.class_bar.fields
        for p in pair:
            year = p[0].year
            try:
                meta = self.bcolz_meta.get(self.bcolz_meta.symbol==symbol, self.bcolz_meta.exchange==exchange.value, self.bcolz_meta.year==year)
                meta_inst = BcolzMinuteBarMetadata.open(meta)
                reader = BcolzMinuteBarReader(self.store_path, meta_inst)
                start_session = p[0] if p[0] >= reader.first_dt() else reader.first_dt()
                end_session = p[1] if p[1] < reader.last_dt() else reader.last_dt()

                result = reader.load_raw_arrays(fields, start_session, end_session, [meta.sid])
                print(result)
            except Exception as e:
                print(e)

        return final_data


    def save_tick_data(self, datas: Sequence[TickData]):
        ds = [self.class_tick.from_tick(i) for i in datas]
        self.class_tick.save_all(ds)

    def get_newest_bar_data(
        self, symbol: str, exchange: "Exchange", interval: "Interval"
    ) -> Optional["BarData"]:
        s = (
            self.class_bar.select()
                .where(
                (self.class_bar.symbol == symbol)
                & (self.class_bar.exchange == exchange.value)
                & (self.class_bar.interval == interval.value)
            )
            .order_by(self.class_bar.datetime.desc())
            .first()
        )
        if s:
            return s.to_bar()
        return None

    def get_newest_tick_data(
        self, symbol: str, exchange: "Exchange"
    ) -> Optional["TickData"]:
        s = (
            self.class_tick.select()
                .where(
                (self.class_tick.symbol == symbol)
                & (self.class_tick.exchange == exchange.value)
            )
            .order_by(self.class_tick.datetime.desc())
            .first()
        )
        if s:
            return s.to_tick()
        return None

    def clean(self, symbol: str):
        self.class_bar.delete().where(self.class_bar.symbol == symbol).execute()
        self.class_tick.delete().where(self.class_tick.symbol == symbol).execute()
