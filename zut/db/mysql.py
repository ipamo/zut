from __future__ import annotations

import logging
from urllib.parse import urlparse

from .base import DbAdapter

logger = logging.getLogger(__name__)
notice_logger = logging.getLogger("mysql")

try:
    from MySQLdb import connect
    from MySQLdb.connections import Connection
    from MySQLdb.cursors import Cursor

    # TODO: cursor/procedure messages (_log_execute_messages?)
    class MysqlAdapter(DbAdapter[Connection, Cursor]):
        """
        Database adapter for Microsoft SQL Server (using `pyodbc` driver).
        """
        URL_SCHEME = 'mysql'
        EXPECTED_CONNECTION_TYPES = ['MySQLdb.connections.Connection'] # Compatible with the Python DB API interface version 2 (not "_mysql.connection")

        @classmethod
        def is_available(cls):
            return True
        

        def _create_connection(self) -> Connection:
            r = urlparse(self._connection_url)
            kwargs = {}
            if r.hostname:
                kwargs['host'] = r.hostname
            if r.port:
                kwargs['port'] = r.port
            if r.path:
                kwargs['database'] = r.path.lstrip('/')
            if r.username:
                kwargs['user'] = r.username
            if r.password:
                kwargs['password'] = r.password
            return connect(**kwargs, sql_mode='STRICT_ALL_TABLES', autocommit=self.autocommit)


        def _get_url_from_connection(self):
            raise NotImplementedError() # TODO
        

        def get_select_table_query(self, table: str|tuple = None, *, schema_only = False) -> str:
            _, table = self.split_name(table)
            
            query = f'SELECT * FROM {self.escape_identifier(table)}'
            if schema_only:
                query += ' WHERE 1 = 0'

            return query
            

        def escape_identifier(self, value: str):
            if not isinstance(value, str):
                raise TypeError(f"Invalid identifier: {value} (type: {type(value)})")
            if '`' in value:
                raise ValueError(f"Identifier cannot contain back ticks")
            return f"`" + value + "`"

    
        def split_name(self, name: str|tuple = None) -> tuple[str,str]:
            schema, name = super().split_name(name)
            if schema is not None:
                raise ValueError(f"Cannot use schema (\"{schema}\") with mysql.")
            return None, name


        def table_exists(self, table: str|tuple = None) -> bool:        
            _, table = self.split_name(table)

            query = "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = %s)"
            params = [table]

            return self.get_scalar(query, params) == 1
            

except ImportError:  

    class MysqlAdapter(DbAdapter):
        """
        Database adapter for Microsoft SQL Server (using `pyodbc` driver).
        """
                
        URL_SCHEME = 'mysql'
        EXPECTED_CONNECTION_TYPES = ['MySQLdb.connections.Connection'] # Compatible with the Python DB API interface version 2 (not "_mysql.connection")

        @classmethod
        def is_available(cls):
            return False
