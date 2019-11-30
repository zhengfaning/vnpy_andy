from __future__ import print_function

# Let's import the packages we need for this tutorial
from bcolz import ctable
from toolz import keymap, valmap
import numpy as np
import sys
import os
import json
import pandas as pd
from enum import Enum
from trading_calendars import get_calendar
US_EQUITIES_MINUTES_PER_DAY = 390
FUTURES_MINUTES_PER_DAY = 1440

DEFAULT_EXPECTEDLEN = US_EQUITIES_MINUTES_PER_DAY * 252 * 15

# Timing measurements will be saved here
# bcolz_vs_numpy = {}

# bcolz.print_versions()
# a = np.arange(10)
# b = bcolz.carray(a)
# # c = bcolz.carray(a, rootdir='mydir')
# # c.flush()
# d = bcolz.arange(10, rootdir='mydir', mode='w')
class ExchangeToCalendarLangure(Enum):
    SMART = 'XNYS'

class BcolzMinuteBarMetadata(object):
    """
    Parameters
    ----------
    ohlc_ratio : int
         The factor by which the pricing data is multiplied so that the
         float data can be stored as an integer.
    calendar :  trading_calendars.trading_calendar.TradingCalendar
        The TradingCalendar on which the minute bars are based.
    start_session : datetime
        The first trading session in the data set.
    end_session : datetime
        The last trading session in the data set.
    minutes_per_day : int
        The number of minutes per each period.
    """
    FORMAT_VERSION = 3

    METADATA_FILENAME = 'metadata.json'

    @classmethod
    def metadata_path(cls, rootdir):
        return os.path.join(rootdir, cls.METADATA_FILENAME)

    @classmethod
    def read(cls, rootdir):
        path = cls.metadata_path(rootdir)
        with open(path) as fp:
            raw_data = json.load(fp)

            try:
                version = raw_data['version']
            except KeyError:
                # Version was first written with version 1, assume 0,
                # if version does not match.
                version = 0

            default_ohlc_ratio = raw_data['ohlc_ratio']

            if version >= 1:
                minutes_per_day = raw_data['minutes_per_day']
            else:
                # version 0 always assumed US equities.
                minutes_per_day = US_EQUITIES_MINUTES_PER_DAY

            if version >= 2:
                calendar = get_calendar(raw_data['calendar_name'])
                start_session = pd.Timestamp(
                    raw_data['start_session'], tz='UTC')
                end_session = pd.Timestamp(raw_data['end_session'], tz='UTC')
            else:
                # No calendar info included in older versions, so
                # default to NYSE.
                calendar = get_calendar('XNYS')

                start_session = pd.Timestamp(
                    raw_data['first_trading_day'], tz='UTC')
                end_session = calendar.minute_to_session_label(
                    pd.Timestamp(
                        raw_data['market_closes'][-1], unit='m', tz='UTC')
                )

            # if version >= 3:
            #     ohlc_ratios_per_sid = raw_data['ohlc_ratios_per_sid']
            #     if ohlc_ratios_per_sid is not None:
            #         ohlc_ratios_per_sid = keymap(int, ohlc_ratios_per_sid)
            # else:
            #     ohlc_ratios_per_sid = None

            return cls(
                default_ohlc_ratio,
                # ohlc_ratios_per_sid,
                calendar,
                start_session,
                end_session,
                minutes_per_day,
                version=version,
            )

    def __init__(
        self,
        default_ohlc_ratio,
        # ohlc_ratios_per_sid,
        calendar,
        start_session,
        end_session,
        minutes_per_day,
        version=FORMAT_VERSION,
    ):
        self.calendar = calendar
        self.start_session = start_session
        self.end_session = end_session
        self.default_ohlc_ratio = default_ohlc_ratio
        # self.ohlc_ratios_per_sid = ohlc_ratios_per_sid
        self.minutes_per_day = minutes_per_day
        self.version = version

    def write(self, rootdir):
        """
        Write the metadata to a JSON file in the rootdir.

        Values contained in the metadata are:

        version : int
            The value of FORMAT_VERSION of this class.
        ohlc_ratio : int
            The default ratio by which to multiply the pricing data to
            convert the floats from floats to an integer to fit within
            the np.uint32. If ohlc_ratios_per_sid is None or does not
            contain a mapping for a given sid, this ratio is used.
        ohlc_ratios_per_sid : dict
             A dict mapping each sid in the output to the factor by
             which the pricing data is multiplied so that the float data
             can be stored as an integer.
        minutes_per_day : int
            The number of minutes per each period.
        calendar_name : str
            The name of the TradingCalendar on which the minute bars are
            based.
        start_session : datetime
            'YYYY-MM-DD' formatted representation of the first trading
            session in the data set.
        end_session : datetime
            'YYYY-MM-DD' formatted representation of the last trading
            session in the data set.

        Deprecated, but included for backwards compatibility:

        first_trading_day : string
            'YYYY-MM-DD' formatted representation of the first trading day
             available in the dataset.
        market_opens : list
            List of int64 values representing UTC market opens as
            minutes since epoch.
        market_closes : list
            List of int64 values representing UTC market closes as
            minutes since epoch.
        """

        calendar = self.calendar
        slicer = calendar.schedule.index.slice_indexer(
            self.start_session,
            self.end_session,
        )
        schedule = calendar.schedule[slicer]
        market_opens = schedule.market_open
        market_closes = schedule.market_close

        metadata = {
            'version': self.version,
            'ohlc_ratio': self.default_ohlc_ratio,
            # 'ohlc_ratios_per_sid': self.ohlc_ratios_per_sid,
            'minutes_per_day': self.minutes_per_day,
            'calendar_name': self.calendar.name,
            'start_session': str(self.start_session.date()),
            'end_session': str(self.end_session.date()),
            # Write these values for backwards compatibility
            'first_trading_day': str(self.start_session.date()),
            'market_opens': (
                market_opens.values.astype('datetime64[m]').
                astype(np.int64).tolist()),
            'market_closes': (
                market_closes.values.astype('datetime64[m]').
                astype(np.int64).tolist()),
        }
        with open(self.metadata_path(rootdir), 'w+') as fp:
            json.dump(metadata, fp)

