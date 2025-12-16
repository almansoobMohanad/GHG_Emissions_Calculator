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

        # Try nested secrets first, then flat secrets, then env vars
        db_secrets = st.secrets.get("database", {})
        host = db_secrets.get("host") or st.secrets.get("DB_HOST") or os.getenv("DB_HOST")
        user = db_secrets.get("user") or st.secrets.get("DB_USER") or os.getenv("DB_USER")
        password = db_secrets.get("password") or st.secrets.get("DB_PASSWORD") or os.getenv("DB_PASSWORD")
        database = db_secrets.get("database") or st.secrets.get("DB_NAME") or os.getenv("DB_NAME")
        port = db_secrets.get("port") or st.secrets.get("DB_PORT") or os.getenv("DB_PORT", 3306)
        ssl_disabled = db_secrets.get("ssl_disabled") or st.secrets.get("DB_SSL_DISABLED") or os.getenv("DB_SSL_DISABLED", "true")

        if not all([host, user, password, database]):
            st.error("Database secrets missing. Set either [database] section or flat DB_* keys in Streamlit secrets.")
            raise KeyError("Missing DB secrets")

        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': int(port),
            'connect_timeout': 10,
            'autocommit': True,
            'pool_reset_session': True,
            'ssl_disabled': str(ssl_disabled).lower() in ("1","true","yes","on"),
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