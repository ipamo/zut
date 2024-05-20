from __future__ import annotations

import logging
import re
from contextlib import nullcontext
from typing import Any

from .. import build_url
from .base import DbAdapter, T_Connection, T_Cursor

logger = logging.getLogger(__name__)


def pg_notice_handler(diag: Diagnostic, logger: logging.Logger = None):
    """
    Handler required by psycopg 3 `connection.add_notice_handler()`.
    """
    # determine level
    level = pg_get_logging_level(diag.severity_nonlocalized)
    
    # determine logger
    if logger:
        logger = logger
        message = diag.message_primary
    else:
        # parse context
        m = re.match(r"^fonction [^\s]+ (\w+)", diag.context or '')
        if m:
            logger = logging.getLogger(f"pg:{m[1]}")
            message = diag.message_primary
        else:
            logger = logging.getLogger("pg")
            message = f"{diag.context or ''}{diag.message_primary}"

    # write log
    logger.log(level, message)


def pg_get_logging_level(severity_nonlocalized: str):
    if severity_nonlocalized.startswith('DEBUG'): # not sent to client (by default)
        return logging.DEBUG
    elif severity_nonlocalized == 'LOG': # not sent to client (by default), written on server log (LOG > ERROR for log_min_messages)
        return logging.DEBUG
    elif severity_nonlocalized == 'NOTICE': # sent to client (by default) [=client_min_messages]
        return logging.DEBUG
    elif severity_nonlocalized == 'INFO': # always sent to client
        return logging.INFO
    elif severity_nonlocalized == 'WARNING': # sent to client (by default) [=log_min_messages]
        return logging.WARNING
    elif severity_nonlocalized in ['ERROR', 'FATAL']: # sent to client
        return logging.ERROR
    elif severity_nonlocalized in 'PANIC': # sent to client
        return logging.CRITICAL
    else:
        return logging.ERROR


class BasePgAdapter(DbAdapter[T_Connection, T_Cursor]):
    """
    Base class for PostgreSql database adapters (:class:`PgAdapter` using `psycopg` (v3) driver or :class:`Pg2Adapter` using `psycopg2` driver).
    """
    URL_SCHEME = 'postgresql' # See: https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
    _ALT_SCHEMES = {'pg', 'postgres'}
    DEFAULT_SCHEMA = 'public'    
    EXPECTED_CONNECTION_TYPES = ['psycopg.Connection']
    _sql: Any


    def _create_connection(self):
        return connect(self._connection_url, autocommit=self.autocommit)
    
    
    def _get_url_from_connection(self):
        with self.cursor() as cursor:
            cursor.execute("SELECT session_user, inet_server_addr(), inet_server_port(), current_database()")
            user, host, port, dbname = next(iter(cursor))
        return build_url(scheme=self.URL_SCHEME, username=user, hostname=host, port=port, path='/'+dbname)

    
    def execute_procedure(self, name: str|tuple, *args):
        schema, name = self.split_name(name)
        
        query = "CALL "
        params = []
            
        if schema:    
            query +="{}."
            params += [self._sql.Identifier(schema)]

        query += "{}"
        params += [self._sql.Identifier(name)]

        query += "(" + ", ".join(['{}'] * len(args)) + ")"
        params += [self._get_composable_param(arg) for arg in args]

        with self.cursor() as cursor:
            with self.register_notice_handler(if_exists=None, logprefix=f"pg:{schema + '.' if schema and schema != self.DEFAULT_SCHEMA else ''}{name}"):
                cursor.execute(self._sql.SQL(query).format(*params))
                return cursor
            

    def register_notice_handler(self, if_exists = '__raise__', logprefix = 'pg'):
        raise NotImplementedError()
    
    
    def get_select_table_query(self, table: str|tuple = None, *, schema_only = False):
        schema, table = self.split_name(table)

        query = "SELECT * FROM "
        params = []
            
        if schema:    
            query +="{}."
            params += [self._sql.Identifier(schema)]

        query += "{}"
        params += [self._sql.Identifier(table)]
        
        if schema_only:
            query += ' WHERE false'

        return self._sql.SQL(query).format(*params)


    def _get_composable_param(self, value):
        if value is None:
            return self._sql.SQL("null")
        elif value == '__now__':
            return self._sql.SQL("NOW()")
        elif isinstance(value, self._sql.Composable):
            return value
        else:
            return self._sql.Literal(value)
        

    def escape_identifier(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f"Invalid identifier: {value} (type: {type(value)})")
        if '"' in value:
            raise ValueError(f"Identifier cannot contain double quotes")
        return '"' + value + '"'
    

    def table_exists(self, table: str|tuple = None) -> bool:
        schema, table = self.split_name(table)

        query = "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = %s AND tablename = %s)"
        params = [schema, table]

        return self.get_scalar(query, params)


try:
    from psycopg import Connection, Cursor, connect, sql
    from psycopg.errors import Diagnostic


    class PgAdapter(BasePgAdapter[Connection, Cursor]):
        """
        Database adapter for PostgreSQL (using `psycopg` (v3) driver).
        """
        _sql = sql

        @classmethod
        def is_available(cls):
            return True
        

        def register_notice_handler(self, if_exists = '__raise__', logprefix = 'pg'):
            if self.connection._notice_handlers:
                if if_exists != '__raise__':
                    return nullcontext(if_exists)
                raise ValueError(f"notice handler already registered: {self.connection._notice_handlers}")

            return PgNoticeManager(self.connection, logprefix)


    class PgNoticeManager:
        """
        This class can be used as a context manager that remove the handler on exit.

        The actual handler required by psycopg 3 `connection.add_notice_handler()` is the `pg_notice_handler` method.
        """
        def __init__(self, connection: Connection, logprefix: str = None):
            self.connection = connection
            self.logger = logging.getLogger(logprefix) if logprefix else None
            self.connection.add_notice_handler(self.handler)

        def __enter__(self):
            return self.handler
        
        def __exit__(self, *args):
            self.connection._notice_handlers.remove(self.handler)


        def handler(self, diag: Diagnostic):
            return pg_notice_handler(diag, logger=self.logger)


except ImportError:

    class PgAdapter(BasePgAdapter):
        """
        Database adapter for PostgreSQL (using `psycopg` (v3) driver).
        """

        @classmethod
        def is_available(cls):
            return False
