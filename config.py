import os
from urllib.parse import quote_plus

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Use your server name
    SQL_SERVER = os.environ.get('SQL_SERVER', 'ERCERC-F5UPCR11')
    SQL_DATABASE = os.environ.get('SQL_DATABASE', 'CityWokDB')
    DRIVER = os.environ.get('ODBC_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    # FIXED: Use & instead of ; after driver parameter
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc://@{SQL_SERVER}/{SQL_DATABASE}?driver={quote_plus(DRIVER)}&trusted_connection=yes"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'c1tywok.reservation@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'qbbrkqpvrzuclzqt')
    MAIL_DEFAULT_SENDER = 'c1tywok.reservation@gmail.com'
    SUPPORT_EMAIL = 'c1tywok.reservation@gmail.com'
