from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Vérifier l'utilisateur
        user = User.get_by_email(email)

        if user and user.check_password(password):
            login_user(user)
            flash('Connexion réussie !', 'success')

            # Rediriger vers la page demandée ou la page d'accueil
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        # Validations
        if not email or not username or not password:
            flash('Tous les champs sont requis.', 'danger')
            return render_template('auth/register.html')

        if password != password_confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('auth/register.html')

        # Vérifier si l'utilisateur existe déjà
        if User.get_by_email(email):
            flash('Cet email est déjà utilisé.', 'danger')
            return render_template('auth/register.html')

        # Créer l'utilisateur
        user = User.create_user(email=email, username=username, password=password)
        flash('Compte créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous êtes déconnecté.', 'info')
    return redirect(url_for('auth.login'))
