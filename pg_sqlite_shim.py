"""
PostgreSQL shim that mimics sqlite3 API.
- Uses Transaction Pooler (port 6543) for speed
- Uses connection pool to reuse connections
"""
import re
import queue
import threading
import pg8000.dbapi as _pg

# ==== CONFIG ====
import os

PG_PARAMS = {
    'user': os.environ.get('PG_USER', 'neondb_owner'),
    'password': os.environ.get('PG_PASSWORD', 'npg_UNM4lncbXf0k'),
    'host': os.environ.get('PG_HOST', 'ep-crimson-term-b8rsm466-pooler.c-14.us-east-1.aws.neon.tech'),
    'port': int(os.environ.get('PG_PORT', '5432')),
    'database': os.environ.get('PG_DATABASE', 'neondb'),
    'ssl_context': True
}

POOL_SIZE = 20  # Number of pooled connections

# ==== CONNECTION POOL ====
_pool = queue.Queue(maxsize=POOL_SIZE)
_pool_lock = threading.Lock()
_pool_initialized = False


def _create_pg_connection():
    return _pg.connect(**PG_PARAMS)


def _init_pool():
    global _pool_initialized
    with _pool_lock:
        if _pool_initialized:
            return
        for _ in range(POOL_SIZE):
            try:
                c = _create_pg_connection()
                _pool.put(c)
            except Exception:
                pass
        _pool_initialized = True


def _get_pg_connection():
    _init_pool()
    try:
        conn = _pool.get_nowait()
        # Test if connection is alive
        try:
            cur = conn.cursor()
            cur.execute('SELECT 1')
            cur.fetchone()
            cur.close()
            return conn
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return _create_pg_connection()
    except queue.Empty:
        return _create_pg_connection()


