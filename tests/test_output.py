from __future__ import annotations

import logging
import sys
from contextlib import redirect_stdout
from datetime import date, datetime, time, timezone
from enum import Enum
from io import StringIO
from pathlib import Path
from unittest import TestCase, skipIf

from tests import RESULTS_DIR, SAMPLES_DIR, SMB_RESULTS_DIR
from zut import Header, files, out_table, pytz, tabulate, tzdata
from zut.excel import ExcelWorkbook, openpyxl, split_excel_path


logger = logging.getLogger(__name__)

class Case(TestCase):
    def test_noop(self):
        capture = StringIO()
        with redirect_stdout(capture):            
            with self.assertLogs(level=logging.WARNING) as cm:
                with out_table(False, headers=['col1', 'col2']) as t:
                    t.append([1, 2])

                logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
                self.assertEqual(1, len(cm.records))

        
        self.assertEqual("", capture.getvalue())


    @skipIf(tabulate is None, "tabulate not available")
    def test_tabulate(self):
        outfile = StringIO()        
        with self.assertLogs(level=logging.WARNING) as cm:
            _export(outfile, tablefmt='tabulate')

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))
        
        outfile.seek(0)
        content = outfile.read()
        self.assertEqual(content, _EXPECTED_TABULATE)


    @skipIf(tabulate is None, "tabulate not available")
    def test_tabulate_using_dict(self):
        outfile = StringIO()        
        with self.assertLogs(level=logging.WARNING) as cm:
            _export_using_dict(outfile, tablefmt='tabulate')

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))
        
        outfile.seek(0)
        content = outfile.read()
        self.assertEqual(content, _EXPECTED_TABULATE)

    
    @skipIf(tabulate is None, "tabulate not available")
    def test_tabulate_noheaders(self):
        out = StringIO()

        class AnEnum(Enum):
            VAL = 1

        with redirect_stdout(out):            
            with self.assertLogs(level=logging.WARNING) as cm:
                with out_table(title='Test', headers=['col1', 'col2', 'col3'], tablefmt='tabulate') as t:
                    t.append(['Text', 3.14, None])
                    t.append(['', 20, AnEnum.VAL])

                logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
                self.assertEqual(1, len(cm.records))

        self.assertEqual(out.getvalue(), """col1      col2  col3
------  ------  ------
Text      3.14
         20     VAL
""")
                         

    def test_csv(self):
        target = RESULTS_DIR.joinpath("output.csv")        
        with self.assertLogs(level=logging.WARNING) as cm:
            _export(target, tablefmt='csv-excel')

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))

        with open(target, 'r', encoding='utf-8-sig', newline='') as fp:
            actual = fp.read()

        self.assertEqual(actual, _EXPECTED_CSV)


    def test_csv_using_dict(self):
        target = RESULTS_DIR.joinpath("output-with-dict.csv")        
        with self.assertLogs(level=logging.WARNING) as cm:
            _export_using_dict(target, tablefmt='csv-excel')

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))

        with open(target, 'r', encoding='utf-8-sig', newline='') as fp:
            actual = fp.read()

        self.assertEqual(actual, _EXPECTED_CSV)


    def test_csv_noheaders(self):
        out = StringIO(newline='')

        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(out, tablefmt='csv') as o:
                o.append(['Text', '"Quote"', 'New\r\nLine', 1, 3.14, '', None])

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))
        
        self.assertEqual(out.getvalue(), 'Text,"""Quote""","New\r\nLine",1,3.14,\"\",')


    def test_csv_headers(self):
        out = StringIO()

        with self.assertLogs(level=logging.WARNING) as cm:
            expected = 'col1;col2;missing'
            with out_table(out, headers = ['col1', 'col2', 'missing'], tablefmt='csv-excel') as o:
                o.append(['val1', 'val2'])
                expected += '\r\nval1;val2'

                o.append(['val1', 'val2', 'missing', 'extra'])  # Extra will be added anyway
                expected += '\r\nval1;val2;missing;extra'

                o.append(['val1', 'val2'])
                expected += '\r\nval1;val2'
        
            self.assertEqual(out.getvalue(), expected)

            self.assertEqual(len(cm.records), 3)
            self.assertEqual(cm.records[0].message, "Row 1 length: 2 (expected headers length: 3)")
            self.assertEqual(cm.records[1].message, "Row 2 length: 4 (expected headers length: 3)")
            self.assertEqual(cm.records[2].message, "Row 3 length: 2 (expected headers length: 3)")


    def test_csv_mix_delay(self):
        out = StringIO()
        expected = 'col1,col2,col3,col4\r\n'

        with self.assertLogs(level=logging.WARNING) as cm: # headers not given, so rows will be delayed
            with out_table(out, csv_delimiter=',') as o:
                o.append({'col1': 11, 'col2': 12})
                expected += '11,12,,\r\n'

                o.append({'col3': 23, 'col2': 22})
                expected += ',22,23,\r\n'

                o.append({'col1': 31, 'col3': 33})
                expected += '31,,33,\r\n'

                o.append([41, 42])
                expected += '41,42\r\n'

                o.append({'col1': 51, 'col4': 54})
                expected += '51,,,54'

            self.assertEqual(out.getvalue(), expected)

            self.assertEqual(len(cm.records), 1)
            self.assertEqual(cm.records[0].message, "Row 4 length: 2 (expected headers length: 4)")


    def test_csv_mix_nodelay(self):
        out = StringIO()
        expected = 'col1,col2,col3\r\n'

        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(out, csv_delimiter=',', headers=['col1', 'col2', 'col3']) as o: # headers are given, so rows will not be delayed
                o.append({'col1': 11, 'col2': 12})
                expected += '11,12,\r\n'

                o.append({'col3': 23, 'col2': 22})
                expected += ',22,23\r\n'

                o.append({'col1': 31, 'col3': 33})
                expected += '31,,33\r\n'

                o.append([41, 42])
                expected += '41,42\r\n'

                o.append({'col1': 51, 'col4': 54})
                expected += '51,,,54'

            self.assertEqual(out.getvalue(), expected)

            self.assertEqual(len(cm.records), 2)
            self.assertEqual(cm.records[0].message, "Row 4 length: 2 (expected headers length: 3)")
            self.assertEqual(cm.records[1].message, "Row 5 key \"col4\" not found in headers: value will be appended at column 4 with an empty header")


    @skipIf(sys.version_info < (3, 9) and not pytz, "pytz not available")
    @skipIf(sys.version_info >= (3, 9) and sys.platform == 'win32' and not tzdata, "tzdata not available")
    def test_csv_timezone(self):
        out = StringIO()
        with out_table(out, csv_delimiter=';', headers=['Col'], tablefmt='csv-excel') as o:
            o.append([datetime.fromisoformat('1998-07-12T21:46:00.000+02:00')])

        self.assertEqual(out.getvalue(), "Col\r\n1998-07-12 21:46:00")


        out = StringIO()
        with out_table(out, csv_delimiter=';', tz='Europe/Paris', headers = ['Col'], tablefmt='csv-excel') as o:
            o.append([datetime.fromisoformat('1998-07-12T21:46:00.123+02:00')])

        self.assertEqual(out.getvalue(), "Col\r\n1998-07-12 21:46:00")


        out = StringIO()
        with out_table(out, csv_delimiter=';', tz='UTC', headers = ['Col'], tablefmt='csv-excel') as o:
            o.append([datetime.fromisoformat('1998-07-12T21:46:00.123+02:00')])

        self.assertEqual(out.getvalue(), "Col\r\n1998-07-12 19:46:00")


    def test_csv_append(self):
        expected = 'previous;col2;col1\r\n;02;01'       
        out = RESULTS_DIR.joinpath('append.csv')        
        with files.open(out, 'w', newline='', encoding='utf-8-sig', mkdir=True) as f:
            f.write(expected)
        
        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(out, append=True, csv_delimiter=';', headers = ['col1', 'col2', 'col3', 'col4']) as o:
                o.append([11, 12, 13, 14])
                expected += '\r\n;12;11;13;14'

            with files.open(out, 'r', newline='', encoding='utf-8-sig') as f:
                actual = f.read()
            self.assertEqual(actual, expected)

            self.assertEqual(len(cm.records), 1)
            self.assertEqual(cm.records[0].message, "Header \"col3\", \"col4\" not found in existing headers: values will be appended without a column header")


    def test_csv_append_to_empty(self):
        out = RESULTS_DIR.joinpath('append_to_empty.csv')
        with files.open(out, 'w', newline='', encoding='utf-8-sig', mkdir=True) as f:
            pass
        
        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(out, append=True, csv_delimiter=';', headers = ['col1', 'col2', 'col3', 'col4']) as o:
                o.append([11, 12, 13, 14])
                expected = 'col1;col2;col3;col4\r\n11;12;13;14'

            with files.open(out, 'r', newline='', encoding='utf-8-sig') as f:
                actual = f.read()
            self.assertEqual(actual, expected)

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))


    def test_csv_append_delay(self):
        expected = 'previous;col2;col1\r\n;02;01'       
        out = RESULTS_DIR.joinpath('append_delay.csv')        
        with files.open(out, 'w', newline='', encoding='utf-8-sig', mkdir=True) as f:
            f.write(expected)
        
        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(out, append=True, csv_delimiter=';') as o:
                o.append({'col1': 11, 'col3': 13})
                expected += '\r\n;;11;13;'

                o.append({'col2': 12, 'col4': 14})
                expected += '\r\n;12;;;14'

            with files.open(out, 'r', newline='', encoding='utf-8-sig') as f:
                actual = f.read()
            self.assertEqual(actual, expected)

            self.assertEqual(len(cm.records), 1)
            self.assertEqual(cm.records[0].message, "Header \"col3\", \"col4\" not found in existing headers: values will be appended without a column header")


    def test_format_out(self):
        out = RESULTS_DIR.joinpath('{prefix}_{title}.csv')

        prefix = 'out'
        title = 'table_list'
        actual_out = Path(str(out).format(prefix=prefix, title=title))

        with self.assertLogs(level=logging.INFO) as logs:
            with out_table(out, headers=['X', 'Y'], title=title, prefix=prefix, csv_delimiter=';') as table:
                table.append(['1', '2'])
                table.append(['a', 'b'])
   
            self.assertEqual(2, len(logs.records))    
            self.assertEqual((logging.INFO, f"Export {title} to {actual_out}"), (logs.records[0].levelno, logs.records[0].message))
            self.assertEqual((logging.INFO, f"2 rows exported to {actual_out}"), (logs.records[1].levelno, logs.records[1].message))

        with self.assertLogs(level=logging.INFO) as logs:
            with out_table(out, headers=['Y', 'X', 'Z'], append=True, title=title, prefix=prefix, csv_delimiter=';') as table:
                table.append(['3', '4', '0'])
                table.append(['a', 'b', 'Z'])

            self.assertEqual(3, len(logs.records))            
            self.assertEqual((logging.INFO, f"Append {title} to {actual_out}"), (logs.records[0].levelno, logs.records[0].message))
            self.assertEqual((logging.WARNING, f"Header \"Z\" not found in existing headers: values will be appended without a column header"), (logs.records[1].levelno, logs.records[1].message))
            self.assertEqual((logging.INFO, f"2 rows appended to {actual_out}"), (logs.records[2].levelno, logs.records[2].message))


        # Check final file content
        expected = """X;Y
1;2
a;b
4;3;0
b;a;Z"""
        self.assertEqual(expected, actual_out.read_text(encoding='utf-8-sig'))


    def test_default_fmt(self):
        out = StringIO()
        expected = 'what;value'        
        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(out, headers=['what', 'value'], csv_delimiter=';') as table:
                table.append(['bool', True])
                expected += '\r\nbool;true'

                table.append(['list1', [1, 2]])
                expected += '\r\nlist1;1|2'

                table.append(['list2', ["A"]])
                expected += '\r\nlist2;A'

                table.append(['list3', [1, "A \"B\" C", None]])
                expected += '\r\nlist3;"1|A ""B"" C|"'

                table.append(['dict', {'int': 1, 'float': 3.14, 'list': [1, 2], 'null': None}])
                expected += "\r\ndict;{'int': 1, 'float': 3.14, 'list': [1, 2], 'null': None}"

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))

        self.assertEqual(out.getvalue(), expected)


    def test_csv_specific_fmt(self):
        out = StringIO()
        expected = 'size_gib;size_human_bytes'        
        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(out, headers=[Header('size_gib', fmt='gib'), Header('size_human_bytes', fmt='human_bytes')], tablefmt='csv-excel') as table:
                table.append([20971520, 20971520])
                expected += '\r\n0,019531250;20,0 MiB'
                
                table.append([21474836480, 21474836480])
                expected += '\r\n20,000000000;20,0 GiB'

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))

        self.assertEqual(out.getvalue(), expected)


    @skipIf(not tabulate, 'tabulate not available')
    def test_tabulate_specific_fmt(self):
        out = StringIO()   
        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(out, headers=[Header('size_gib', fmt='gib'), Header('size_human_bytes', fmt='human_bytes')], csv_delimiter=';', tablefmt='tabulate') as table:
                table.append([20971520, 20971520])
                table.append([21474836480, 21474836480])

            logger.warning("Dummy warning") # Cannot use assertNoLogs for Python < 3.10
            self.assertEqual(1, len(cm.records))

        expected = """  size_gib  size_human_bytes
----------  ------------------
      0.02  20,0 MiB
     20.00  20,0 GiB
"""

        self.assertEqual(out.getvalue(), expected)


    @skipIf(not openpyxl, 'openpyxl not available')
    def test_excel_successive(self):
        path = RESULTS_DIR.joinpath('successive.xlsx')
        self._excel_successive(path)


    @skipIf(not openpyxl, 'openpyxl not available')
    @skipIf(not SMB_RESULTS_DIR, 'smb not configured')
    def test_excel_successive_smb(self):
        self._excel_successive(SMB_RESULTS_DIR + r'\successive.xlsx')


    @skipIf(not openpyxl, 'openpyxl not available')
    def test_excel_several(self):
        path = RESULTS_DIR.joinpath('several.xlsx')
        self._excel_several(path)


    @skipIf(not openpyxl, 'openpyxl not available')
    @skipIf(not SMB_RESULTS_DIR, 'smb not configured')
    def test_excel_several_smb(self):
        self._excel_several(SMB_RESULTS_DIR + r'\several.xlsx')


    @skipIf(not openpyxl, 'openpyxl not available')
    def test_excel_timezone(self):
        path = RESULTS_DIR.joinpath('timezone.xlsx')        
        if files.exists(path):
            files.remove(path)
                
        with out_table(f"{path}#Paris", headers=['Col'], tz='Europe/Paris') as o:
            o.append([datetime.fromisoformat('1998-07-12T21:46:00.123+02:00')])

        self._excel_verify(f"{path}#Paris", expected_headers=['Col'], expected_rows=[[datetime(1998, 7, 12, 21, 46, 0)]])
        
        with out_table(f"{path}#UTC", headers=['Col'], tz=timezone.utc) as o:
            o.append([datetime.fromisoformat('1998-07-12T21:46:00.123+02:00')])

        self._excel_verify(f"{path}#UTC", expected_headers=['Col'], expected_rows=[[datetime(1998, 7, 12, 19, 46, 0)]])


    @skipIf(not openpyxl, 'openpyxl not available')
    def test_excel_manual_lessrows(self):
        origin_path = SAMPLES_DIR.joinpath('manual-lessrows.xlsx')
        path = RESULTS_DIR.joinpath('manual-lessrows.xlsx')

        if files.exists(path):
            files.remove(path)

        files.copy2(origin_path, path)

        with out_table(f'{path}#Tableau1', headers=['Col1', 'Col2']) as o:
            o.append(['A', 1])
            o.append(['B', 2])

        #MANUAL: check that table as filtering buttons, and that styles and formulas are automatically added when a new row is created

    
    def _excel_several(self, workbook_path: str):
        if files.exists(workbook_path):
            files.remove(workbook_path)
        
        with out_table(workbook_path, headers=['Col1', 'Col2']) as o:
            o.append([1, 2])
            o.append([3, 4])
        
        with out_table(f"{workbook_path}#Table2", headers=['T2_Col1', 'T2_Col2']) as o:
            o.append([21, 22])
            o.append([23, 24])
        
        with out_table(f"{workbook_path}#Table3", headers=['T3_Col1', 'T3_Col2']) as o:
            o.append([21, 22])
            o.append([23, 24])

        self._excel_verify(workbook_path, expected_headers=['Col1', 'Col2'], expected_rows=[[1, 2], [3, 4]])
        self._excel_verify(f"{workbook_path}#Table2", expected_headers=['T2_Col1', 'T2_Col2'], expected_rows=[[21, 22], [23, 24]])
        self._excel_verify(f"{workbook_path}#Table3", expected_headers=['T3_Col1', 'T3_Col2'], expected_rows=[[21, 22], [23, 24]])


    def _excel_successive(self, workbook_path: str):
        # Write to new file    
        if files.exists(workbook_path):
            files.remove(workbook_path)

        with out_table(workbook_path, headers=FRUITS_HEADERS) as o:
            for row in FRUITS_ROWS:
                o.append(row)

        self._excel_verify(workbook_path, FRUITS_HEADERS, FRUITS_ROWS)


        # Append to file
        with out_table(workbook_path, headers=['2011', 'Fruit', 'New'], append=True) as o:
            o.append([1, 'More1', 'N1'])
            o.append([2, 'More2', 'N2'])
        
        expected_headers = [*FRUITS_HEADERS, 'New']
        expected_rows = []
        for row in FRUITS_ROWS:
            expected_rows.append([*row, None])
        expected_rows.append(['More1', None, None, None, 1, None, None, None, 'N1'])
        expected_rows.append(['More2', None, None, None, 2, None, None, None, 'N2'])

        self._excel_verify(workbook_path, expected_headers=expected_headers, expected_rows=expected_rows)

        # Write (NOT APPEND) to existing file with an additional column and row
        with self.assertLogs(level=logging.WARNING) as cm:
            with out_table(workbook_path, headers=[*FRUITS_HEADERS, "2015"]) as o:
                o.append(["NEW FRUIT", "Date", "Mix", "Decimal", "2011", "2012", "2013", "2014", "2015", 'MORE'])

            self.assertEqual(len(cm.records), 2)
            self.assertEqual(cm.records[0].message, "Row 1 length: 10 (expected headers length: 9)")
            self.assertEqual(cm.records[1].message, "Ignore values from index 10 (MORE)")


        expected_headers = [*FRUITS_HEADERS, 'New', '2015']
        expected_rows = [
            ["NEW FRUIT", "Date", "Mix", "Decimal", "2011", "2012", "2013", "2014", None, "2015"]
        ]
        
        self._excel_verify(workbook_path, expected_headers=expected_headers, expected_rows=expected_rows)
    

    def _excel_verify(self, path: str, expected_headers: list[str], expected_rows: list[list]):
        workbook_path, table_name = split_excel_path(path)
        if not table_name:
            table_name = 'Out'

        workbook = ExcelWorkbook.get_or_create_cached(workbook_path)
        table = workbook.get_table(table_name)

        actual_headers = table.column_names
        actual_rows = [row.values for row in table]

        self.assertEqual(actual_headers, expected_headers)
        self.assertEqual(len(actual_rows), len(expected_rows))
        
        for i in range(0, len(actual_rows)):
            self.assertEqual(actual_rows[i], expected_rows[i], msg=f"row {i+1}")
            #self.assertEqual(actual_rows[i], _convert_row_dates(expected_rows[i]), msg=f"row {i+1}")


