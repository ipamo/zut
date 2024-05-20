from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest import SkipTest
from urllib.parse import urlparse

from tests import CONFIG, SAMPLES_DIR
from zut import ZUT_ROOT, slugify
from zut.db import DbAdapter, PgAdapter, Pg2Adapter, MssqlAdapter, MysqlAdapter
from zut.db.base import ColumnInfo


class DbBase:
    adapter: type[DbAdapter]
    config_key_prefix: str
    url: str
    db: DbAdapter
    mark: str

    sql_types = {
        'id': None,
        'name': None,
        'price': None,
        'col_text': None,
        'col_float': None,
        'col_date': None,
        'col_time': None,
        'col_timestamp': None,
    }


    @classmethod
    def setUpClass(cls):
        cls.url = CONFIG.get('zut-tests', f'{cls.config_key_prefix}_url', fallback=None)
        if not cls.url:
            raise SkipTest(f"{cls.config_key_prefix}_url not configured")
        
        cls.db = cls.adapter(cls.url, autocommit=True)

        # Check database name
        if not CONFIG.getboolean('zut-tests', 'allow_db_name_without_test', fallback=False):
            url = cls.db.get_url()
            r = urlparse(url)
            dbname = r.path.lstrip('/')
            if not (dbname.startswith(("test", "Test")) or dbname.endswith(("test", "Test"))):
                raise ValueError(f"invalid dbname \"{dbname}\": does not start or end with \"test\"")
        
        mark_base = slugify(cls.adapter.__name__)
        if mark_base.endswith('adapter'):
            mark_base = mark_base[:-len('adapter')]
        cls.mark = mark_base
        
        # Execute sql-utils
        sql_utils = ZUT_ROOT.joinpath("db", "sql-utils", f"{cls.mark}.sql")
        if sql_utils.exists():
            cls.db.execute_file(sql_utils)

        cls.db.execute_query(f'DROP TABLE IF EXISTS {cls.mark}_tryout')
        cls.db.execute_query(f"""CREATE TABLE {cls.mark}_tryout (
            id BIGINT NOT NULL PRIMARY KEY
            ,name VARCHAR(100) NOT NULL
            ,price DECIMAL(18,4) NULL
            ,col_text TEXT NULL
            ,col_float FLOAT NULL
            ,col_date DATE
            ,col_time TIME NULL
            ,col_timestamp TIMESTAMP NOT NULL
        )""")


    @classmethod
    def tearDownClass(cls):
        cls.db.__exit__()

    
    def test_basics(self):
        self.assertEqual(1, self.db.get_scalar("SELECT 1"))
        self.assertEqual({'id': 1, 'name': 'A'}, self.db.get_dict("SELECT 1 AS id, 'A' AS name"))
        self.assertEqual([{'id': 1, 'name': 'A'}, {'id': 99, 'name': None}], self.db.get_dicts("SELECT 1 AS id, 'A' AS name UNION SELECT 99, null"))
    

    def test_table_exists(self):
        self.assertTrue(self.db.table_exists(f'{self.mark}_tryout'))
        self.assertFalse(self.db.table_exists(f'{self.mark}_nope'))


    def test_get_table_column_names(self):
        self.assertEqual(['id', 'name', 'price'], self.db.get_table_column_names(f'{self.mark}_tryout')[0:3])


    def test_truncate(self):
        self.db.execute_query("DROP TABLE IF EXISTS using_table")
        self.db.execute_query("DROP TABLE IF EXISTS ref_table")
        
        self.db.execute_query("CREATE TABLE ref_table (id int NOT NULL PRIMARY KEY)")
        self.db.execute_query("CREATE TABLE using_table (id int NOT NULL PRIMARY KEY, ref_id int NULL REFERENCES ref_table(id))")

        self.db.execute_query("INSERT INTO ref_table (id) VALUES (1)")
        self.db.execute_query("INSERT INTO using_table (id, ref_id) VALUES (1, 1)")
        
        self.assertEqual(1, self.db.get_scalar("SELECT COUNT(*) FROM ref_table"))
        self.assertEqual(1, self.db.get_scalar("SELECT COUNT(*) FROM using_table"))
        
        self.db.truncate_table("using_table")
        self.db.execute_query("DELETE FROM ref_table")

        self.assertEqual(0, self.db.get_scalar("SELECT COUNT(*) FROM using_table"))
        self.assertEqual(0, self.db.get_scalar("SELECT COUNT(*) FROM ref_table"))


    def test_get_table_columns(self):
        expected = [
            {'name': 'id', 'python_type': int, 'sql_type': self.sql_types['id'], 'nullable': False},
            {'name': 'name', 'python_type': str, 'sql_type': self.sql_types['name'], 'nullable': False},
            {'name': 'price', 'python_type': Decimal, 'sql_type': self.sql_types['price'], 'nullable': True},
            {'name': 'col_text', 'python_type': str, 'sql_type': self.sql_types['col_text'], 'nullable': True},
            {'name': 'col_float', 'python_type': float, 'sql_type': self.sql_types['col_float'], 'nullable': True},
            {'name': 'col_date', 'python_type': date, 'sql_type': self.sql_types['col_date'], 'nullable': True},
            {'name': 'col_time', 'python_type': timedelta if isinstance(self.db, MysqlAdapter) else time, 'sql_type': self.sql_types['col_time'], 'nullable': True},
            {'name': 'col_timestamp', 'python_type': datetime, 'sql_type': self.sql_types['col_timestamp'], 'nullable': False},
        ]

        if isinstance(self.db, (PgAdapter, Pg2Adapter)):
            # Cannot get 'nullable' from cursor
            for ex in expected:
                ex['nullable'] = None
        elif isinstance(self.db, MssqlAdapter):
            # Python type for 'timestamp' is 'bytearray'
            for ex in expected:
                if ex['name'] == 'col_timestamp':
                    ex['python_type'] = bytearray

        def get_actual_from_columninfo(info: ColumnInfo):
            actual = {}
            for key, value in info.__dict__.items():
                if key not in ['sql_typecode']:
                    actual[key] = value
            return actual

        self.assertEqual(expected, [get_actual_from_columninfo(info) for info in self.db.get_table_columns(f'{self.mark}_tryout')])


    def test_load_csv_ordered(self):
        if isinstance(self.db, MssqlAdapter):
            raise SkipTest("TODO")

        self.db.execute_query(
            f"""
            DROP TABLE IF EXISTS load_csv_ordered;

            CREATE TABLE load_csv_ordered (
                id int NOT NULL PRIMARY KEY
                ,str0_col text NULL
                ,str_col text NULL
                ,bool_col {'bit' if isinstance(self.db, MssqlAdapter) else 'bool'} NULL
                ,int_col int NULL
                ,decimal_col decimal(5,3) NULL
            )
            """)

        if isinstance(self.db, MssqlAdapter):
            self.db.load_from_csv(SAMPLES_DIR.joinpath('mixed-noheaders.csv'), 'load_csv_ordered', merge='truncate', noheaders=True)
        else:
            self.db.load_from_csv(SAMPLES_DIR.joinpath('mixed-mysql.csv' if isinstance(self.db, MysqlAdapter) else 'mixed.csv'), 'load_csv_ordered', merge='truncate')

        actual = self.db.get_dicts("SELECT * FROM load_csv_ordered")
        self.assertEqual(actual, self._get_mixed_data())
    

    def test_load_csv_nonordered(self):
        if isinstance(self.db, MssqlAdapter):
            raise SkipTest("TODO")
        if isinstance(self.db, MysqlAdapter):
            raise SkipTest("TODO") # TODO: reordering actually does NOT work
        
        self.db.execute_query(
            f"""
            DROP TABLE IF EXISTS load_csv_nonordered;

            CREATE TABLE load_csv_nonordered (
                id int NOT NULL PRIMARY KEY
                ,str_col text NULL
                ,str0_col text NULL
                ,bool_col {'bit' if isinstance(self.db, MssqlAdapter) else 'bool'} NULL
                ,int_col int NULL
                ,decimal_col decimal(5,3) NULL
            )
            """)

        self.db.load_from_csv(SAMPLES_DIR.joinpath('mixed-mysql.csv' if isinstance(self.db, MysqlAdapter) else 'mixed.csv'), 'load_csv_nonordered', columns=['id', 'str0_col', 'str_col', 'bool_col', 'int_col', 'decimal_col'], merge='truncate')
        
        actual = self.db.get_dicts("SELECT * FROM load_csv_nonordered")
        self.assertEqual(actual, self._get_mixed_data())


    def test_load_csv_upsert(self):
        if isinstance(self.db, MssqlAdapter):
            raise SkipTest("TODO")
        
        self.db.execute_query(
            f"""
            DROP TABLE IF EXISTS load_csv_upsert;

            CREATE TABLE load_csv_upsert (
                id int NOT NULL PRIMARY KEY
                ,str0_col text NULL
                ,str_col text NULL
                ,bool_col {'bit' if isinstance(self.db, MssqlAdapter) else 'bool'} NULL
                ,int_col int NULL
                ,decimal_col decimal(5,3) NULL
            );

            INSERT INTO load_csv_upsert (id, str0_col, str_col, bool_col, int_col, decimal_col)
            VALUES
                (1, 'OLD', 'a', {'1' if isinstance(self.db, MssqlAdapter) else 'true'}, 1, 1)
                ,(7, 'KEEP', null, null, null, null);
            """)

        self.db.load_from_csv(SAMPLES_DIR.joinpath('mixed-mysql.csv' if isinstance(self.db, MysqlAdapter) else 'mixed.csv'), 'load_csv_upsert', merge='upsert')

        actual = self.db.get_dicts("SELECT * FROM load_csv_upsert ORDER BY id")
        self.assertEqual(actual, self._get_mixed_data() + [{'id': 7, 'str0_col': 'KEEP', 'str_col': None, 'bool_col': None,  'int_col': None, 'decimal_col': None}])


    def _get_mixed_data(self):
        return [
            {'id': 1, 'str0_col': 'X', 'str_col': 'a',  'bool_col': 1 if isinstance(self.db, MysqlAdapter) else True, 'int_col': 1, 'decimal_col': Decimal('1')},
            {'id': 2, 'str0_col': 'X', 'str_col': 'b',  'bool_col': 0 if isinstance(self.db, MysqlAdapter) else False, 'int_col': 2, 'decimal_col': Decimal('2.2')},
            {'id': 3, 'str0_col': 'X', 'str_col': 'c',  'bool_col': 1 if isinstance(self.db, MysqlAdapter) else True,  'int_col': 3, 'decimal_col': Decimal('3.33')},
            {'id': 4, 'str0_col': 'X', 'str_col': 'd',  'bool_col': 0 if isinstance(self.db, MysqlAdapter) else False, 'int_col': 4, 'decimal_col': Decimal('4.444')},
            {'id': 5, 'str0_col': 'X', 'str_col': '',   'bool_col': None,  'int_col': None, 'decimal_col': None},
            {'id': 6, 'str0_col': 'X', 'str_col': None, 'bool_col': None,  'int_col': None, 'decimal_col': None},
        ]
