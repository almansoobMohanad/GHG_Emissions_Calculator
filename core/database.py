"""Database access layer with connection pooling.

Provides a lightweight wrapper around `mysql.connector` using a shared
connection pool. The pool is created once per-process and subsequent calls
to `connect()` borrow a connection which must be returned with `disconnect()`.
"""

from mysql.connector import pooling, Error
import streamlit as st
from config.settings import config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    _connection_pool = None

    def __init__(self):
        self._setup_pool()

    def _setup_pool(self):
        if DatabaseManager._connection_pool is None:
            try:
                pool_config = config.database_config.copy()
                pool_config.update({
                    "pool_name": "ghg_pool",
                    "pool_size": 5,
                    "pool_reset_session": True,
                })
                DatabaseManager._connection_pool = pooling.MySQLConnectionPool(**pool_config)
                logger.info("✅ Database pool created")
            except Error as e:
                logger.error(f"❌ Pool creation failed: {e}")
                st.error("Database connection failed")

    def connect(self):
        return DatabaseManager._connection_pool is not None

    def disconnect(self):
        return

    def _get_connection(self):
        if DatabaseManager._connection_pool is None:
            logger.error("Connection pool not initialized")
            return None
        try:
            return DatabaseManager._connection_pool.get_connection()
        except Error as e:
            logger.error(f"Connection checkout failed: {e}")
            return None

    def execute_query(self, query, params=None, return_id=False):
        conn, cursor = self._get_connection(), None
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid if return_id else True
        except Error as e:
            logger.error(f"Query error: {e}")
            conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            conn.close()

    def fetch_query(self, query, params=None):
        conn, cursor = self._get_connection(), None
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Fetch error: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            conn.close()

    def fetch_one(self, query, params=None):
        conn, cursor = self._get_connection(), None
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Fetch error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            conn.close()