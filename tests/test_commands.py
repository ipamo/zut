from __future__ import annotations
from unittest import TestCase
from argparse import ArgumentParser
from zut import add_func_command, add_module_command, ArgumentParser

class Case(TestCase):
    def test_add_module_commands(self):
        parser = ArgumentParser()
        subparsers = parser.add_subparsers()
        add_module_command(subparsers, "tests.samples.myfeaturecmd")

        self.assertEqual(list(subparsers._name_parser_map.keys()), ["myfeature"])


    def test_add_func_commands(self):
        def clean():
            pass

        def lso():
            pass
            
        parser = ArgumentParser()
        subparsers = parser.add_subparsers()
        add_func_command(subparsers, clean)
        add_func_command(subparsers, lso)

        self.assertEqual(list(subparsers._name_parser_map.keys()), ['clean', 'lso'])
