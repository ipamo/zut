import os
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from unittest import TestCase
from zut import Header, dump_to_csv, list_dicts_from_csv, get_csv_headers, out_table, _is_semicolon_csv
from tests import SAMPLES_DIR, RESULTS_DIR


class Case(TestCase):
    def test_is_semicolon_csv(self):
        self.assertTrue(_is_semicolon_csv(StringIO('A;B\nE;F')))
        self.assertFalse(_is_semicolon_csv(StringIO('A,B\nE;E,F;F')))
        self.assertFalse(_is_semicolon_csv(StringIO('A\nE;E,F;F')))
        self.assertFalse(_is_semicolon_csv(StringIO('A\nE;E,F;F')))
        self.assertTrue(_is_semicolon_csv(MixedSample.path))


    def test_get_csv_headers_local(self):
        existing_headers = get_csv_headers(MixedSample.path)
        self.assertEqual([header.name for header in existing_headers], ['id', 'str0_col', 'str_col', 'bool_col', 'int_col', 'decimal_col'])


    def test_dump(self):
        target = RESULTS_DIR.joinpath("test_dump_LaRose.csv")
        dump_to_csv(target, LaRoseSample.data, headers=LaRoseSample.headers, csv_decimal_separator='.', csv_delimiter=';', csv_nullval='■')

        actual = target.read_text()
        expected = LaRoseSample.path.read_text()
        self.assertEqual(actual, expected)
    

    def test_load(self):
        actual = list_dicts_from_csv(LaRoseSample.path, csv_nullval='■')
        expected = LaRoseSample.as_loaded_dicts()
        self.assertEqual(actual, expected)


    def test_comma(self):
        target = RESULTS_DIR.joinpath("test_load_LaRose.csv")
        dump_to_csv(target, LaRoseSample.data, headers=LaRoseSample.headers, csv_delimiter=';', csv_nullval='■', csv_decimal_separator=',')

        actual = list_dicts_from_csv(target, csv_nullval='■')
        expected = LaRoseSample.as_loaded_dicts(decimal_separator=',')
        self.assertEqual(actual, expected)
    

    def test_string_io(self):
        target = StringIO(newline=None)
        dump_to_csv(target, LaRoseSample.data, headers=LaRoseSample.headers, csv_decimal_separator='.', csv_delimiter=';', csv_nullval='■')

        actual = target.getvalue()
        expected = LaRoseSample.path.read_text(encoding='utf-8-sig')     
        self.assertEqual(actual, expected)

        target.seek(0)
        actual = list_dicts_from_csv(target, csv_nullval='■')
        expected = LaRoseSample.as_loaded_dicts(linesep='\n')
        self.assertEqual(actual, expected)


    def test_dump_dicts(self):
        target = StringIO(newline=None)
        with out_table(target, tablefmt='csv', csv_decimal_separator='.', csv_delimiter=';', csv_nullval='■') as o:
            o.append({0: 1, f"Détails{os.linesep}Plus": f"La Rose, 13013;{os.linesep}Marseille: \"BDR\"", "Date": date(2024, 1, 10)})
            o.append({0: 3.14, "~Ôç~": datetime.strptime('1998-07-12T23:46:00', "%Y-%m-%dT%H:%M:%S"), "Date": date(2024, 1, 10)})
            o.append({"~Ôç~": datetime.strptime('1998-07-12T00:46:00.123+02:00', "%Y-%m-%dT%H:%M:%S.%f%z"), 0: 6.55957, "Date": date(2024, 1, 10), f"Détails{os.linesep}Plus": "<a href=\"http://www.marseille.fr\">Marseille</a>"})

        actual = target.getvalue()
        expected = LaRoseSample.path.read_text(encoding='utf-8-sig')
        self.assertEqual(actual, expected)


    def test_load_mixed(self):
        actual = list_dicts_from_csv(MixedSample.path, headers=['*', Header('id', fmt=int), Header('bool_col', fmt=bool), Header('int_col', fmt=int), Header('decimal_col', fmt=Decimal)], csv_nullval='■')
        self.assertEqual(actual, MixedSample.data)


class LaRoseSample:
    name = "la-rose.csv"
    path = SAMPLES_DIR.joinpath(name)

    headers = [0, f"Détails{os.linesep}Plus", "Date", "~Ôç~"]
    data = [
        [1, f"La Rose, 13013;{os.linesep}Marseille: \"BDR\"", date(2024, 1, 10), None],
        [3.14, None, date(2024, 1, 10), datetime.strptime('1998-07-12T23:46:00', "%Y-%m-%dT%H:%M:%S")],
        [6.55957, "<a href=\"http://www.marseille.fr\">Marseille</a>", date(2024, 1, 10), datetime.strptime('1998-07-12T00:46:00.123+02:00', "%Y-%m-%dT%H:%M:%S.%f%z")],
    ]

    @classmethod
    def as_loaded_dicts(cls, decimal_separator='.', linesep=os.linesep):
        dict_rows = []

        def format_value(value):
            if value is None:
                return None
            elif isinstance(value, (float,Decimal)) and decimal_separator != '.':
                return str(value).replace('.', decimal_separator)
            elif isinstance(value, str) and linesep != os.linesep:
                return value.replace(os.linesep, linesep)
            else:
                return str(value)
            
        headers = [format_value(header) for header in cls.headers]

        for list_row in cls.data:
            dict_rows.append({headers[i]: format_value(value) for i, value in enumerate(list_row)})

        return dict_rows


class MixedSample:
    name = "mixed-nullval.csv"
    path = SAMPLES_DIR.joinpath(name)

    data = [
        {'id': 1, 'str0_col': 'X', 'str_col': 'a',  'bool_col': True,  'int_col': 1, 'decimal_col': Decimal('1')},
        {'id': 2, 'str0_col': 'X', 'str_col': 'b',  'bool_col': False, 'int_col': 2, 'decimal_col': Decimal('2.2')},
        {'id': 3, 'str0_col': 'X', 'str_col': 'c',  'bool_col': True,  'int_col': 3, 'decimal_col': Decimal('3.33')},
        {'id': 4, 'str0_col': 'X', 'str_col': 'd',  'bool_col': False, 'int_col': 4, 'decimal_col': Decimal('4.444')},
        {'id': 5, 'str0_col': 'X', 'str_col': '',   'bool_col': None,  'int_col': None, 'decimal_col': None},
        {'id': 6, 'str0_col': 'X', 'str_col': None, 'bool_col': None,  'int_col': None, 'decimal_col': None},
    ]
