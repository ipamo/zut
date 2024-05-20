from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from unittest import TestCase, skipIf

from tests.test_text import SLUGIFY_DJANGO_SAMPLES, SLUGIFY_SAMPLES
from zut import out_table
from zut.db.pg import PgAdapter

from .base import DbBase

logger = logging.getLogger(__name__)

class PgBase(DbBase):
    adapter = PgAdapter
    config_key_prefix = 'pg'
    sql_types = {
        'id': 'int8',
        'name': 'varchar',
        'price': 'numeric',
        'col_text': 'text',
        'col_float': 'float8',
        'col_date': 'date',
        'col_time': 'time',
        'col_timestamp': 'timestamp',
    }

    def test_slugify_pg(self):        
        for text, expected in SLUGIFY_SAMPLES.items():
            actual = self.db.get_scalar("SELECT slugify(%s)", [text])
            self.assertEqual(actual, expected, "pg slugify(%s)" % text)


    def test_slugify_django_pg(self):        
        for text, expected in SLUGIFY_DJANGO_SAMPLES.items():
            actual = self.db.get_scalar("SELECT slugify_django(%s)", [text])
            self.assertEqual(actual, expected, "pg slugify_django(%s)" % text)


    # TODO: move to base
    def test_out_table_with_explicit_headers(self):
        self.db.execute_query(f'DROP TABLE IF EXISTS {self.mark}_out_table1')
        self.db.execute_query(f'CREATE TABLE {self.mark}_out_table1 (id BIGINT NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY, col_notnull TEXT NOT NULL, col_nullable TEXT NULL, col_decimal DECIMAL NULL, col_float FLOAT NULL, col_date DATE, col_time TIME, col_timestamp TIMESTAMPTZ)')
        dt = datetime.fromisoformat('1998-07-12T21:46:00.123+02:00')

        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(f'{self.url}/{self.mark}_out_table1', headers=['col_notnull', 'col_nullable', 'col_decimal', 'col_timestamp']) as t:
                t.append(['A', '', Decimal('1.23456789'), dt])
                t.append(['B', None, None, None])

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))

        actual = self.db.get_dicts(f"SELECT col_notnull, col_nullable, col_decimal, col_timestamp FROM {self.mark}_out_table1")
        self.assertEqual(actual, [
            {'col_notnull': 'A', 'col_nullable': '', 'col_decimal': Decimal('1.23456789'), 'col_timestamp': dt},
            {'col_notnull': 'B', 'col_nullable': None, 'col_decimal': None, 'col_timestamp': None},
        ])


    # TODO: move to base
    def test_out_table_with_calculated_headers(self):
        self.db.execute_query(f'DROP TABLE IF EXISTS {self.mark}_out_table2')
        self.db.execute_query(f'CREATE TABLE {self.mark}_out_table2 (id BIGINT NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY, col_notnull TEXT NOT NULL, col_nullable TEXT NULL, col_decimal DECIMAL NULL, col_float FLOAT NULL, col_date DATE, col_time TIME, col_timestamp TIMESTAMPTZ)')

        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(f'{self.url}/{self.mark}_out_table2', headers=['col_notnull', 'col_nullable', 'col_decimal']) as t:
                t.append({'col_notnull': 'A', 'col_nullable': '', 'col_decimal': Decimal('1.23456789')})
                t.append({'col_notnull': 'B'})

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))


        actual = self.db.get_dicts(f"SELECT col_notnull, col_nullable, col_decimal FROM {self.mark}_out_table2")
        self.assertEqual(actual, [
            {'col_notnull': 'A', 'col_nullable': '', 'col_decimal': Decimal('1.23456789')},
            {'col_notnull': 'B', 'col_nullable': None, 'col_decimal': None},
        ])


@skipIf(not PgAdapter.is_available(), "PgAdapter not available")
class Case(PgBase, TestCase):
    adapter = PgAdapter
