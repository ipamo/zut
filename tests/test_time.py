
from __future__ import annotations
import sys
from unittest import TestCase, skipIf
from datetime import datetime, timezone, time, timedelta
from zut import make_aware, is_aware, parse_tz, tzlocal, tzdata, pytz

class Case(TestCase):
    def test_make_aware_with_specified_timezone(self):
        self.assertEqual(False, is_aware(datetime.fromisoformat('1980-01-01T00:00:00')))
        self.assertEqual(False, is_aware(time.fromisoformat('12:00:00')))

        self.assertEqual(True, is_aware(datetime.fromisoformat('1980-01-01T00:00:00+02:00')))
        self.assertEqual(True, is_aware(time.fromisoformat('12:00:00+02:00')))

        # make aware on a given timezone
        self.assertEqual(datetime.fromisoformat('1980-01-01T00:00:00+02:00'), make_aware(datetime.fromisoformat('1980-01-01T00:00:00'), timezone(timedelta(hours=2))))
        self.assertEqual(time.fromisoformat('12:00:00+02:00'), make_aware(time.fromisoformat('12:00:00'), timezone(timedelta(hours=2))))


    @skipIf((sys.version_info < (3, 9) or sys.platform == 'win32') and not tzlocal, "tzlocal not available")
    def test_make_aware_for_local_timezone(self):
        tz = parse_tz('localtime', explicit_local=True)

        def offset_to_isosuffix(offset: timedelta):
            sign = '+'
            seconds = offset.total_seconds()
            if seconds < 0:
                sign = '-'
                offset = timedelta(seconds=-seconds)
        
            return sign + str(offset)[:-3].rjust(5, '0')
            
        
        winter_offset = offset_to_isosuffix(tz.utcoffset(datetime.fromisoformat('1980-01-01')))
        summer_offset = offset_to_isosuffix(tz.utcoffset(datetime.fromisoformat('1980-07-01')))
        
        self.assertEqual(datetime.fromisoformat(f'1980-01-01T00:00:00{winter_offset}'), make_aware(datetime.fromisoformat('1980-01-01T00:00:00'))) # winter time
        self.assertEqual(datetime.fromisoformat(f'1980-07-01T00:00:00{summer_offset}'), make_aware(datetime.fromisoformat('1980-07-01T00:00:00'))) # summer time

        time_naive = time.fromisoformat('12:00:00')
        time_aware = make_aware(time_naive)
        self.assertEqual(time_aware.hour, time_naive.hour)
        self.assertEqual(tz.utcoffset(datetime.now()), time_aware.tzinfo.utcoffset(datetime.now())) # we cannot determine the offset because we need a date: for example it might be '12:00:00+02:00' or '12:00:00+01:00' depending on whether we're in summer or winter


    @skipIf(sys.version_info < (3, 9) and not pytz, "pytz not available")
    @skipIf(sys.version_info >= (3, 9) and sys.platform == 'win32' and not tzdata, "tzdata not available")
    def test_parse_tz_from_str(self):
        tz = parse_tz('Europe/Paris')
        self.assertEqual(make_aware(datetime.fromisoformat('1980-01-01T00:00:00'), tz).isoformat(), '1980-01-01T00:00:00+01:00')
