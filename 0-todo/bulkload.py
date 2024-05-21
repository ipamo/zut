# TODO: use setlocale only for get_locale_decimal_point => csv_decimal_separator. Other uses may have side effects.
from contextlib import nullcontext
import subprocess
import sys
import io
from pathlib import Path
import tempfile
import MySQLdb
import pyodbc
import psycopg
from pyodbc import Connection as MssqlConnection
from MySQLdb.connections import Connection as MysqlConnection
from psycopg import Connection as PgConnection

def prepare_target_table(conn):
    false_literal = 'false' if isinstance(conn, PgConnection) else '0'

    with conn.cursor() as cursor:
        cursor.execute(f"""
DROP TABLE IF EXISTS csv_target;
                       
CREATE TABLE csv_target (
    id BIGINT NOT NULL PRIMARY KEY {'AUTO_INCREMENT' if isinstance(conn, MysqlConnection) else ('GENERATED ALWAYS AS IDENTITY' if isinstance(conn, PgConnection) else 'IDENTITY')}
    ,name VARCHAR(100) NOT NULL
    ,price DECIMAL(18,4) NULL
    ,unit VARCHAR(3) NULL
    ,qty INT NULL
    ,is_promo {'BIT' if isinstance(conn, MssqlConnection) else 'BOOL'} NOT NULL DEFAULT {false_literal}
    ,updated_at  {'TIMESTAMPTZ' if isinstance(conn, PgConnection) else 'DATETIME'} NOT NULL DEFAULT {'GETDATE()' if isinstance(conn, MssqlConnection) else 'NOW()'}
    ,updated_at0 {'TIMESTAMP'   if isinstance(conn, (PgConnection,MysqlConnection)) else 'DATETIME'} NOT NULL DEFAULT {'GETDATE()' if isinstance(conn, MssqlConnection) else 'NOW()'}
);

INSERT INTO csv_target (name)
VALUES ('Default');
""")

def check_target_table(conn, expected: list[dict] = None):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM csv_target ORDER BY id")
        for row in cursor:
            print(row)

def escape_csv_value(conn, value):
    if value is None:
        return '' # TODO
    value = str(value)
    if value == '':
        return '""' # TODO
    if '\r' in value or '\n' in value or ',' in value or '"' in value:
        return '"' + value.replace('"', '""') + '"'
    return value
    
def load_csv(conn, rows: list[list]):
    with nullcontext(io.StringIO()) if isinstance(conn, PgConnection) else tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as tmp:
        print('<stringio>' if isinstance(conn, PgConnection) else tmp.name)

        # TODO: utf-8 BOM?
        for row in rows:
            for i, value in enumerate(row):
                if i > 0:
                    tmp.write(',')
                tmp.write(escape_csv_value(conn, value))
            tmp.write('\n')
            tmp.flush()

        # check content
        tmp.seek(0)
        if isinstance(conn, PgConnection):
            print(tmp.getvalue())
        else:
            print(Path(tmp.name).read_text(encoding='utf-8'))

        tmp.seek(0)
        if isinstance(conn, MssqlConnection):
            # TODO: does not work: BULK INSERT statement refers to paths from the perspective of the SQL Server machine
            # Use SqlBulkCopy in Powershell or C# instead, or bcp.exe
            # /opt/mssql-tools18/bin/bcp
            # query = f"BULK INSERT csv_target FROM '{tmp.name}' WITH (FIELDTERMINATOR = ',', FIELDQUOTE = ',', KEEPNULLS"
            # if sys.platform != 'linux': # Keyword or statement option 'CODEPAGE' is not supported on the 'Linux' platform.
            #     query += ", CODEPAGE = 'utf-8'" #TODO: test on windows
            # query += ")"
            # with conn.cursor() as cursor:
            #     conn.execute(query)
            #     return cursor.rowcount
            subprocess.run(['/opt/mssql-tools18/bin/bcp', 'csv_target', 'in', tmp.name, '-S', '127.0.0.1', '-U', 'sa', '-P', 'testmeZ0', '-d', 'TestZut', '-u'], stdout=sys.stdout, stderr=sys.stderr)
            #TODO: make it non-interactive
            pass #TODO

        elif isinstance(conn, PgConnection):
            query = "COPY csv_target (id, unit, name) FROM STDIN (FORMAT csv, ENCODING 'utf-8', DELIMITER ',', QUOTE '\"', ESCAPE '\"', NULL '', HEADER match)"
            with conn.cursor() as cursor:
                with cursor.copy(query) as copy:
                    while True:
                        data = tmp.read(65536)
                        if not data:
                            break
                        copy.write(data)
                    return cursor.rowcount
                        
        else:
            pass #TODO
        
def run(conn_type):
    if conn_type == MssqlConnection:
        print("##### mssql")
        conn = pyodbc.connect("Driver={ODBC Driver 18 for SQL Server};Server=127.0.0.1;Database=TestZut;UID=sa;PWD=testmeZ0;Encrypt=no;", autocommit=True)
    elif conn_type == MysqlConnection:
        print("##### mysql")
        conn = MySQLdb.connect(host='127.0.0.1', user='root', password='testmeZ0', database='test_zut', sql_mode='STRICT_ALL_TABLES', autocommit=True)
    elif conn_type == PgConnection:
        print("##### pg")
        conn = psycopg.connect("postgres://postgres:testmeZ0@127.0.0.1/test_zut", autocommit=True)
    else:
        raise NotImplementedError()

    if not isinstance(conn, conn_type):
        raise ValueError(f"conn type: {type(conn)}")

    prepare_target_table(conn)
    check_target_table(conn)
    load_csv(conn, [
        ['id', 'unit', 'name'],
        [2, None, "Deux"],
        #[3, None, "Trois678901234567890"], #TODO: test insert too long
        [4, None, "Quatre,Four"],
        [5, None, "Cinq\nFive"],
        [6, 'X', "Six\r\nSix"],
        [7, '', "Sept \"Seven\""],
    ])
    rowcount = check_target_table(conn)
    print(rowcount)

    conn.close()

run(MssqlConnection)
#run(MysqlConnection)
#run(PgConnection)
#TODO: add sqlite
