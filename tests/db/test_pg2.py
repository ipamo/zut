from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from unittest import TestCase, skipIf

from zut.db.pg2 import Pg2Adapter

from .base import DbBase


@skipIf(not Pg2Adapter.is_available(), "Pg2Adapter not available")
class Case(DbBase, TestCase):
    adapter = Pg2Adapter
    config_key_prefix = 'pg'

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
