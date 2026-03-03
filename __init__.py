from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail()

def create_app():
    from config import Config
    
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Import routes here to avoid circular imports
    from routes import bp
    app.register_blueprint(bp)

    return app