def _return_pg_connection(conn):
    if conn is None:
        return
    try:
        if _pool.full():
            conn.close()
        else:
            _pool.put_nowait(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


class Row:
    """Mimics sqlite3.Row"""
    def __init__(self, col_names, values):
        self._col_names = list(col_names)
        self._values = list(values)
        self._index = {n: i for i, n in enumerate(self._col_names)}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        try:
            return self._values[self._index[key]]
        except KeyError:
            raise IndexError(f'No item with that key: {key}')

    def keys(self):
        return list(self._col_names)

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return f'Row({dict(zip(self._col_names, self._values))})'


def _convert_sql(sql):
    # Placeholders: ? -> %s
    sql = sql.replace('?', '%s')
    
    # SQLite AUTOINCREMENT -> PostgreSQL SERIAL
    sql = re.sub(
        r'INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT',
        'SERIAL PRIMARY KEY',
        sql,
        flags=re.IGNORECASE
    )
    
    # SQLite BLOB -> BYTEA
    sql = re.sub(r'\bBLOB\b', 'BYTEA', sql, flags=re.IGNORECASE)
    
    return sql


class Cursor:
    def __init__(self, conn):
        self._conn = conn
        self._pg_cur = conn._pg_conn.cursor()
        self.lastrowid = None
        self.rowcount = 0
        self.description = None
        self._col_names = []

    def execute(self, sql, params=None):
        sql_stripped = sql.strip()
        upper = sql_stripped.upper()
        
        is_insert_or = upper.startswith('INSERT OR REPLACE') or upper.startswith('INSERT OR IGNORE')
        
        if is_insert_or:
            sql_stripped = re.sub(
                r'^\s*INSERT\s+OR\s+(REPLACE|IGNORE)\s+INTO',
                'INSERT INTO',
                sql_stripped,
                flags=re.IGNORECASE
            )
            if 'ON CONFLICT' not in sql_stripped.upper():
                sql_stripped = sql_stripped.rstrip().rstrip(';') + ' ON CONFLICT DO NOTHING'
            sql = sql_stripped
        
        no_id_tables = ['user_profiles', 'passcodes', 'deposit_addresses', 'settings', 'chat_read_status', 'wishlist']
        lower_sql = sql_stripped.lower()
        skip_returning = any(t in lower_sql for t in no_id_tables)
        is_plain_insert = upper.startswith('INSERT INTO') and 'RETURNING' not in upper
        
        converted = _convert_sql(sql)
        
        # Try with RETURNING id first
        if is_plain_insert:
            converted_with_id = converted.rstrip().rstrip(';') + ' RETURNING id' if not skip_returning else converted
        else:
            converted_with_id = converted
        
        self._col_names = []
        self.description = None
        self.lastrowid = None
        
        try:
            if params is None:
                self._pg_cur.execute(converted_with_id)
            else:
                if isinstance(params, dict):
                    self._pg_cur.execute(converted_with_id, params)
                else:
                    self._pg_cur.execute(converted_with_id, tuple(params))
            
            if self._pg_cur.description:
                self._col_names = [d[0] for d in self._pg_cur.description]
                self.description = [(n, None, None, None, None, None, None) for n in self._col_names]
                if is_plain_insert:
                    try:
                        row = self._pg_cur.fetchone()
                        if row:
                            self.lastrowid = row[0]
                    except Exception:
                        pass
        except Exception as e:
            # ALWAYS rollback to clear aborted transaction state (PostgreSQL behavior)
            try:
                self._conn._pg_conn.rollback()
                self._pg_cur = self._conn._pg_conn.cursor()
            except Exception:
                pass
            # If RETURNING id failed because table has no 'id', retry without RETURNING
            err_msg = str(e).lower()
            if is_plain_insert and ('does not exist' in err_msg or 'column' in err_msg and 'id' in err_msg):
                # Rollback the failed transaction
                try:
                    self._conn._pg_conn.rollback()
                except Exception:
                    pass
                # Recreate cursor (transaction was aborted)
                self._pg_cur = self._conn._pg_conn.cursor()
                # Retry without RETURNING id
                if params is None:
                    self._pg_cur.execute(converted)
                else:
                    if isinstance(params, dict):
                        self._pg_cur.execute(converted, params)
                    else:
                        self._pg_cur.execute(converted, tuple(params))
            else:
                raise
        
        self.rowcount = self._pg_cur.rowcount
        
        return self

    def executemany(self, sql, seq_of_params):
        converted = _convert_sql(sql)
        self._pg_cur.executemany(converted, [tuple(p) for p in seq_of_params])
        self.rowcount = self._pg_cur.rowcount
        return self

    def fetchone(self):
        row = self._pg_cur.fetchone()
        if row is None:
            return None
        return Row(self._col_names, row)

    def fetchall(self):
        rows = self._pg_cur.fetchall()
        return [Row(self._col_names, r) for r in rows]

    def fetchmany(self, size=1):
        rows = self._pg_cur.fetchmany(size)
        return [Row(self._col_names, r) for r in rows]

    def __iter__(self):
        for row in self._pg_cur:
            yield Row(self._col_names, row)

    def close(self):
        try:
            self._pg_cur.close()
        except Exception:
            pass


class Connection:
    def __init__(self, *args, **kwargs):
        self._pg_conn = _get_pg_connection()
        self.row_factory = None
        self._closed = False

    def cursor(self):
        return Cursor(self)

    def execute(self, sql, params=None):
        cur = Cursor(self)
        cur.execute(sql, params)
        return cur

    def commit(self):
        try:
            self._pg_conn.commit()
        except Exception:
            pass

    def rollback(self):
        try:
            self._pg_conn.rollback()
        except Exception:
            pass

    def close(self):
        if not self._closed:
            try:
                self._pg_conn.rollback()
            except Exception:
                pass
            _return_pg_connection(self._pg_conn)
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def connect(*args, **kwargs):
    return Connection(*args, **kwargs)


def Binary(data):
    return data


sqlite_version = 'postgres-shim-pooled'
version = 'postgres-shim-pooled'
PARSE_DECLTYPES = 1
PARSE_COLNAMES = 2
