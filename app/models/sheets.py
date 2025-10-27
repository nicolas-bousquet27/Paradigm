import gspread
from google.oauth2.service_account import Credentials
from flask import current_app

class GoogleSheetsManager:
    """Gestionnaire pour interagir avec Google Sheets"""

    def __init__(self):
        self.client = None
        self.spreadsheet = None

    def connect(self):
        """Se connecter à Google Sheets"""
        if self.client is None:
            # Définir les scopes nécessaires
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # Charger les credentials
            creds = Credentials.from_service_account_file(
                current_app.config['GOOGLE_CREDENTIALS_FILE'],
                scopes=scopes
            )

            # Créer le client
            self.client = gspread.authorize(creds)

            # Ouvrir le spreadsheet
            self.spreadsheet = self.client.open(current_app.config['GOOGLE_SHEET_NAME'])

        return self.spreadsheet

    def get_sheet(self, sheet_name):
        """Récupérer une feuille spécifique"""
        if self.spreadsheet is None:
            self.connect()

        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            # Créer la feuille si elle n'existe pas
            return self.spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")

    def get_all_records(self, sheet_name):
        """Récupérer tous les enregistrements d'une feuille"""
        sheet = self.get_sheet(sheet_name)
        return sheet.get_all_records()

    def append_row(self, sheet_name, values):
        """Ajouter une ligne à une feuille"""
        sheet = self.get_sheet(sheet_name)
        return sheet.append_row(values)

    def update_row(self, sheet_name, row_number, values):
        """Mettre à jour une ligne"""
        sheet = self.get_sheet(sheet_name)
        for col_idx, value in enumerate(values, start=1):
            sheet.update_cell(row_number, col_idx, value)

    def find_row(self, sheet_name, column_name, value):
        """Trouver une ligne par valeur de colonne"""
        records = self.get_all_records(sheet_name)
        for idx, record in enumerate(records, start=2):  # start=2 car ligne 1 = headers
            if record.get(column_name) == value:
                return idx, record
        return None, None

# Instance globale
sheets_manager = GoogleSheetsManager()
