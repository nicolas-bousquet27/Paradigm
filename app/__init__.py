from flask import Flask
from flask_login import LoginManager
from config import Config

# Initialisation des extensions
login_manager = LoginManager()

def create_app(config_class=Config):
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialiser Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

    # Importer le user_loader
    from app.models.user import load_user
    login_manager.user_loader(load_user)

    # Importer et enregistrer les blueprints (routes)
    from app.routes import auth, main, pricing

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(pricing.bp)

    return app
