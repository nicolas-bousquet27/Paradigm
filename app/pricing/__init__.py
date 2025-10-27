"""
Module de pricing - Modèles de courbes et clustering
Migré depuis l'application Streamlit
"""

from .curves import (
    nelson_siegel,
    fit_nelson_siegel,
    create_nelson_siegel_curve,
    remove_outliers_iqr,
    adjust_curve_to_market_points,
    calculate_adjustment_score
)

from .clustering import (
    create_yellow_curve_rating_clustering,
    create_green_curve_tranche_clustering,
    create_blue_curve_fusion
)

from .google_sheets import GoogleSheetsLoader

__all__ = [
    # Curves
    'nelson_siegel',
    'fit_nelson_siegel',
    'create_nelson_siegel_curve',
    'remove_outliers_iqr',
    'adjust_curve_to_market_points',
    'calculate_adjustment_score',

    # Clustering
    'create_yellow_curve_rating_clustering',
    'create_green_curve_tranche_clustering',
    'create_blue_curve_fusion',

    # Google Sheets
    'GoogleSheetsLoader'
]