_EXPECTED_TABULATE = """  Id  Name                                      Created on    Last at
----  ----------------------------------------  ------------  --------------------------------
   1  La Rose, au top; Marseille: "superbe"     2022-03-26
   2  Moi aussi                                 2022-03-26    1998-07-12 23:46:00+02:00
   3  <a href="http://www.supelec.fr">Lien</a>  2022-03-26    1998-07-12 00:46:00.123000+02:00
"""

_EXPECTED_CSV = f"""Id;Name;Created on;Last at
1;"La Rose, au top; Marseille: \"\"superbe\"\"";2022-03-26;
2;Moi aussi;2022-03-26;1998-07-12 23:46:00
3;"<a href=\"\"http://www.supelec.fr\"\">Lien</a>";2022-03-26;1998-07-12 00:46:00""".replace('\n', '\r\n')


FRUITS_HEADERS = ["Fruit", "Date", "Mix", "Decimal", "2011", "2012", "2013", "2014"]

FRUITS_ROWS = [
    ['Apples',  date(2000, 1, 1), datetime(2014, 10, 26, 10, 26, 59), 3.14,    10000, 5000, 8000, 6000],
    ['Pears',   date(2000, 1, 1), date(2014, 10, 26),                 6.55957, 2000, 3000, 4000, 5000],
    ['Bananas', date(2000, 1, 1), time(10, 26, 59),                   2.7182,  36000, 6000, 6500, 6000],
    ['Oranges', date(2000, 1, 1), None,                               123456789.1234567, 500,  300,  200,  700],
]

