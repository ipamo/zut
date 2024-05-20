from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest import TestCase, skipIf

from zut.db.mysql import MysqlAdapter

from .base import DbBase


@skipIf(not MysqlAdapter.is_available(), "MysqlAdapter not available")
class Case(DbBase, TestCase):
    adapter = MysqlAdapter
    config_key_prefix = 'mysql'
    sql_types = {
        'id': 'LONGLONG',
        'name': 'VAR_STRING',
        'price': 'NEWDECIMAL',
        'col_text': 'BLOB',
        'col_float': 'FLOAT',
        'col_date': 'DATE',
        'col_time': 'TIME',
        'col_timestamp': 'TIMESTAMP',
    }

    def test_specific_types(self):
        self.db.execute_query(
            f"""
            DROP TABLE IF EXISTS {self.mark}_specific_types;

            CREATE TABLE {self.mark}_specific_types (
                /* Numeric */
                spec_tinyint TINYINT
                ,spec_smallint SMALLINT
                ,spec_mediumint MEDIUMINT
                ,spec_int INT
                ,spec_bigint BIGINT
                ,spec_float FLOAT
                ,spec_double DOUBLE
                ,spec_decimal DECIMAL(5,2)
                ,spec_bit BIT(8)
                /* Dates */
                ,spec_timestamp TIMESTAMP
                ,spec_datetime DATETIME
                ,spec_date DATE
                ,spec_time TIME
                ,spec_year YEAR
                /* Divers */
                ,spec_json JSON
            );

            INSERT INTO {self.mark}_specific_types
            VALUES (
                /* Numeric */
                0, 0, 0, 0, 0, 0.1, 0.1, 0.1, b'1000001'
                /* Dates */
                ,'1998-07-12 21:14:00', '1998-07-12 21:14:00', '1998-07-12', '21:14:00', 1998
                /* Divers */
                ,1
            );
            """)

        with self.db.cursor() as cursor:
            self.db.execute_query(f"SELECT * FROM {self.mark}_specific_types", cursor=cursor)
            columns = self.db.get_cursor_columns(cursor)
            actual = {}
            for row in cursor:
                for i, value in enumerate(row):
                    column = columns[i]
                    actual[column.name] = (value, type(value), column.sql_type)

        expected = {
            'spec_tinyint': (0, int, 'TINY'),
            'spec_smallint': (0, int, 'SHORT'),
            'spec_mediumint': (0, int, 'INT24'),
            'spec_int': (0, int, 'LONG'),
            'spec_bigint': (0, int, 'LONGLONG'),
            'spec_float': (0.1, float, 'FLOAT'),
            'spec_double': (0.1, float, 'DOUBLE'),
            'spec_decimal': (Decimal('0.1'), Decimal, 'NEWDECIMAL'),
            'spec_bit': (b'A', bytes, 'BIT'),
            'spec_timestamp': (datetime.fromisoformat('1998-07-12 21:14:00'), datetime, 'TIMESTAMP'),
            'spec_datetime': (datetime.fromisoformat('1998-07-12 21:14:00'), datetime, 'DATETIME'),
            'spec_date': (date.fromisoformat('1998-07-12'), date, 'DATE'),
            'spec_time': (timedelta(hours=21, minutes=14), timedelta, 'TIME'),
            'spec_year': (1998, int, 'YEAR'),
            'spec_json': ('1', str, 'BLOB'),
        }

        for column_name, column_actual in actual.items():
            self.assertEqual(expected[column_name], column_actual, f"Column: {column_name}")
