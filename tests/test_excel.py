from __future__ import annotations

from pathlib import Path
from unittest import TestCase, skipIf

from zut import files
from zut.excel import openpyxl, ExcelWorkbook, split_excel_path
from tests import RESULTS_DIR, SAMPLES_DIR

class Case(TestCase):
    def test_split_excel_path(self):
        self.assertEqual((Path('path.xlsx'), 'table'), split_excel_path('path.xlsx#table'))
        self.assertEqual((Path('path.xlsx'), None), split_excel_path('path.xlsx'))
        self.assertEqual((Path('path'), None), split_excel_path('path'))

    @skipIf(not openpyxl, "openpyxl not available")
    def test_sample(self):
        wb = ExcelWorkbook(SAMPLES_DIR.joinpath('colors-and-formulas.xlsx'))
        self.assertEqual(wb.get_table('toto', default=None), None)

        table = wb.get_table('Tableau1', default=None)
        self.assertEqual(table.name, 'Tableau1')
        self.assertEqual(table.column_names, ['Col1', 'Col2', 'Col3'])
        self.assertEqual(table.min_row_index, 1)
        self.assertEqual(table.min_col_index, 0)
        self.assertEqual(table.row_count, 4)
        self.assertEqual(table.col_count, 3)

        it = iter(table)
        self.assertEqual(next(it).values, ['A', 1, '=Tableau1[[#This Row],[Col2]]*2'])

        accu = ''
        for row in table:
            accu += row["Col1"]
        self.assertEqual(accu, "ABCD")

        self.assertEqual(next(it).values, ['B', 2, '=Tableau1[[#This Row],[Col2]]*2'])
        self.assertEqual(next(it).values, ['C', 3, '=Tableau1[[#This Row],[Col2]]*2'])
        self.assertEqual(next(it).values, ['D', 4, '=Tableau1[[#This Row],[Col2]]*2'])
        with self.assertRaises(StopIteration):
            next(it)

        table = wb.get_table('Tableau2', default=None)
        self.assertEqual(table.name, 'Tableau2')
        self.assertEqual(table.min_row_index, 0)
        self.assertEqual(table.min_col_index, 6)
        self.assertEqual(table.row_count, 2)
        self.assertEqual(table.col_count, 2)

    @skipIf(not openpyxl, "openpyxl not available")
    def test_set(self):
        path = RESULTS_DIR.joinpath('colors-and-formulas__set.xlsx')
        if files.exists(path):
            files.remove(path)
        files.copy(SAMPLES_DIR.joinpath('colors-and-formulas.xlsx'), path)

        wb = ExcelWorkbook(path)

        table = wb.get_table('Tableau1')
        row = table.get_row(1)
        self.assertEqual(row['Col2'], 2)
        row['Col2'] = 20
        self.assertEqual(row[1], 20)
        row[1] = 200
        self.assertEqual(row['Col2'], 200)
        
        table = wb.get_table('Tableau2')
        row = table.get_row(0)
        self.assertEqual(row[0], 'A')
        row[0] = 'AAA'
        self.assertEqual(row[0], 'AAA')

        wb.close()

        wb = ExcelWorkbook(path)
        table = wb.get_table('Tableau1')
        row = table.get_row(1)
        self.assertEqual(row['Col2'], 200)

        table = wb.get_table('Tableau2')
        row = table.get_row(0)
        self.assertEqual(row[0], 'AAA')


    @skipIf(not openpyxl, "openpyxl not available")
    def test_insert_row(self):
        path = RESULTS_DIR.joinpath('colors-and-formulas__insert-row.xlsx')
        if files.exists(path):
            files.remove(path)
        files.copy(SAMPLES_DIR.joinpath('colors-and-formulas.xlsx'), path)

        wb = ExcelWorkbook(path)

        table = wb.get_table('Tableau1')
        row = table.insert_row()
        row['Col1'] = "Inserted"
        row['Col2'] = 100
        self.assertEqual(row['Col2'], 100)

        table = wb.get_table('Tableau2')
        row = table.insert_row()
        row[0] = 'Inserted'
        row[1] = None
        self.assertEqual(row[0], 'Inserted')
        self.assertEqual(row[1], None)

        wb.close()

        wb = ExcelWorkbook(path)
        table = wb.get_table('Tableau1')
        row = table.get_row(4)
        self.assertEqual(row['Col2'], 100)

        table = wb.get_table('Tableau2')
        row = table.get_row(2)
        self.assertEqual(row[0], 'Inserted')
        self.assertEqual(row[1], None)


    @skipIf(not openpyxl, "openpyxl not available")
    def test_insert_col(self):
        path = RESULTS_DIR.joinpath('colors-and-formulas__insert-col.xlsx')
        if files.exists(path):
            files.remove(path)
        files.copy(SAMPLES_DIR.joinpath('colors-and-formulas.xlsx'), path)

        wb = ExcelWorkbook(path)

        table = wb.get_table('Tableau1')
        table.insert_col('More4')
        table.insert_col('More5')
        table.insert_col('More6')
        with self.assertRaises(ValueError):
            table.insert_col('More7')
    
        table = wb.get_table('Tableau2')
        table.insert_col('More3')
        table.insert_col('More4')

        wb.close()

        wb = ExcelWorkbook(path)
        table = wb.get_table('Tableau1')
        row = table.get_row(3)
        self.assertEqual(row['More4'], None)

        table = wb.get_table('Tableau2')
        row = table.get_row(1)
        self.assertEqual(row[0], 'C')
        self.assertEqual(row['More3'], None)


    @skipIf(not openpyxl, "openpyxl not available")
    def test_truncate(self):
        path = RESULTS_DIR.joinpath('colors-and-formulas__truncate.xlsx')
        if files.exists(path):
            files.remove(path)
        files.copy(SAMPLES_DIR.joinpath('colors-and-formulas.xlsx'), path)

        wb = ExcelWorkbook(path)

        table = wb.get_table('Tableau1')
        table.truncate()
        wb.close()

        wb = ExcelWorkbook(path)
        table = wb.get_table('Tableau1')
        self.assertEqual(table.ref, 'A1:C2') # table cannot be empty (must have at least one blank row)
        row = table.get_row(0)
        self.assertEqual(row['Col2'], None)


    @skipIf(not openpyxl, "openpyxl not available")
    def test_truncate_and_insert(self):
        path = RESULTS_DIR.joinpath('colors-and-formulas__truncate-and-insert.xlsx')
        if files.exists(path):
            files.remove(path)
        files.copy(SAMPLES_DIR.joinpath('colors-and-formulas.xlsx'), path)

        wb = ExcelWorkbook(path)

        table = wb.get_table('Tableau1')
        table.truncate()

        row = table.insert_row()
        row['Col1'] = "Inserted"
        row['Col2'] = 100
        self.assertEqual(row['Col2'], 100)

        wb.close()

        wb = ExcelWorkbook(path)
        table = wb.get_table('Tableau1')
        row = table.get_row(0)
        self.assertEqual(row['Col2'], 100)


    @skipIf(not openpyxl, "openpyxl not available")
    def test_insert_in_empty_table(self):
        path = RESULTS_DIR.joinpath('empty-table__inserted.xlsx')
        if files.exists(path):
            files.remove(path)
        files.copy(SAMPLES_DIR.joinpath('empty-table.xlsx'), path)

        wb = ExcelWorkbook(path)

        table = wb.get_table('Tableau1')
        row = table.insert_row()
        row['Col1'] = "Inserted"
        row['Col2'] = 100
        self.assertEqual(row['Col2'], 100)

        wb.close()

        wb = ExcelWorkbook(path)
        table = wb.get_table('Tableau1')
        row = table.get_row(0)
        self.assertEqual(row['Col1'],  "Inserted")
        self.assertEqual(row['Col2'], 100)


    @skipIf(not openpyxl, "openpyxl not available")
    def test_create_table(self):
        path = RESULTS_DIR.joinpath('colors-and-formulas__create-table.xlsx')
        if files.exists(path):
            files.remove(path)
        files.copy(SAMPLES_DIR.joinpath('colors-and-formulas.xlsx'), path)

        wb = ExcelWorkbook(path)

        with self.assertRaises(KeyError):
            wb.get_table('NewTable')

        table = wb.get_table('NewTable', default=None)
        if not table:
            table = wb.create_table('NewTable')
        self.assertEqual(table.column_names, [])
        
        with self.assertRaises(ValueError):
            table.ref
        
        with self.assertRaises(ValueError):
            table.get_row(0)

        row = table.insert_row()
        self.assertEqual(row.values, [])

        table.insert_col("A")
        table.insert_col("B")
        row = table.get_row(0)
        self.assertEqual(row["A"], None)
        row["A"] = 1
        self.assertEqual(row["A"], 1)
        
        row = table.insert_row()
        row["A"] = 2
        row["B"] = 3

        wb.close()
        
        wb = ExcelWorkbook(path)
        table = wb.get_table('NewTable')
        self.assertEqual(table.ref, 'A1:B3')


    @skipIf(not openpyxl, "openpyxl not available")
    def test_create_workbook(self):
        path = RESULTS_DIR.joinpath('new-workbook.xlsx')
        if files.exists(path):
            files.remove(path)

        wb = ExcelWorkbook(path)

        table = wb.get_table('NewTable', default=None)        
        if not table:
            table = wb.create_table('NewTable')
        row = table.insert_row()
        table.insert_col("A")
        table.insert_col("B")
        row["A"] = 1        
        row = table.insert_row()
        row["A"] = 2
        row["B"] = 3

        wb.close()
        
        wb = ExcelWorkbook(path)
        table = wb.get_table('NewTable')
        self.assertEqual(table.ref, 'A1:B3')


    @skipIf(not openpyxl, "openpyxl not available")
    def test_create_empty_table(self):
        path = RESULTS_DIR.joinpath('new-empty-table.xlsx')
        if files.exists(path):
            files.remove(path)

        wb = ExcelWorkbook(path)

        table = wb.get_table('NewTable', default=None)        
        if not table:
            table = wb.create_table('NewTable')
        table.insert_col("A")
        table.insert_col("B")
        wb.close()
        
        wb = ExcelWorkbook(path)
        table = wb.get_table('NewTable')
        self.assertEqual(table.pyxl_worksheet.cell(1, 1).value, 'A')
        self.assertEqual(table.pyxl_worksheet.cell(1, 2).value, 'B')
        self.assertEqual(table.pyxl_worksheet.cell(2, 1).value, None)
        self.assertEqual(table.pyxl_worksheet.cell(2, 2).value, None)
