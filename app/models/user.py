from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.sheets import sheets_manager

class User(UserMixin):
    """Modèle utilisateur"""

    def __init__(self, id, email, username, password_hash=None):
        self.id = id
        self.email = email
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        """Définir le mot de passe (hashé)"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifier le mot de passe"""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_id(user_id):
        """Récupérer un utilisateur par son ID"""
        row_num, user_data = sheets_manager.find_row('users', 'id', user_id)
        if user_data:
            return User(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                password_hash=user_data['password_hash']
            )
        return None

    @staticmethod
    def get_by_email(email):
        """Récupérer un utilisateur par son email"""
        row_num, user_data = sheets_manager.find_row('users', 'email', email)
        if user_data:
            return User(
                id=user_data['id'],
                email=user_data['email'],
                username=user_data['username'],
                password_hash=user_data['password_hash']
            )
        return None

    def save(self):
        """Sauvegarder l'utilisateur dans Google Sheets"""
        # Vérifier si l'utilisateur existe déjà
        row_num, existing_user = sheets_manager.find_row('users', 'id', self.id)

        values = [self.id, self.email, self.username, self.password_hash]

        if row_num:
            # Mettre à jour
            sheets_manager.update_row('users', row_num, values)
        else:
            # Créer
            sheet = sheets_manager.get_sheet('users')
            # Vérifier si c'est la première ligne (headers)
            if sheet.row_count == 0 or sheet.row_values(1) == []:
                sheet.append_row(['id', 'email', 'username', 'password_hash'])
            sheets_manager.append_row('users', values)

    @staticmethod
    def create_user(email, username, password):
        """Créer un nouvel utilisateur"""
        import uuid

        # Générer un ID unique
        user_id = str(uuid.uuid4())

        user = User(id=user_id, email=email, username=username)
        user.set_password(password)
        user.save()

        return user


def load_user(user_id):
    """Charger un utilisateur pour Flask-Login"""
    return User.get_by_id(user_id)
