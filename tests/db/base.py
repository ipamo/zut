from __future__ import annotations

from unittest import SkipTest
from urllib.parse import urlparse

from tests import CONFIG
from zut import ZUT_ROOT, slugify
from zut.db import DbAdapter


class DbBase:
    adapter: type[DbAdapter]
    config_key_prefix: str
    url: str
    db: DbAdapter
    mark: str


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
        cls.db.execute_query(f'CREATE TABLE {cls.mark}_tryout (id BIGINT NOT NULL PRIMARY KEY, name TEXT NOT NULL, price DECIMAL(18,4) NULL, col_float FLOAT NULL, col_date DATE, col_time TIME, col_timestamp TIMESTAMP)')


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
