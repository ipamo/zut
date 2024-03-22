from __future__ import annotations

from datetime import date, datetime
from unittest import TestCase

from zut import convert


class Case(TestCase):
    def test_convert(self):
        self.assertEqual(False, convert("0", bool))
        self.assertEqual(True, convert("1", bool))

        self.assertEqual([], convert("", list))
        self.assertEqual(["A", "B", "C", "D", "E", "F", "G"], convert("A,B;C|D E  F   G", list))

        self.assertEqual(date(1998,7,12), convert('1998-07-12', date))
        self.assertEqual(datetime.fromisoformat('1998-07-12T00:00:00'), convert(date(1998,7,12), datetime))
