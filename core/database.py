"""Database access layer with connection pooling.

Provides a lightweight wrapper around `mysql.connector` using a shared
connection pool. The pool is created once per-process and subsequent calls
to `connect()` borrow a connection which must be returned with `disconnect()`.
"""

import mysql.connector
from mysql.connector import pooling, Error
import streamlit as st
from config.settings import config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manage pooled connections and basic query helpers.

    Typical usage:
        db = DatabaseManager()
        if db.connect():
            try:
                rows = db.fetch_query("SELECT NOW()")
            finally:
                db.disconnect()
    """
    _connection_pool = None
    
    def __init__(self):
        self.connection = None
        self._setup_pool()
    
    def _setup_pool(self):
        """Initialize the shared MySQL connection pool if not created.

        Creates a pool named `ghg_pool` with a default size of 5 connections
        using configuration from `config.settings`.
        """
        if DatabaseManager._connection_pool is None:
            try:
                pool_config = config.database_config.copy()
                pool_config.update({
                    'pool_name': 'ghg_pool',
                    'pool_size': 5,
                    'pool_reset_session': True
                })
                DatabaseManager._connection_pool = pooling.MySQLConnectionPool(**pool_config)
                logger.info("✅ Database pool created")
            except Error as e:
                logger.error(f"❌ Pool creation failed: {e}")
                st.error("Database connection failed")
    
    def connect(self):
        """Borrow a connection from the pool.

        Returns:
            bool: True if a connection was successfully acquired.
        """
        try:
            if DatabaseManager._connection_pool:
                self.connection = DatabaseManager._connection_pool.get_connection()
                return True
            return False
        except Error as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Return the current connection back to the pool.

        Safe to call multiple times.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query, params=None, return_id=False):
        """Execute a data-modifying SQL statement.

        Args:
            query: SQL string with placeholders.
            params: Optional tuple of parameters to bind.
            return_id: When True, returns last inserted id (for INSERTs).

        Returns:
            bool|int: True on success, or lastrowid when `return_id=True`.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            
            if return_id:
                last_id = cursor.lastrowid
                cursor.close()
                return last_id
            
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Query error: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def fetch_query(self, query, params=None):
        """Execute a SELECT query and return all rows.

        Args:
            query: SQL SELECT string with placeholders.
            params: Optional tuple of parameters to bind.

        Returns:
            list[tuple]: List of rows. Empty list on error.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"Fetch error: {e}")
            return []
    
    def fetch_one(self, query, params=None):
        """Execute a SELECT query and return a single row.

        Args:
            query: SQL SELECT string with placeholders.
            params: Optional tuple of parameters to bind.

        Returns:
            tuple|None: First row or None if not found or on error.
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            logger.error(f"Fetch error: {e}")
            return None