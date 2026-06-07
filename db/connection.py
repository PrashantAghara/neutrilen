import os
from contextlib import contextmanager
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: pool.ThreadedConnectionPool | None = None


def _get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None or _pool.closed:
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=DATABASE_URL,
        )
    return _pool


@contextmanager
def get_db():
    connection_pool = _get_pool()
    conn = connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        connection_pool.putconn(conn)


def get_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)


def close_pool():
    global _pool
    if _pool and not _pool.closed:
        _pool.closeall()
        _pool = None
