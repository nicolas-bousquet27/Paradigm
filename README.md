# Pricing Investment Fund - Application Web

Application web pour le calcul de pricing de fonds d'investissement, avec gestion d'utilisateurs et persistance des données dans Google Sheets.

## Structure du Projet

```
.
├── app/
│   ├── __init__.py              # Initialisation de l'application Flask
│   ├── models/                  # Modèles de données
│   │   ├── __init__.py
│   │   ├── sheets.py           # Gestionnaire Google Sheets
│   │   ├── user.py             # Modèle utilisateur
│   │   └── pricing_data.py     # Modèle données de pricing
│   ├── routes/                  # Routes (endpoints) de l'application
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentification (login/register)
│   │   ├── main.py             # Pages principales
│   │   └── pricing.py          # Gestion du pricing
│   ├── templates/               # Templates HTML
│   │   ├── base.html           # Template de base
│   │   ├── auth/               # Pages d'authentification
│   │   ├── main/               # Pages principales
│   │   └── pricing/            # Pages de pricing
│   ├── static/                  # Fichiers statiques (CSS, JS)
│   │   ├── css/
│   │   └── js/
│   └── pricing/                 # Votre modèle de pricing
│       └── __init__.py
├── instance/                    # Données locales (créé automatiquement)
├── config.py                    # Configuration de l'application
├── requirements.txt             # Dépendances Python
├── run.py                       # Point d'entrée de l'application
├── .env                         # Variables d'environnement (à créer)
└── credentials.json             # Credentials Google (à créer)
```

## Installation

### 1. Prérequis

- Python 3.8 ou supérieur
- Un compte Google
- Un projet Google Cloud avec l'API Google Sheets activée

### 2. Cloner le projet

```bash
git clone <votre-repo>
cd Paradigm
```

### 3. Créer un environnement virtuel

```bash
python -m venv venv
```

Activer l'environnement virtuel :
- **Windows** : `venv\Scripts\activate`
- **Mac/Linux** : `source venv/bin/activate`

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 5. Configuration Google Sheets

#### Créer un projet Google Cloud

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créez un nouveau projet
3. Activez l'API Google Sheets :
   - Menu "APIs & Services" > "Enable APIs and Services"
   - Recherchez "Google Sheets API" et activez-la
   - Recherchez "Google Drive API" et activez-la

#### Créer des credentials

1. Dans Google Cloud Console, allez dans "APIs & Services" > "Credentials"
2. Cliquez sur "Create Credentials" > "Service Account"
3. Remplissez les informations et créez le compte de service
4. Cliquez sur le compte de service créé
5. Allez dans l'onglet "Keys"
6. Cliquez sur "Add Key" > "Create new key" > "JSON"
7. Téléchargez le fichier JSON et renommez-le `credentials.json`
8. Placez `credentials.json` à la racine du projet

#### Créer le Google Sheet

1. Créez un nouveau Google Sheet
2. Notez le nom du fichier (par exemple : "pricing-investment-fund")
3. Partagez le fichier avec l'email du service account (visible dans credentials.json, champ "client_email")
   - Donnez les droits d'édition

### 6. Configuration de l'application

Créez un fichier `.env` à la racine du projet :

```bash
cp .env.example .env
```

Éditez le fichier `.env` et modifiez les valeurs :

```
SECRET_KEY=votre-cle-secrete-aleatoire-tres-longue
FLASK_ENV=development
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEET_NAME=pricing-investment-fund
```

## Lancement de l'application

```bash
python run.py
```

L'application sera accessible sur : http://localhost:5000

## Utilisation

### 1. Créer un compte

- Rendez-vous sur http://localhost:5000
- Cliquez sur "S'inscrire"
- Créez votre compte

### 2. Se connecter

- Utilisez vos identifiants pour vous connecter

### 3. Créer un calcul de pricing

- Cliquez sur "Nouveau Calcul"
- Remplissez les paramètres
- Lancez le calcul

### 4. Voir vos résultats

- Allez dans "Mes Calculs"
- Cliquez sur un calcul pour voir les résultats

## Intégration de votre modèle de pricing

Votre modèle Streamlit existant doit être intégré dans `app/pricing/__init__.py`.

1. Copiez votre code de modèle dans ce fichier
2. Adaptez la fonction `run_pricing_model(parameters)` pour :
   - Recevoir les paramètres en entrée (dictionnaire)
   - Retourner les résultats (dictionnaire)

Exemple :

```python
def run_pricing_model(parameters):
    # Extraire les paramètres
    investment_amount = parameters['investment_amount']
    duration = parameters['duration']
    risk_level = parameters['risk_level']

    # Votre logique de calcul ici
    # ...

    # Retourner les résultats
    return {
        'estimated_return': 12.5,
        'risk_score': 7.2,
        'recommendation': 'Investissement recommandé',
        # Ajoutez d'autres résultats selon vos besoins
    }
```

3. Modifiez `app/routes/pricing.py` ligne 52 pour appeler votre fonction :

```python
from app.pricing import run_pricing_model
results = run_pricing_model(pricing.parameters)
```

## Personnalisation

### Ajouter des paramètres au modèle

1. Modifiez le formulaire dans `app/templates/pricing/new.html`
2. Ajoutez les champs dans la route `pricing.new()` dans `app/routes/pricing.py`

### Modifier l'affichage des résultats

Éditez `app/templates/pricing/view.html` pour afficher vos résultats personnalisés.

### Ajouter des graphiques

Vous pouvez utiliser des bibliothèques JavaScript comme Chart.js ou Plotly pour afficher des graphiques dans les templates.

## Déploiement

### Option 1 : Heroku

1. Créez un fichier `Procfile` :
```
web: gunicorn run:app
```

2. Déployez sur Heroku :
```bash
heroku create votre-app
git push heroku main
```

### Option 2 : VPS (Linux)

1. Installez nginx et gunicorn
2. Configurez nginx comme reverse proxy
3. Lancez l'application avec gunicorn :
```bash
gunicorn -w 4 -b 127.0.0.1:5000 run:app
```

## Sécurité

**IMPORTANT** : Avant de mettre en production :

1. Changez la `SECRET_KEY` dans `.env` (utilisez une clé aléatoire longue)
2. Passez `FLASK_ENV` à `production`
3. Ne commitez JAMAIS :
   - Le fichier `.env`
   - Le fichier `credentials.json`
   - Les fichiers dans `instance/`

## Dépannage

### Erreur de connexion à Google Sheets

- Vérifiez que `credentials.json` est bien à la racine
- Vérifiez que le Google Sheet est partagé avec le service account
- Vérifiez que les APIs Google Sheets et Drive sont activées

### Erreur au lancement

- Vérifiez que toutes les dépendances sont installées
- Vérifiez que l'environnement virtuel est activé
- Vérifiez que le fichier `.env` existe et est correctement configuré

## Support

Pour toute question ou problème, créez une issue sur GitHub.