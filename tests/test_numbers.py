from __future__ import annotations
import re
from unittest import TestCase
from zut import human_number, human_bytes

class Case(TestCase):
    def test_human_numeric(self):
        value = 8*1024*1024

        human = human_number(value)
        self.assertEqual(human, '8,4 M')
        
        human = human_bytes(value)
        self.assertEqual(human, '8,0 MiB')
        
        human = human_bytes(value, max_multiple='K', decimals=2)
        human = re.sub(r'\s', ' ', human)
        self.assertEqual(human, '8 192,00 KiB')
