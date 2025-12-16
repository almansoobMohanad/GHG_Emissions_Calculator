"""Database access layer with connection pooling."""

from mysql.connector import pooling, Error
import streamlit as st
from config.settings import config
import logging
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

class DatabaseManager:
    _connection_pool = None
    _pool_lock = threading.Lock()

    def __init__(self):
        self._setup_pool()
        self._current_connection = None  # Thread-local would be better, but this works for Streamlit

    def _setup_pool(self):
        """Set up the connection pool (thread-safe singleton)."""
        if DatabaseManager._connection_pool is None:
            with DatabaseManager._pool_lock:
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
        """Check if pool is available (backward compatible)."""
        return DatabaseManager._connection_pool is not None

    def disconnect(self):
        """No-op for backward compatibility."""
        return

    def _get_connection(self):
        """Get a connection from the pool."""
        if DatabaseManager._connection_pool is None:
            logger.error("Connection pool not initialized")
            return None
        try:
            return DatabaseManager._connection_pool.get_connection()
        except Error as e:
            logger.error(f"Connection checkout failed: {e}")
            return None

    def execute_query(self, query, params=None, return_id=False):
        conn = self._get_connection()
        if not conn:
            return False
        
        cursor = None
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
            conn.close()  # Return to pool

    def fetch_query(self, query, params=None):
        conn = self._get_connection()
        if not conn:
            return []
        
        cursor = None
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
            conn.close()  # Return to pool

    def fetch_one(self, query, params=None):
        conn = self._get_connection()
        if not conn:
            return None
        
        cursor = None
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
            conn.close()  # Return to pool