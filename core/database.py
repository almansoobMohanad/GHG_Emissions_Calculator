import mysql.connector
from mysql.connector import pooling, Error
import streamlit as st
from config.settings import config
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    _connection_pool = None
    
    def __init__(self):
        self.connection = None
        self._setup_pool()
    
    def _setup_pool(self):
        """Setup connection pool once"""
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
        """Get connection from pool"""
        try:
            if DatabaseManager._connection_pool:
                self.connection = DatabaseManager._connection_pool.get_connection()
                return True
            return False
        except Error as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Release connection back to pool"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query, params=None, return_id=False):
        """Execute INSERT/UPDATE/DELETE"""
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
        """Execute SELECT query"""
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
        """Execute SELECT and return one row"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            logger.error(f"Fetch error: {e}")
            return None