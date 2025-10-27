import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration de base de l'application"""

    # Clé secrète pour la sécurité (sessions, cookies, etc.)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-a-changer-en-production'

    # Configuration Google Sheets
    GOOGLE_CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE') or 'credentials.json'
    GOOGLE_SHEET_NAME = os.environ.get('GOOGLE_SHEET_NAME') or 'pricing-investment-fund'

    # Configuration Flask
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
