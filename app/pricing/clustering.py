"""
Algorithmes de clustering pour les courbes de pricing
Migré depuis l'application Streamlit
"""

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.preprocessing import StandardScaler
from .curves import create_nelson_siegel_curve, remove_outliers_iqr


def create_yellow_curve_rating_clustering(
    all_seniority_data,
    selected_issuer,
    n_clusters_rating,
    common_risk_grid
):
    """
    Crée la courbe JAUNE basée sur le clustering de rating (Ward)

    Args:
        all_seniority_data: DataFrame avec tous les émetteurs pour cette séniorité
        selected_issuer: Nom de l'émetteur sélectionné
        n_clusters_rating: Nombre de clusters de rating
        common_risk_grid: Grille de risque commune

    Returns:
        Tuple (yellow_curve, info_message)
    """
    yellow_curve = None
    yellow_curve_info = ""

    try:
        # Préparer les features pour clustering (seulement le rating)
        valid_issuers = all_seniority_data.dropna(subset=['Note'])

        if len(valid_issuers) >= n_clusters_rating:
            # Clustering Ward sur les ratings
            features = valid_issuers[['Note']].values
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)

            ward_clustering = AgglomerativeClustering(
                n_clusters=n_clusters_rating,
                linkage='ward'
            )

            cluster_labels = ward_clustering.fit_predict(features_scaled)
            valid_issuers = valid_issuers.copy()
            valid_issuers['cluster_rating'] = cluster_labels

            # Trouver le cluster de l'émetteur sélectionné
            issuer_cluster = None
            if selected_issuer in valid_issuers['ticker_corp'].values:
                issuer_cluster = valid_issuers[valid_issuers['ticker_corp'] == selected_issuer]['cluster_rating'].iloc[0]
            else:
                issuer_cluster = 0

            # Récupérer toutes les données du cluster (sans l'émetteur cible)
            cluster_issuers = valid_issuers[valid_issuers['cluster_rating'] == issuer_cluster]['ticker_corp'].tolist()
            cluster_data = all_seniority_data[
                (all_seniority_data['ticker_corp'].isin(cluster_issuers)) &
                (all_seniority_data['ticker_corp'] != selected_issuer)
            ].copy()

            if len(cluster_data) >= 4:
                # Nettoyer les outliers
                cluster_clean = remove_outliers_iqr(cluster_data)
                if len(cluster_clean) < 4:
                    cluster_clean = cluster_data

                # Créer la courbe Nelson-Siegel
                cluster_sorted = cluster_clean.sort_values('riskmid')
                _, yellow_curve, _ = create_nelson_siegel_curve(
                    cluster_sorted['riskmid'].values,
                    cluster_sorted['zspread'].values,
                    common_risk_grid
                )

                yellow_curve_info = f"Cluster {issuer_cluster} | {len(cluster_clean)} points"
            else:
                yellow_curve_info = f"Pas assez de points dans le cluster {issuer_cluster}"
        else:
            yellow_curve_info = "Pas assez d'émetteurs avec rating"

    except Exception as e:
        yellow_curve_info = f"Erreur: {str(e)}"

    return yellow_curve, yellow_curve_info


