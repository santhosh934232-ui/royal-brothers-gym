"""
Royal Brothers Fitness Gym - Database Connection Helper
Provides a single function that all route files use to talk to MySQL.

Uses mysql-connector-python (the "mysqlconnector" package you installed).

Uses a connection pool instead of opening a brand-new TCP connection to
MySQL on every single call. Every request your frontend makes (e.g.
/api/auth/me on every page load) calls get_db_connection() at least
once; opening a fresh connection each time means re-doing the full
TCP handshake + MySQL auth negotiation on every request, which is the
main source of the "flash of logged-out state before the page catches
up" delay reported after the restructure. This didn't change during
the restructure -- it's the same pattern the project always used --
but it's the concrete fix for that reported slowness.

conn.close() on a pooled connection returns it to the pool instead of
actually closing it, so no other file needs to change: every existing
`cursor = conn.cursor(...)`, `conn.commit()`, `cursor.close()`,
`conn.close()` call site keeps working exactly as before.
"""

import mysql.connector
from mysql.connector import Error, pooling
from .config import Config

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="royal_brothers_pool",
            pool_size=5,
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT,
        )
    return _pool


def get_db_connection():
    """
    Returns a MySQL connection from the connection pool (creating the
    pool on first use). Each route function should call this, use it,
    and close it when done (see usage example below) -- closing simply
    returns the connection to the pool for reuse.

    Usage in a route file:
        from ..extensions import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
    """
    try:
        return _get_pool().get_connection()
    except Error as e:
        # Printed to your terminal so you can see connection issues
        # (wrong password, MySQL not running, database not created yet, etc.)
        print(f"[Database Connection Error] {e}")
        raise