class BcolzTable:

    def __init__(self):
        self._rootdir = os.path.abspath(os.path.dirname(__file__))
        self._expectedlen = DEFAULT_EXPECTEDLEN
    
    def symbol_path(self, symbol, exchange):
        """
        Parameters
        ----------
        sid : int
            Asset identifier.

        Returns
        -------
        out : string
            Full path to the bcolz rootdir for the given sid.
        """
        # sid_subdir = _sid_subdir_path(symbol, exchange)
        return os.path.join(self._rootdir, exchange, "{0}.bcolz".format(str(symbol)))

    def _ensure_ctable(self, symbol, exchange):
        """Ensure that a ctable exists for ``sid``, then return it."""
        sidpath = self.symbol_path(symbol, exchange)
        if not os.path.exists(sidpath):
            return self._init_ctable(sidpath)
        return ctable(rootdir=sidpath, mode='a')

    def _init_ctable(self, path):
        """
        Create empty ctable for given path.

        Parameters
        ----------
        path : string
            The path to rootdir of the new ctable.
        """
        # Only create the containing subdir on creation.
        # This is not to be confused with the `.bcolz` directory, but is the
        # directory up one level from the `.bcolz` directories.
        sid_containing_dirname = os.path.dirname(path)
        if not os.path.exists(sid_containing_dirname):
            # Other sids may have already created the containing directory.
            os.makedirs(sid_containing_dirname)
        initial_array = np.empty(0, np.uint32)
        table = ctable(
            rootdir=path,
            columns=[
                initial_array,
                initial_array,
                initial_array,
                initial_array,
                initial_array,
                initial_array,
                initial_array,
            ],
            names=[
                'datetime',
                'open_interest',
                'open',
                'high',
                'low',
                'close',
                'volume'
            ],
            expectedlen=self._expectedlen,
            mode='w',
        )
        table.flush()
        return table
    
    def last_date_in_output_for_sid(self, sid):
        """
            Parameters
            ----------
            sid : int
                Asset identifier.

            Returns
            -------
            out : pd.Timestamp
                The midnight of the last date written in to the output for the
                given sid.
        """
        sizes_path = "{0}/close/meta/sizes".format(self.sidpath(sid))
        if not os.path.exists(sizes_path):
            return pd.NaT
        with open(sizes_path, mode='r') as f:
            sizes = f.read()
        data = json.loads(sizes)
        # use integer division so that the result is an int
        # for pandas index later https://github.com/pandas-dev/pandas/blob/master/pandas/tseries/base.py#L247 # noqa
        num_days = data['shape'][0] // self._minutes_per_day
        if num_days == 0:
            # empty container
            return pd.NaT
        return self._session_labels[num_days - 1]

    def _write_cols(self, sid, dts, cols, invalid_data_behavior):
        """
        Internal method for `write_cols` and `write`.

        Parameters
        ----------
        sid : int
            The asset identifier for the data being written.
        dts : datetime64 array
            The dts corresponding to values in cols.
        cols : dict of str -> np.array
            dict of market data with the following characteristics.
            keys are ('open', 'high', 'low', 'close', 'volume')
            open : float64
            high : float64
            low  : float64
            close : float64
            volume : float64|int64
        """
        table = self._ensure_ctable(sid)

        tds = self._session_labels
        input_first_day = self._calendar.minute_to_session_label(
            pd.Timestamp(dts[0]), direction='previous')

        last_date = self.last_date_in_output_for_sid(sid)

        day_before_input = input_first_day - tds.freq

        self.pad(sid, day_before_input)
        table = self._ensure_ctable(sid)

        # Get the number of minutes already recorded in this sid's ctable
        num_rec_mins = table.size

        all_minutes = self._minute_index
        # Get the latest minute we wish to write to the ctable
        last_minute_to_write = pd.Timestamp(dts[-1], tz='UTC')

        # In the event that we've already written some minutely data to the
        # ctable, guard against overwriting that data.
        if num_rec_mins > 0:
            last_recorded_minute = all_minutes[num_rec_mins - 1]
            if last_minute_to_write <= last_recorded_minute:
                raise BcolzMinuteOverlappingData(dedent("""
                Data with last_date={0} already includes input start={1} for
                sid={2}""".strip()).format(last_date, input_first_day, sid))

        latest_min_count = all_minutes.get_loc(last_minute_to_write)

        # Get all the minutes we wish to write (all market minutes after the
        # latest currently written, up to and including last_minute_to_write)
        all_minutes_in_window = all_minutes[num_rec_mins:latest_min_count + 1]

        minutes_count = all_minutes_in_window.size

        open_col = np.zeros(minutes_count, dtype=np.uint32)
        high_col = np.zeros(minutes_count, dtype=np.uint32)
        low_col = np.zeros(minutes_count, dtype=np.uint32)
        close_col = np.zeros(minutes_count, dtype=np.uint32)
        vol_col = np.zeros(minutes_count, dtype=np.uint32)

        dt_ixs = np.searchsorted(all_minutes_in_window.values,
                                 dts.astype('datetime64[ns]'))

        ohlc_ratio = self.ohlc_ratio_for_sid(sid)

        (
            open_col[dt_ixs],
            high_col[dt_ixs],
            low_col[dt_ixs],
            close_col[dt_ixs],
            vol_col[dt_ixs],
        ) = convert_cols(cols, ohlc_ratio, sid, invalid_data_behavior)

        table.append([
            open_col,
            high_col,
            low_col,
            close_col,
            vol_col
        ])
        table.flush()