def create_green_curve_tranche_clustering(
    all_seniority_data,
    issuer_data,
    selected_issuer,
    n_clusters_spread,
    common_risk_grid
):
    """
    Crée la courbe VERTE basée sur le clustering par tranches de Risk Mid (K-means)

    Args:
        all_seniority_data: DataFrame avec tous les émetteurs pour cette séniorité
        issuer_data: DataFrame avec les données de l'émetteur sélectionné
        selected_issuer: Nom de l'émetteur sélectionné
        n_clusters_spread: Nombre de clusters de spread
        common_risk_grid: Grille de risque commune

    Returns:
        Tuple (green_curve, info_message, tranches_details)
    """
    green_curve = None
    green_curve_info = ""
    tranches_info = []

    try:
        # Tranches de Risk Mid (0-1, 1-3, 3-5, 5-7, 7-10, 10+)
        risk_tranches = [(0, 1), (1, 3), (3, 5), (5, 7), (7, 10), (10, 15)]

        courbes_par_tranche = []
        poids_par_tranche = []

        for i, (tranche_min, tranche_max) in enumerate(risk_tranches):
            # Points de l'émetteur dans cette tranche
            issuer_points_tranche = issuer_data[
                (issuer_data['riskmid'] >= tranche_min) &
                (issuer_data['riskmid'] < tranche_max)
            ]

            if len(issuer_points_tranche) > 0:
                # Tous les émetteurs ayant des points dans cette tranche (sans l'émetteur cible)
                tranche_data = all_seniority_data[
                    (all_seniority_data['riskmid'] >= tranche_min) &
                    (all_seniority_data['riskmid'] < tranche_max) &
                    (all_seniority_data['ticker_corp'] != selected_issuer)
                ].copy()

                if len(tranche_data) >= n_clusters_spread:
                    # Clustering Z-spread dans cette tranche
                    spread_features = tranche_data[['zspread']].values
                    kmeans_spread = KMeans(n_clusters=n_clusters_spread, random_state=42)
                    spread_cluster_labels = kmeans_spread.fit_predict(spread_features)
                    tranche_data['cluster_spread'] = spread_cluster_labels

                    # Trouver le cluster de spread de l'émetteur dans cette tranche
                    avg_issuer_spread_tranche = issuer_points_tranche['zspread'].mean()
                    issuer_spread_cluster_tranche = kmeans_spread.predict([[avg_issuer_spread_tranche]])[0]

                    # Récupérer les données du cluster final dans cette tranche
                    cluster_tranche_data = tranche_data[
                        tranche_data['cluster_spread'] == issuer_spread_cluster_tranche
                    ].copy()

                    if len(cluster_tranche_data) >= 3:
                        # Nettoyer les outliers
                        cluster_clean = remove_outliers_iqr(cluster_tranche_data)
                        if len(cluster_clean) < 3:
                            cluster_clean = cluster_tranche_data

                        # Créer courbe pour cette tranche
                        cluster_sorted = cluster_clean.sort_values('riskmid')

                        if len(cluster_sorted) >= 4:
                            _, courbe_tranche, _ = create_nelson_siegel_curve(
                                cluster_sorted['riskmid'].values,
                                cluster_sorted['zspread'].values,
                                common_risk_grid
                            )

                            courbes_par_tranche.append(courbe_tranche)
                            poids_par_tranche.append(len(issuer_points_tranche))

                            # Gestion du nom de la dernière tranche (10+)
                            if tranche_max == 15:
                                tranche_name = f"[{tranche_min}+)"
                            else:
                                tranche_name = f"[{tranche_min}-{tranche_max})"

                            tranches_info.append({
                                'name': tranche_name,
                                'points': len(issuer_points_tranche),
                                'cluster': issuer_spread_cluster_tranche
                            })

        # Calculer la moyenne pondérée des courbes
        if len(courbes_par_tranche) > 0:
            courbes_array = np.array(courbes_par_tranche)
            poids_array = np.array(poids_par_tranche)
            green_curve = np.average(courbes_array, axis=0, weights=poids_array)

            total_points = sum(poids_par_tranche)
            green_curve_info = f"{len(courbes_par_tranche)} tranches | {total_points} points total"
        else:
            green_curve_info = "Aucune tranche avec assez de points"

    except Exception as e:
        green_curve_info = f"Erreur: {str(e)}"

    return green_curve, green_curve_info, tranches_info


def create_blue_curve_fusion(yellow_curve, green_curve, adjustment_pct):
    """
    Crée la courbe BLEUE par fusion des courbes jaune et verte + ajustements

    Args:
        yellow_curve: Courbe jaune (array)
        green_curve: Courbe verte (array)
        adjustment_pct: Pourcentage d'ajustement total

    Returns:
        Tuple (blue_curve, blue_curve_base, info_message)
    """
    blue_curve = None
    blue_curve_base = None
    blue_curve_info = ""

    if yellow_curve is not None and green_curve is not None:
        # Moyenne point par point
        blue_curve_base = (yellow_curve + green_curve) / 2
        blue_curve_info = "Fusion courbes jaune + verte"
    elif yellow_curve is not None:
        # Seulement la jaune disponible
        blue_curve_base = yellow_curve.copy()
        blue_curve_info = "Seule courbe jaune disponible"
    elif green_curve is not None:
        # Seulement la verte disponible
        blue_curve_base = green_curve.copy()
        blue_curve_info = "Seule courbe verte disponible"
    else:
        blue_curve_info = "Aucune courbe de référence"

    # Appliquer les ajustements
    if blue_curve_base is not None:
        blue_curve = blue_curve_base * (1 + adjustment_pct / 100)

    return blue_curve, blue_curve_base, blue_curve_info
