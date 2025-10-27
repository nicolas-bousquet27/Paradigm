from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.pricing_data import PricingData

bp = Blueprint('pricing', __name__, url_prefix='/pricing')

@bp.route('/')
@login_required
def list():
    """Liste des calculs de pricing"""
    pricing_data = PricingData.get_by_user(current_user.id)
    return render_template('pricing/list.html', pricing_data=pricing_data)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Créer un nouveau calcul de pricing"""
    if request.method == 'POST':
        name = request.form.get('name')

        # Récupérer les paramètres du formulaire
        # TODO: Adapter selon les paramètres de votre modèle
        parameters = {
            'investment_amount': float(request.form.get('investment_amount', 0)),
            'duration': int(request.form.get('duration', 0)),
            'risk_level': request.form.get('risk_level'),
            # Ajoutez ici les autres paramètres de votre modèle
        }

        # Créer l'enregistrement
        pricing = PricingData.create(
            user_id=current_user.id,
            name=name,
            parameters=parameters
        )

        flash('Calcul créé avec succès !', 'success')
        return redirect(url_for('pricing.calculate', pricing_id=pricing.id))

    return render_template('pricing/new.html')

@bp.route('/<pricing_id>/calculate', methods=['GET', 'POST'])
@login_required
def calculate(pricing_id):
    """Calculer le pricing"""
    pricing = PricingData.get_by_id(pricing_id)

    if not pricing or pricing.user_id != current_user.id:
        flash('Calcul non trouvé.', 'danger')
        return redirect(url_for('pricing.list'))

    if request.method == 'POST':
        # TODO: Appeler votre modèle de pricing ici
        # from app.pricing import run_pricing_model
        # results = run_pricing_model(pricing.parameters)

        # Exemple de résultat factice
        results = {
            'estimated_return': 12.5,
            'risk_score': 7.2,
            'recommendation': 'Investissement recommandé'
        }

        pricing.results = results
        pricing.save()

        flash('Calcul effectué avec succès !', 'success')
        return redirect(url_for('pricing.view', pricing_id=pricing.id))

    return render_template('pricing/calculate.html', pricing=pricing)

@bp.route('/<pricing_id>')
@login_required
def view(pricing_id):
    """Voir les résultats d'un calcul"""
    pricing = PricingData.get_by_id(pricing_id)

    if not pricing or pricing.user_id != current_user.id:
        flash('Calcul non trouvé.', 'danger')
        return redirect(url_for('pricing.list'))

    return render_template('pricing/view.html', pricing=pricing)

@bp.route('/<pricing_id>/delete', methods=['POST'])
@login_required
def delete(pricing_id):
    """Supprimer un calcul"""
    # TODO: Implémenter la suppression dans Google Sheets
    flash('Fonctionnalité de suppression à implémenter.', 'info')
    return redirect(url_for('pricing.list'))
