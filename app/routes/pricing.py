"""
Routes pour l'application de pricing
Migré depuis Streamlit vers Flask
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import numpy as np
import json

from app.pricing import (
    GoogleSheetsLoader,
    create_yellow_curve_rating_clustering,
    create_green_curve_tranche_clustering,
    create_blue_curve_fusion,
    adjust_curve_to_market_points,
    calculate_adjustment_score
)

bp = Blueprint('pricing', __name__, url_prefix='/pricing')


# === HELPER FUNCTIONS ===

def get_sheets_loader():
    """Initialise et retourne le loader Google Sheets"""
    loader = GoogleSheetsLoader()
    return loader


def serialize_curve(curve):
    """Convertit un numpy array en liste pour JSON"""
    if curve is None:
        return None
    return curve.tolist() if hasattr(curve, 'tolist') else list(curve)


# === ROUTES PRINCIPALES ===

@bp.route('/')
@login_required
def index():
    """Page d'accueil du module pricing - Navigation entre les 4 pages"""
    return render_template('pricing/index.html')


@bp.route('/construction', methods=['GET', 'POST'])
@login_required
def construction():
    """
    Page 1: Construction des courbes de pricing
    Équivalent de la page "Construction des courbes" de Streamlit
    """
    loader = get_sheets_loader()
    df_all, df_gr, df_merged = loader.load_pricing_data()

    if df_all.empty:
        flash("Impossible de charger les données depuis Google Sheets", "danger")
        return render_template('pricing/construction.html',
                             error="Impossible de charger les données")

    # Récupérer les paramètres depuis le formulaire ou les valeurs par défaut
    selected_issuer = request.args.get('issuer') or request.form.get('issuer')
    selected_seniority = request.args.get('seniority') or request.form.get('seniority', 'SP')

    # Scores d'ajustement
    score_liquidite = int(request.args.get('score_liquidite', 3))
    score_equity = int(request.args.get('score_equity', 3))
    score_solidite = int(request.args.get('score_solidite', 3))

    # Paramètres de clustering
    n_clusters_rating = int(request.args.get('n_clusters_rating', 5))
    n_clusters_spread = int(request.args.get('n_clusters_spread', 3))

    # Options d'affichage
    show_individual_curves = request.args.get('show_individual_curves') == 'true'

    # Listes disponibles
    available_issuers = loader.get_available_issuers(df_all)
    available_seniorities = loader.get_available_seniorities(df_all)

    # Sélectionner le premier émetteur par défaut si aucun n'est sélectionné
    if not selected_issuer and available_issuers:
        selected_issuer = available_issuers[0]

    # Calculer les courbes si un émetteur est sélectionné
    curves_data = None
    if selected_issuer and selected_seniority:
        curves_data = calculate_curves(
            df_all, df_gr, df_merged,
            selected_issuer, selected_seniority,
            n_clusters_rating, n_clusters_spread,
            score_liquidite, score_equity, score_solidite
        )

    return render_template('pricing/construction.html',
                         available_issuers=available_issuers,
                         available_seniorities=available_seniorities,
                         selected_issuer=selected_issuer,
                         selected_seniority=selected_seniority,
                         score_liquidite=score_liquidite,
                         score_equity=score_equity,
                         score_solidite=score_solidite,
                         n_clusters_rating=n_clusters_rating,
                         n_clusters_spread=n_clusters_spread,
                         show_individual_curves=show_individual_curves,
                         curves_data=curves_data)


@bp.route('/analyse', methods=['GET'])
@login_required
def analyse():
    """
    Page 2: Analyse comparative et cross-séniorité
    Équivalent de la page "Analyse" de Streamlit
    """
    loader = get_sheets_loader()
    df_all, df_gr, df_merged = loader.load_pricing_data()

    if df_all.empty:
        flash("Impossible de charger les données depuis Google Sheets", "danger")
        return render_template('pricing/analyse.html',
                             error="Impossible de charger les données")

    available_issuers = loader.get_available_issuers(df_all)
    available_seniorities = loader.get_available_seniorities(df_all)

    return render_template('pricing/analyse.html',
                         available_issuers=available_issuers,
                         available_seniorities=available_seniorities)


@bp.route('/clusters-rating', methods=['GET'])
@login_required
def clusters_rating():
    """
    Page 3: Visualisation des clusters de rating
    Équivalent de la page "Clusters Rating" de Streamlit
    """
    loader = get_sheets_loader()
    df_all, df_gr, df_merged = loader.load_pricing_data()

    if df_all.empty or df_gr.empty:
        flash("Impossible de charger les données depuis Google Sheets", "danger")
        return render_template('pricing/clusters_rating.html',
                             error="Impossible de charger les données")

    # Paramètres
    n_clusters = int(request.args.get('n_clusters', 10))
    selected_seniority = request.args.get('seniority', 'Tous')

    available_seniorities = ['Tous'] + loader.get_available_seniorities(df_all)

    return render_template('pricing/clusters_rating.html',
                         n_clusters=n_clusters,
                         selected_seniority=selected_seniority,
                         available_seniorities=available_seniorities)


