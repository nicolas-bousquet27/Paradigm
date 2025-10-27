"""
Gestion de la connexion et chargement des données depuis Google Sheets
Migré depuis l'application Streamlit
"""

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os


class GoogleSheetsLoader:
    """Gestionnaire de connexion Google Sheets pour les données de pricing"""

    def __init__(self, credentials_file=None, sheet_url=None):
        """
        Initialise le loader Google Sheets

        Args:
            credentials_file: Chemin vers credentials.json (défaut: depuis config)
            sheet_url: URL du Google Sheet (défaut: depuis config ou .env)
        """
        self.credentials_file = credentials_file or os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.sheet_url = sheet_url or os.getenv(
            'GOOGLE_SHEET_URL',
            'https://docs.google.com/spreadsheets/d/1hT8v9JOP1jSR8JhsYWBUIoiRS13kn4BdJ8wORFIzoqk/edit?usp=sharing'
        )
        self.gc = None

    def connect(self):
        """Établit la connexion avec Google Sheets"""
        try:
            # Définir les scopes nécessaires
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # Charger les credentials
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )

            # Autoriser gspread
            self.gc = gspread.authorize(creds)

            return True

        except Exception as e:
            print(f"Erreur connexion Google Sheets: {e}")
            return False

    def load_pricing_data(self):
        """
        Charge les données de pricing depuis Google Sheets

        Returns:
            Tuple (df_all, df_gr, df_merged)
            - df_all: DataFrame Data_All (tous les points de marché)
            - df_gr: DataFrame Data_GR (ratings des émetteurs)
            - df_merged: DataFrame fusionné (all + ratings)
        """
        try:
            if self.gc is None:
                if not self.connect():
                    raise Exception("Impossible de se connecter à Google Sheets")

            # Ouvrir le spreadsheet
            sh = self.gc.open_by_url(self.sheet_url)

            # Lire Data_All (premier onglet)
            worksheet_all = sh.get_worksheet(0)
            data_all_raw = worksheet_all.get_all_records()
            df_all = pd.DataFrame(data_all_raw)

            # Lire Data_GR (deuxième onglet)
            worksheet_gr = sh.get_worksheet(1)
            data_gr_raw = worksheet_gr.get_all_records()
            df_gr = pd.DataFrame(data_gr_raw)

            # Convertir les colonnes numériques pour df_all
            numeric_cols_all = ['zspread', 'riskmid']
            for col in numeric_cols_all:
                if col in df_all.columns:
                    df_all[col] = pd.to_numeric(df_all[col], errors='coerce')

            # Convertir les colonnes numériques pour df_gr
            if 'Note' in df_gr.columns:
                df_gr['Note'] = pd.to_numeric(df_gr['Note'], errors='coerce')

            if 'LinReg' in df_gr.columns:
                df_gr['LinReg'] = pd.to_numeric(df_gr['LinReg'], errors='coerce')

            # Nettoyer les données
            df_all = df_all.dropna(subset=['zspread', 'riskmid', 'ticker_corp', 'payment_rank'])
            df_all = df_all[(df_all['zspread'] > 0) & (df_all['riskmid'] > 0)]

            # Joindre avec les ratings
            df_merged = df_all.merge(
                df_gr[['ticker_corp', 'Note', 'Rating']],
                on='ticker_corp',
                how='left'
            )

            return df_all, df_gr, df_merged

        except Exception as e:
            print(f"Erreur chargement données Google Sheets: {e}")
            # Retourner des DataFrames vides en cas d'erreur
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def get_available_issuers(self, df_all):
        """Retourne la liste des émetteurs disponibles"""
        return sorted(df_all['ticker_corp'].unique())

    def get_available_seniorities(self, df_all):
        """Retourne la liste des séniorités disponibles"""
        all_seniorities = ['SP', 'SLA', 'T2', 'AT1']
        available_seniorities = sorted(df_all['payment_rank'].unique())
        return [s for s in all_seniorities if s in available_seniorities]

    def get_issuer_data(self, df_all, issuer, seniority):
        """
        Retourne les données pour un émetteur et une séniorité donnés

        Args:
            df_all: DataFrame avec toutes les données
            issuer: Nom de l'émetteur
            seniority: Séniorité (SP, SLA, T2, AT1)

        Returns:
            DataFrame filtré
        """
        return df_all[
            (df_all['ticker_corp'] == issuer) &
            (df_all['payment_rank'] == seniority)
        ].copy()

    def get_seniority_data(self, df_merged, seniority):
        """
        Retourne toutes les données pour une séniorité donnée

        Args:
            df_merged: DataFrame fusionné (avec ratings)
            seniority: Séniorité (SP, SLA, T2, AT1)

        Returns:
            DataFrame filtré
        """
        return df_merged[
            df_merged['payment_rank'] == seniority
        ].dropna(subset=['Note']).copy()

    def get_issuer_rating(self, df_gr, issuer):
        """
        Retourne le rating d'un émetteur

        Args:
            df_gr: DataFrame des ratings
            issuer: Nom de l'émetteur

        Returns:
            Float (Note) ou None si non trouvé
        """
        if issuer in df_gr['ticker_corp'].values:
            return df_gr[df_gr['ticker_corp'] == issuer]['Note'].iloc[0]
        return None
