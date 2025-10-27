"""
Modèles de courbes de pricing (Nelson-Siegel, interpolation, ajustements)
Migré depuis l'application Streamlit
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.interpolate import interp1d


def nelson_siegel(maturity, beta0, beta1, beta2, tau):
    """
    Modèle Nelson-Siegel pour les courbes de taux

    Args:
        maturity: Maturité (Risk Mid)
        beta0, beta1, beta2, tau: Paramètres du modèle

    Returns:
        Valeur de la courbe à cette maturité
    """
    tau = max(tau, 0.1)  # Éviter division par zéro
    term1 = beta0
    term2 = beta1 * (1 - np.exp(-maturity/tau)) / (maturity/tau)
    term3 = beta2 * ((1 - np.exp(-maturity/tau)) / (maturity/tau) - np.exp(-maturity/tau))
    return term1 + term2 + term3


def fit_nelson_siegel(maturities, yields):
    """
    Ajuste les paramètres Nelson-Siegel sur des données observées
    Utilise seulement les points <= 7 ans pour l'ajustement

    Args:
        maturities: Array des maturités
        yields: Array des spreads observés

    Returns:
        Tuple (beta0, beta1, beta2, tau)
    """
    # Utiliser seulement les points <= 7 ans pour l'ajustement
    short_mask = maturities <= 7.0
    maturities_fit = maturities[short_mask]
    yields_fit = yields[short_mask]

    if len(maturities_fit) < 3:
        # Pas assez de points courts, utiliser tous
        maturities_fit = maturities
        yields_fit = yields

    def objective(params):
        beta0, beta1, beta2, tau = params
        predicted = nelson_siegel(maturities_fit, beta0, beta1, beta2, tau)
        return np.sum((yields_fit - predicted)**2)

    # Paramètres initiaux
    initial_beta0 = np.mean(yields_fit)
    initial_beta1 = yields_fit[0] - yields_fit[-1] if len(yields_fit) > 1 else 0
    initial_beta2 = 0
    initial_tau = 2.0

    # Contraintes sur les paramètres
    bounds = [
        (max(0, np.min(yields_fit) * 0.5), np.max(yields_fit) * 2),  # beta0
        (-np.max(yields_fit), np.max(yields_fit)),  # beta1
        (-np.max(yields_fit)/2, np.max(yields_fit)/2),  # beta2
        (0.5, 10.0)  # tau
    ]

    try:
        result = minimize(
            objective,
            [initial_beta0, initial_beta1, initial_beta2, initial_tau],
            bounds=bounds,
            method='L-BFGS-B'
        )

        if result.success:
            return result.x
        else:
            return [initial_beta0, initial_beta1, initial_beta2, initial_tau]
    except:
        return [initial_beta0, initial_beta1, initial_beta2, initial_tau]


def create_nelson_siegel_curve(maturities, yields, risk_grid=None):
    """
    Crée une courbe Nelson-Siegel avec extension linéaire après 7 ans

    Args:
        maturities: Array des maturités observées
        yields: Array des spreads observés
        risk_grid: Grille de points où calculer la courbe (défaut: 0-15 par 0.1)

    Returns:
        Tuple (risk_grid, curve_values, params)
    """
    if risk_grid is None:
        risk_grid = np.arange(0, 15.1, 0.1)

    # Ajuster Nelson-Siegel
    beta0, beta1, beta2, tau = fit_nelson_siegel(maturities, yields)

    # Partie Nelson-Siegel (0 à 7 ans)
    risk_short = risk_grid[risk_grid <= 7.0]
    curve_short = nelson_siegel(risk_short, beta0, beta1, beta2, tau)

    # Extension linéaire (7 à 15 ans)
    risk_long = risk_grid[risk_grid > 7.0]
    if len(risk_long) > 0:
        value_at_7 = nelson_siegel(7.0, beta0, beta1, beta2, tau)
        gentle_slope = min(2.0, max(0.5, value_at_7 * 0.01))  # Pente douce
        curve_long = value_at_7 + gentle_slope * (risk_long - 7.0)
    else:
        curve_long = np.array([])

    # Combiner
    curve = np.concatenate([curve_short, curve_long])
    return risk_grid, curve, (beta0, beta1, beta2, tau)


def remove_outliers_iqr(data, factor=1.5):
    """
    Supprime les outliers avec la méthode IQR

    Args:
        data: DataFrame avec colonne 'zspread'
        factor: Facteur multiplicatif pour IQR (défaut: 1.5)

    Returns:
        DataFrame nettoyé
    """
    Q1 = data['zspread'].quantile(0.25)
    Q3 = data['zspread'].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - factor * IQR
    upper = Q3 + factor * IQR
    return data[(data['zspread'] >= lower) & (data['zspread'] <= upper)]


def adjust_curve_to_market_points(curve_shape, curve_risk_grid, market_points_risk, market_points_spread):
    """
    Ajuste une courbe pour passer au milieu des points de marché
    (Utilisé pour la courbe rouge)

    Args:
        curve_shape: Courbe de référence (array)
        curve_risk_grid: Grille de risque de la courbe de référence
        market_points_risk: Maturités des points de marché
        market_points_spread: Spreads des points de marché

    Returns:
        Courbe ajustée (array)
    """
    if len(market_points_risk) == 0:
        return curve_shape

    # Interpoler la courbe de référence aux points de marché
    curve_values_at_market = np.interp(market_points_risk, curve_risk_grid, curve_shape)

    if len(market_points_risk) == 1:
        # Un seul point : décalage vertical simple
        shift = market_points_spread[0] - curve_values_at_market[0]
        return curve_shape + shift

    elif len(market_points_risk) == 2:
        # Deux points : décalage moyen
        shifts = market_points_spread - curve_values_at_market
        avg_shift = np.mean(shifts)
        return curve_shape + avg_shift

    else:
        # Plusieurs points : ajustement par régression locale
        shifts = market_points_spread - curve_values_at_market

        # Supprimer les outliers dans les shifts
        Q1_shift = np.percentile(shifts, 25)
        Q3_shift = np.percentile(shifts, 75)
        IQR_shift = Q3_shift - Q1_shift

        if IQR_shift > 0:
            # Filtrer les shifts outliers
            mask = (shifts >= Q1_shift - 1.5*IQR_shift) & (shifts <= Q3_shift + 1.5*IQR_shift)
            if np.sum(mask) >= 2:
                avg_shift = np.mean(shifts[mask])
            else:
                avg_shift = np.mean(shifts)
        else:
            avg_shift = np.mean(shifts)

        return curve_shape + avg_shift


def calculate_adjustment_score(score_liquidite, score_equity, score_solidite):
    """
    Calcule l'ajustement total à partir des 3 scores

    Args:
        score_liquidite: Score de liquidité (1-5)
        score_equity: Score equity (1-5)
        score_solidite: Score de solidité (1-5)

    Returns:
        Pourcentage d'ajustement total (float)
    """
    adjustments = {1: -20, 2: -10, 3: 0, 4: 10, 5: 20}

    adjustment_liquidite = adjustments[score_liquidite]
    adjustment_equity = adjustments[score_equity]
    adjustment_solidite = adjustments[score_solidite]

    # Moyenne des ajustements
    total_adjustment_pct = (adjustment_liquidite + adjustment_equity + adjustment_solidite) / 3

    return total_adjustment_pct
