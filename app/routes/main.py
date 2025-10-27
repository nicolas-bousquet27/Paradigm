from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    """Page d'accueil"""
    return render_template('main/index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord"""
    return render_template('main/dashboard.html')
