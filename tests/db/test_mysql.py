from __future__ import annotations

from unittest import TestCase, skipIf

from zut.db.mysql import MysqlAdapter

from .base import DbBase


@skipIf(not MysqlAdapter.is_available(), "MysqlAdapter not available")
class Case(DbBase, TestCase):
    adapter = MysqlAdapter
    config_key_prefix = 'mysql'
