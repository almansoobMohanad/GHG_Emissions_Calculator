import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_SSL_DISABLED = os.getenv('DB_SSL_DISABLED', 'false').lower() == 'true'
    
    # App
    SECRET_KEY = os.getenv('SECRET_KEY')
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))
    
    @property
    def is_production(self):
        return self.ENVIRONMENT == 'production'
    
    @property
    def database_config(self):
        return {
            'host': self.DB_HOST,
            'user': self.DB_USER,
            'password': self.DB_PASSWORD,
            'database': self.DB_NAME,
            'port': self.DB_PORT,
            'ssl_disabled': self.DB_SSL_DISABLED
        }

config = Config()