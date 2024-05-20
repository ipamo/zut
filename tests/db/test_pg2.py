from __future__ import annotations

from unittest import TestCase, skipIf

from zut.db.pg2 import Pg2Adapter

from .test_pg import PgBase


@skipIf(not Pg2Adapter.is_available(), "Pg2Adapter not available")
class Case(PgBase, TestCase):
    adapter = Pg2Adapter
