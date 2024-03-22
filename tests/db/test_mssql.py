from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from unittest import TestCase, skipIf

from zut.db.mssql import MssqlAdapter

from .base import DbBase


@skipIf(not MssqlAdapter.is_available(), "MssqlAdapter not available")
class Case(DbBase, TestCase):
    adapter = MssqlAdapter
    config_key_prefix = 'mssql'

    def test_get_table_columns(self):
        expected = [
            {'name': 'id', 'python_type': int, 'nullable': False},
            {'name': 'name', 'python_type': str, 'nullable': False},
            {'name': 'price', 'python_type': Decimal, 'nullable': True},
            {'name': 'col_float', 'python_type': float, 'nullable': True},
            {'name': 'col_date', 'python_type': date, 'nullable': True},
            {'name': 'col_time', 'python_type': time, 'nullable': True},
            {'name': 'col_timestamp', 'python_type': bytearray, 'nullable': False},
        ]

        def keep_keys(data):
            new_data = {}
            for key, value in data.items():
                if key in ['name', 'python_type', 'nullable']:
                    new_data[key] = value
            return new_data

        self.assertEqual(expected, [keep_keys(info.__dict__) for info in self.db.get_table_columns(f'{self.mark}_tryout')])
