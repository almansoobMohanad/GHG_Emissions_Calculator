"""
Database Manager with proper connection handling
"""
import mysql.connector
from mysql.connector import Error
import streamlit as st

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
        # Get database config from Streamlit secrets
        self.config = {
            'host': st.secrets["database"]["host"],
            'user': st.secrets["database"]["user"],
            'password': st.secrets["database"]["password"],
            'database': st.secrets["database"]["database"],
            'port': st.secrets["database"].get("port", 3306),
            # IMPORTANT: Connection settings to prevent timeouts
            'connect_timeout': 10,
            'autocommit': True,  # Important for avoiding hanging transactions
            'pool_reset_session': True,
        }
    
    def connect(self):
        """Establish database connection with error handling."""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.config)
                self.cursor = self.connection.cursor()
                return True
            return True
        except Error as e:
            st.error(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """Safely close database connection."""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.connection and self.connection.is_connected():
                self.connection.close()
                self.connection = None
        except Error as e:
            # Log but don't raise - we're cleaning up anyway
            print(f"Error during disconnect: {e}")
    
    def fetch_query(self, query, params=None):
        """Execute SELECT query and return all results."""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            st.error(f"Query error: {e}")
            return []
    
    def fetch_one(self, query, params=None):
        """Execute SELECT query and return one result."""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except Error as e:
            st.error(f"Query error: {e}")
            return None
    
    def execute_query(self, query, params=None):
        """Execute INSERT/UPDATE/DELETE query."""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
            
            self.cursor.execute(query, params or ())
            # Since autocommit=True, no need to call commit()
            return True
        except Error as e:
            st.error(f"Execute error: {e}")
            return False
    
    def __del__(self):
        """Cleanup on object destruction."""
        self.disconnect()