@bp.route('/clusters-tranches', methods=['GET'])
@login_required
def clusters_tranches():
    """
    Page 4: Clustering par tranches de Risk Mid
    Équivalent de la page "Clusters Tranches" de Streamlit
    """
    loader = get_sheets_loader()
    df_all, df_gr, df_merged = loader.load_pricing_data()

    if df_all.empty:
        flash("Impossible de charger les données depuis Google Sheets", "danger")
        return render_template('pricing/clusters_tranches.html',
                             error="Impossible de charger les données")

    # Paramètres
    n_clusters_spread = int(request.args.get('n_clusters_spread', 3))
    selected_seniority = request.args.get('seniority', 'SP')

    available_seniorities = loader.get_available_seniorities(df_all)

    return render_template('pricing/clusters_tranches.html',
                         n_clusters_spread=n_clusters_spread,
                         selected_seniority=selected_seniority,
                         available_seniorities=available_seniorities)


# === API ENDPOINTS POUR AJAX ===

@bp.route('/api/calculate-curves', methods=['POST'])
@login_required
def api_calculate_curves():
    """API endpoint pour calculer les courbes (appelé via AJAX)"""
    try:
        data = request.get_json()

        loader = get_sheets_loader()
        df_all, df_gr, df_merged = loader.load_pricing_data()

        if df_all.empty:
            return jsonify({'error': 'Données non disponibles'}), 400

        selected_issuer = data.get('issuer')
        selected_seniority = data.get('seniority')
        n_clusters_rating = int(data.get('n_clusters_rating', 5))
        n_clusters_spread = int(data.get('n_clusters_spread', 3))
        score_liquidite = int(data.get('score_liquidite', 3))
        score_equity = int(data.get('score_equity', 3))
        score_solidite = int(data.get('score_solidite', 3))

        curves_data = calculate_curves(
            df_all, df_gr, df_merged,
            selected_issuer, selected_seniority,
            n_clusters_rating, n_clusters_spread,
            score_liquidite, score_equity, score_solidite
        )

        if curves_data is None:
            return jsonify({'error': 'Impossible de calculer les courbes'}), 400

        # Sérialiser les courbes pour JSON
        response = {
            'risk_grid': serialize_curve(curves_data['risk_grid']),
            'yellow_curve': serialize_curve(curves_data.get('yellow_curve')),
            'green_curve': serialize_curve(curves_data.get('green_curve')),
            'blue_curve': serialize_curve(curves_data.get('blue_curve')),
            'red_curve': serialize_curve(curves_data.get('red_curve')),
            'issuer_points': curves_data['issuer_points'].to_dict('records') if curves_data['issuer_points'] is not None else [],
            'adjustment_pct': curves_data['adjustment_pct'],
            'info': curves_data['info']
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# === HELPER FUNCTIONS POUR LES CALCULS ===

def calculate_curves(df_all, df_gr, df_merged, selected_issuer, selected_seniority,
                    n_clusters_rating, n_clusters_spread,
                    score_liquidite, score_equity, score_solidite):
    """
    Calcule toutes les courbes pour un émetteur donné

    Returns:
        Dict avec toutes les courbes et infos
    """
    try:
        # Grille commune
        common_risk_grid = np.arange(0, 15.1, 0.1)

        # Calculer l'ajustement total
        adjustment_pct = calculate_adjustment_score(score_liquidite, score_equity, score_solidite)

        # Données de l'émetteur
        issuer_data = df_all[
            (df_all['ticker_corp'] == selected_issuer) &
            (df_all['payment_rank'] == selected_seniority)
        ].copy()

        # Données de tous les émetteurs pour cette séniorité
        all_seniority_data = df_merged[
            df_merged['payment_rank'] == selected_seniority
        ].dropna(subset=['Note']).copy()

        if len(all_seniority_data) < 10:
            return None

        # Courbe JAUNE (clustering rating)
        yellow_curve, yellow_info = create_yellow_curve_rating_clustering(
            all_seniority_data,
            selected_issuer,
            n_clusters_rating,
            common_risk_grid
        )

        # Courbe VERTE (clustering tranches)
        green_curve, green_info, tranches_info = create_green_curve_tranche_clustering(
            all_seniority_data,
            issuer_data,
            selected_issuer,
            n_clusters_spread,
            common_risk_grid
        )

        # Courbe BLEUE (fusion + ajustements)
        blue_curve, blue_curve_base, blue_info = create_blue_curve_fusion(
            yellow_curve,
            green_curve,
            adjustment_pct
        )

        # Courbe ROUGE (marché ajustée)
        red_curve = None
        red_info = "Aucun point marché disponible"

        if len(issuer_data) > 0 and blue_curve_base is not None:
            red_curve = adjust_curve_to_market_points(
                blue_curve_base,
                common_risk_grid,
                issuer_data['riskmid'].values,
                issuer_data['zspread'].values
            )
            red_info = f"Forme bleue ajustée à {len(issuer_data)} points marché"

        return {
            'risk_grid': common_risk_grid,
            'yellow_curve': yellow_curve,
            'green_curve': green_curve,
            'blue_curve': blue_curve,
            'red_curve': red_curve,
            'issuer_points': issuer_data,
            'adjustment_pct': adjustment_pct,
            'info': {
                'yellow': yellow_info,
                'green': green_info,
                'blue': blue_info,
                'red': red_info,
                'tranches': tranches_info
            }
        }

    except Exception as e:
        print(f"Erreur calcul courbes: {e}")
        return None
