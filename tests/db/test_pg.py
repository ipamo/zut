from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
import logging
from unittest import TestCase, skipIf

from tests.test_text import SLUGIFY_DJANGO_SAMPLES, SLUGIFY_SAMPLES, SAMPLES_DIR
from zut import out_table
from zut.db.pg import PgAdapter

from .base import DbBase

logger = logging.getLogger(__name__)


@skipIf(not PgAdapter.is_available(), "PgAdapter not available")
class Case(DbBase, TestCase):
    adapter = PgAdapter
    config_key_prefix = 'pg'

    def test_slugify_pg(self):        
        for text, expected in SLUGIFY_SAMPLES.items():
            actual = self.db.get_scalar("SELECT slugify(%s)", [text])
            self.assertEqual(actual, expected, "pg slugify(%s)" % text)


    def test_slugify_django_pg(self):        
        for text, expected in SLUGIFY_DJANGO_SAMPLES.items():
            actual = self.db.get_scalar("SELECT slugify_django(%s)", [text])
            self.assertEqual(actual, expected, "pg slugify_django(%s)" % text)


    def test_load_csv_ordered(self):
        self.db.execute_query(
            """
            DROP TABLE IF EXISTS load_csv_ordered;

            CREATE TABLE load_csv_ordered (
                id int NOT NULL PRIMARY KEY
                ,str0_col text NULL
                ,str_col text NULL
                ,bool_col bool NULL
                ,int_col int NULL
                ,decimal_col decimal NULL
            )
            """)

        self.db.load_from_csv(SAMPLES_DIR.joinpath('mixed.csv'), 'load_csv_ordered', merge='truncate')

        actual = self.db.list_dicts("SELECT * FROM load_csv_ordered")
        self.assertEqual(actual, MIXED_DATA)
    

    def test_load_csv_nonordered(self):
        self.db.execute_query(
            """
            DROP TABLE IF EXISTS load_csv_nonordered;

            CREATE TABLE load_csv_nonordered (
                id int NOT NULL PRIMARY KEY
                ,str_col text NULL
                ,str0_col text NULL
                ,bool_col bool NULL
                ,int_col int NULL
                ,decimal_col decimal NULL
            )
            """)

        self.db.load_from_csv(SAMPLES_DIR.joinpath('mixed.csv'), 'load_csv_nonordered', columns=['id', 'str0_col', 'str_col', 'bool_col', 'int_col', 'decimal_col'], merge='truncate')
        
        actual = self.db.list_dicts("SELECT * FROM load_csv_nonordered")
        self.assertEqual(actual, MIXED_DATA)


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

        actual = self.db.list_dicts(f"SELECT col_notnull, col_nullable, col_decimal, col_timestamp FROM {self.mark}_out_table1")
        self.assertEqual(actual, [
            {'col_notnull': 'A', 'col_nullable': '', 'col_decimal': Decimal('1.23456789'), 'col_timestamp': dt},
            {'col_notnull': 'B', 'col_nullable': None, 'col_decimal': None, 'col_timestamp': None},
        ])


    def test_out_table_with_calculated_headers(self):
        self.db.execute_query(f'DROP TABLE IF EXISTS {self.mark}_out_table2')
        self.db.execute_query(f'CREATE TABLE {self.mark}_out_table2 (id BIGINT NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY, col_notnull TEXT NOT NULL, col_nullable TEXT NULL, col_decimal DECIMAL NULL, col_float FLOAT NULL, col_date DATE, col_time TIME, col_timestamp TIMESTAMPTZ)')

        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(f'{self.url}/{self.mark}_out_table2', headers=['col_notnull', 'col_nullable', 'col_decimal']) as t:
                t.append({'col_notnull': 'A', 'col_nullable': '', 'col_decimal': Decimal('1.23456789')})
                t.append({'col_notnull': 'B'})

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))


        actual = self.db.list_dicts(f"SELECT col_notnull, col_nullable, col_decimal FROM {self.mark}_out_table2")
        self.assertEqual(actual, [
            {'col_notnull': 'A', 'col_nullable': '', 'col_decimal': Decimal('1.23456789')},
            {'col_notnull': 'B', 'col_nullable': None, 'col_decimal': None},
        ])


    def test_get_table_columns(self):
        expected = [
            {'name': 'id', 'python_type': int, 'sql_type': 'int8', 'nullable': None},
            {'name': 'name', 'python_type': str, 'sql_type': 'text', 'nullable': None},
            {'name': 'price', 'python_type': Decimal, 'sql_type': 'numeric', 'nullable': None},
            {'name': 'col_float', 'python_type': float, 'sql_type': 'float8', 'nullable': None},
            {'name': 'col_date', 'python_type': date, 'sql_type': 'date', 'nullable': None},
            {'name': 'col_time', 'python_type': time, 'sql_type': 'time', 'nullable': None},
            {'name': 'col_timestamp', 'python_type': datetime, 'sql_type': 'timestamp', 'nullable': None},
        ]

        def keep_keys(data):
            new_data = {}
            for key, value in data.items():
                if key in ['name', 'python_type', 'sql_type', 'nullable']:
                    new_data[key] = value
            return new_data

        self.assertEqual(expected, [keep_keys(info.__dict__) for info in self.db.get_table_columns(f'{self.mark}_tryout')])


MIXED_DATA = [
    {'id': 1, 'str0_col': 'X', 'str_col': 'a',  'bool_col': True,  'int_col': 1, 'decimal_col': Decimal('1')},
    {'id': 2, 'str0_col': 'X', 'str_col': 'b',  'bool_col': False, 'int_col': 2, 'decimal_col': Decimal('2.2')},
    {'id': 3, 'str0_col': 'X', 'str_col': 'c',  'bool_col': True,  'int_col': 3, 'decimal_col': Decimal('3.33')},
    {'id': 4, 'str0_col': 'X', 'str_col': 'd',  'bool_col': False, 'int_col': 4, 'decimal_col': Decimal('4.444')},
    {'id': 5, 'str0_col': 'X', 'str_col': '',   'bool_col': None,  'int_col': None, 'decimal_col': None},
    {'id': 6, 'str0_col': 'X', 'str_col': None, 'bool_col': None,  'int_col': None, 'decimal_col': None},
]