def _export(out, **options):
    with out_table(out, **options, headers=["Id", "Name", "Created on", "Last at"]) as t:
        t.append([1, "La Rose, au top; Marseille: \"superbe\"", date(2022, 3, 26), None])
        t.append([2, "Moi aussi", date(2022, 3, 26), datetime.strptime('1998-07-12T23:46:00.000+02:00', "%Y-%m-%dT%H:%M:%S.%f%z")])
        t.append([3, "<a href=\"http://www.supelec.fr\">Lien</a>", date(2022, 3, 26), datetime.strptime('1998-07-12T00:46:00.123+02:00', "%Y-%m-%dT%H:%M:%S.%f%z")])


def _export_using_dict(out, **options):
    with out_table(out, **options) as t:
        t.append({"Id": 1, "Name": "La Rose, au top; Marseille: \"superbe\"", "Created on": date(2022, 3, 26)})
        t.append({"Id": 2, "Created on": date(2022, 3, 26), "Last at": datetime.strptime('1998-07-12T23:46:00.000+02:00', "%Y-%m-%dT%H:%M:%S.%f%z"), "Name": "Moi aussi"})
        t.append({"Id": 3, "Name": "<a href=\"http://www.supelec.fr\">Lien</a>", "Created on": date(2022, 3, 26), "Last at": datetime.strptime('1998-07-12T00:46:00.123+02:00', "%Y-%m-%dT%H:%M:%S.%f%z")})


def _convert_row_dates(row: list) -> list:
    """
    Convert date objects to datetime (Excel does not distinguish between dates and datetimes).
    """
    converted_row = []

    for i in range(0, len(row)):
        value = row[i]
        if type(value) == date:
            value = datetime.combine(value, datetime.min.time())
        converted_row.append(value)

    return converted_row
