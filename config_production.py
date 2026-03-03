import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Use SQLite for free hosting (instead of SQL Server)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///citywok.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'c1tywok.reservation@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'qbbrkqpvrzuclzqt')
    MAIL_DEFAULT_SENDER = 'c1tywok.reservation@gmail.com'
    SUPPORT_EMAIL = 'c1tywok.reservation@gmail.com'
