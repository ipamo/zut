from __future__ import annotations

import logging
import re
from contextlib import nullcontext
from datetime import tzinfo
from io import TextIOWrapper
from pathlib import Path
from urllib.parse import unquote, urlparse

from .. import build_url, skip_utf8_bom
from .base import ColumnInfo, DbAdapter

logger = logging.getLogger(__name__)
notice_logger = logging.getLogger("mssql")

try:
    from pyodbc import Connection, Cursor, connect, drivers

    class MssqlAdapter(DbAdapter[Connection, Cursor, str, str]):
        """
        Database adapter for Microsoft SQL Server (using `pyodbc` driver).
        """
        URL_SCHEME = 'mssql'
        DEFAULT_SCHEMA = 'dbo'
        ONLY_POSITIONAL_PARAMS = True
        EXPECTED_CONNECTION_TYPES = ['pyodbc.Connection']

        @classmethod
        def is_available(cls):
            return True
        

        def _create_connection(self) -> Connection:
            
            def escape(s):
                if ';' in s or '{' in s or '}' in s or '=' in s:
                    return "{" + s.replace('}', '}}') + "}"
                else:
                    return s
                
            r = urlparse(self._connection_url)
            
            server = unquote(r.hostname) or '(local)'
            if r.port:
                server += f',{r.port}'

            # Use "ODBC Driver XX for SQL Server" if available ("SQL Server" seems not to work with LocalDB, and takes several seconds to establish connection on my standard Windows machine with SQL Server Developer).
            driver = "SQL Server"
            for a_driver in sorted(drivers(), reverse=True):
                if re.match(r'^ODBC Driver \d+ for SQL Server$', a_driver):
                    driver = a_driver
                    break

            connection_string = 'Driver={%s};Server=%s;Database=%s;' % (escape(driver), escape(server), escape(r.path.lstrip('/')))

            if r.username:
                connection_string += 'UID=%s;' % escape(unquote(r.username))
                if r.password:
                    connection_string += 'PWD=%s;' % escape(unquote(r.password))
            else:
                connection_string += 'Trusted_Connection=yes;'
                
            connection_string += f"Encrypt={'yes' if r.scheme == 'mssqls' else 'no'};"
            return connect(connection_string, autocommit=self.autocommit)


        def _get_url_from_connection(self):
            with self.cursor() as cursor:
                cursor.execute("SELECT @@SERVERNAME, local_tcp_port, SUSER_NAME(), DB_NAME() FROM sys.dm_exec_connections WHERE session_id = @@spid")
                host, port, user, dbname = next(iter(cursor))
            return build_url(scheme=self.URL_SCHEME, username=user, hostname=host, port=port, path='/'+dbname)
        

        # -------------------------------------------------------------------------
        # Execution
        #
        
        def execute_file(self, path: str|Path, params: list|tuple|dict = None, *, cursor: Cursor = None, results: bool|TextIOWrapper|str|Path = False, tz: tzinfo = None, offset: int = None, limit: int = None, encoding: str = 'utf-8') -> None:
            import sqlparse  # not at the top because the enduser might not need this feature

            # Read file
            with open(path, 'r', encoding=encoding) as fp:
                skip_utf8_bom(fp)
                file_content = fp.read()

            # Split queries
            queries = sqlparse.split(file_content, encoding)
                
            # Execute all queries
            query_count = len(queries)
            with nullcontext(cursor) if cursor else self.cursor() as _cursor:
                for query_index, query in enumerate(queries):
                    query_num = query_index + 1
                    if logger.isEnabledFor(logging.DEBUG):
                        title = re.sub(r"\s+", " ", query).strip()[0:100] + "…"
                        logger.debug("Execute query %d/%d: %s ...", query_num, query_count, title)

                    # Execute query
                    query_id = f'{query_num}/{query_count}' if query_count > 1 else None
                    if query_num < query_count:
                        # Not last query: should not have results
                        self.execute_query(query, params, cursor=_cursor, results='warning', tz=tz, query_id=query_id, offset=offset, limit=limit)

                    else:
                        # Last query
                        return self.execute_query(query, params, cursor=_cursor, results=results, tz=tz, query_id=query_id, offset=offset, limit=limit)


        # -------------------------------------------------------------------------
        # Queries
        #
            
        def _paginate_parsed_query(self, selectpart: str, orderpart: str, *, offset: int, limit: int|None) -> str:
            if orderpart:
                result = f"{selectpart} {orderpart} OFFSET {offset} ROWS"
                if limit is not None:
                    result += f" FETCH NEXT {limit} ROWS ONLY"
                return result
            elif limit is not None:
                if offset > 0:
                    raise ValueError("an ORDER BY clause is required for OFFSET")
                return f"SELECT TOP {limit} * FROM ({selectpart}) s"
            else:
                return selectpart


        def get_select_table_query(self, table: str|tuple = None, *, schema_only = False) -> str:
            schema, table = self.split_name(table)
            
            query = f'SELECT * FROM {self._escape_identifier(schema)}.{self._escape_identifier(table)}'
            if schema_only:
                query += ' WHERE 1 = 0'

            return query
            

        def _escape_identifier(self, value: str) -> str:
            return f"[{value.replace(']', ']]')}]"
        

        def _escape_literal(self, value: str) -> str:
            return f"'" + value.replace("'", "''") + "'"


        def _log_cursor_messages(self, cursor: Cursor):
            if cursor.messages:
                for msg_type, msg_text in cursor.messages:
                    m = re.match(r"^\[Microsoft\]\[ODBC Driver \d+ for SQL Server\]\[SQL Server\](.+)$", msg_text)
                    if m:
                        msg_text = m[1]
                    
                    if msg_type in {"[01000] (0)", "[01000] (50000)"}: # PRINT or RAISERROR
                        level = logging.INFO
                    else:
                        msg_text = f"{msg_type} {msg_text}"
                        if msg_type == "[01003] (8153)": # Avertissement : la valeur NULL est éliminée par un agrégat ou par une autre opération SET.
                            level = logging.INFO
                        else:
                            level = logging.WARNING

                    notice_logger.log(level, f"{msg_text}")

        # -------------------------------------------------------------------------
        # Tables and columns
        #    

        def table_exists(self, table: str|tuple = None) -> bool:        
            schema, table = self.split_name(table)

            query = "SELECT CASE WHEN EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = ? AND table_name = ?) THEN 1 ELSE 0 END"
            params = [schema, table]

            return self.get_scalar(query, params)

            
        def drop_table(self, table: str|tuple = None):
            schema, table = self.split_name(table)
            query = "DROP TABLE %s.%s" % (schema, table)
            self.execute_query(query)

            
        def truncate_table(self, table: str|tuple = None, *, cascade: bool = False):
            if cascade:
                raise ValueError("Cascade truncate not supported by mssql.")
            schema, table = self.split_name(table)
            query = "TRUNCATE TABLE %s.%s" % (schema, table)
            self.execute_query(query)
            

        def _update_column_info(self, info: ColumnInfo, cursor: Cursor, index: int):
            info.name, info.python_type, display_size, internal_size, precision, scale, info.nullable = cursor.description[index]


except ImportError:  

    class MssqlAdapter(DbAdapter):
        """
        Database adapter for Microsoft SQL Server (using `pyodbc` driver).
        """
                
        URL_SCHEME = 'mssql'
        DEFAULT_SCHEMA = 'dbo'
        ONLY_POSITIONAL_PARAMS = True
        EXPECTED_CONNECTION_TYPES = ['pyodbc.Connection']

        @classmethod
        def is_available(cls):
            return False
