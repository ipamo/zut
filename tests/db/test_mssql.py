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
