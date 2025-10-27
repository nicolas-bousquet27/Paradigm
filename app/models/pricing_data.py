from app.models.sheets import sheets_manager
import json
from datetime import datetime

class PricingData:
    """Modèle pour les données de pricing"""

    def __init__(self, id, user_id, name, parameters, results=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.parameters = parameters  # Dictionnaire des paramètres
        self.results = results  # Résultats du calcul
        self.created_at = created_at or datetime.now().isoformat()

    @staticmethod
    def get_by_user(user_id):
        """Récupérer tous les calculs d'un utilisateur"""
        records = sheets_manager.get_all_records('pricing_data')
        user_data = []

        for record in records:
            if record.get('user_id') == user_id:
                user_data.append(PricingData(
                    id=record['id'],
                    user_id=record['user_id'],
                    name=record['name'],
                    parameters=json.loads(record.get('parameters', '{}')),
                    results=json.loads(record.get('results', 'null')),
                    created_at=record['created_at']
                ))

        return user_data

    @staticmethod
    def get_by_id(pricing_id):
        """Récupérer un calcul par son ID"""
        row_num, data = sheets_manager.find_row('pricing_data', 'id', pricing_id)
        if data:
            return PricingData(
                id=data['id'],
                user_id=data['user_id'],
                name=data['name'],
                parameters=json.loads(data.get('parameters', '{}')),
                results=json.loads(data.get('results', 'null')),
                created_at=data['created_at']
            )
        return None

    def save(self):
        """Sauvegarder dans Google Sheets"""
        row_num, existing = sheets_manager.find_row('pricing_data', 'id', self.id)

        values = [
            self.id,
            self.user_id,
            self.name,
            json.dumps(self.parameters),
            json.dumps(self.results) if self.results else '',
            self.created_at
        ]

        if row_num:
            sheets_manager.update_row('pricing_data', row_num, values)
        else:
            sheet = sheets_manager.get_sheet('pricing_data')
            # Vérifier si c'est la première ligne (headers)
            if sheet.row_count == 0 or sheet.row_values(1) == []:
                sheet.append_row(['id', 'user_id', 'name', 'parameters', 'results', 'created_at'])
            sheets_manager.append_row('pricing_data', values)

    @staticmethod
    def create(user_id, name, parameters):
        """Créer un nouveau calcul de pricing"""
        import uuid

        pricing_id = str(uuid.uuid4())
        pricing = PricingData(
            id=pricing_id,
            user_id=user_id,
            name=name,
            parameters=parameters
        )
        pricing.save()
        return pricing
