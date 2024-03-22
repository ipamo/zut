from __future__ import annotations
import json
from unittest import TestCase
from datetime import datetime, timedelta
from zut import ExtendedJSONEncoder

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
DATETIME_NAIVE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S.%f'


class Case(TestCase):
    def test_encode_datetime(self):
        # awaire (UTC) with microseconds
        encoded = json.dumps(datetime.strptime('2022-03-01T11:03:12.5583+0000', DATETIME_FORMAT), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"2022-03-01T11:03:12.558300Z"')

        # awaire (UTC) with milliseconds
        encoded = json.dumps(datetime.strptime('2022-03-01T11:03:12.55+0000', DATETIME_FORMAT), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"2022-03-01T11:03:12.550Z"')

        # awaire (UTC) without microseconds
        encoded = json.dumps(datetime.strptime('2022-03-01T11:03:12.0+0000', DATETIME_FORMAT), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"2022-03-01T11:03:12Z"')

        # awaire (Europe/Paris)
        encoded = json.dumps(datetime.strptime('2022-03-01T11:03:12.558300+0100', DATETIME_FORMAT), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"2022-03-01T11:03:12.558300+01:00"')

        # naive with microseconds
        encoded = json.dumps(datetime.strptime('2022-03-01T11:03:12.558300', DATETIME_NAIVE_FORMAT), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"2022-03-01T11:03:12.558300"')

        # naive without microseconds
        encoded = json.dumps(datetime.strptime('2022-03-01T11:03:12.0', DATETIME_NAIVE_FORMAT), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"2022-03-01T11:03:12"')


    def test_encode_time(self):
        # with microseconds
        encoded = json.dumps(datetime.strptime('11:03:12.5583', TIME_FORMAT).time(), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"T11:03:12.558300"')

        # with milliseconds
        encoded = json.dumps(datetime.strptime('11:03:12.55', TIME_FORMAT).time(), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"T11:03:12.550"')

        # without microseconds
        encoded = json.dumps(datetime.strptime('11:03:12.0', TIME_FORMAT).time(), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"T11:03:12"')


    def test_encode_date(self):
        encoded = json.dumps(datetime.strptime('2022-03-01', DATE_FORMAT).date(), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"2022-03-01"')


    def test_encode_timedelta(self):
        # microseconds
        encoded = json.dumps(timedelta(days=123, hours=1, minutes=2, seconds=3, microseconds=4), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"P123DT01H02M03.000004S"')

        # milliseconds
        encoded = json.dumps(timedelta(days=123, hours=1, minutes=2, seconds=3, milliseconds=4), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"P123DT01H02M03.004000S"')

        # no microseconds
        encoded = json.dumps(timedelta(days=123, hours=1, minutes=2, seconds=3), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"P123DT01H02M03S"')

        # negative
        encoded = json.dumps(timedelta(hours=-1, minutes=-2, seconds=-3), cls=ExtendedJSONEncoder)
        self.assertEqual(encoded, '"-P0DT01H02M03S"')
