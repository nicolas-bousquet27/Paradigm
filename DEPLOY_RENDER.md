# Déploiement sur Render

Ce guide explique comment déployer l'application de pricing sur Render.

## Prérequis

1. Un compte Render (gratuit) : https://render.com
2. Les credentials Google Sheets (`credentials.json`)
3. L'URL de votre Google Sheet

## Étapes de déploiement

### 1. Préparer les credentials Google Sheets

Pour que Render puisse accéder à Google Sheets, vous devez :

1. Convertir votre fichier `credentials.json` en variable d'environnement
2. Sur Render, vous devrez créer une variable d'environnement `GOOGLE_APPLICATION_CREDENTIALS_JSON` avec tout le contenu de `credentials.json`

**Option 1 : Variable d'environnement (recommandé)**

Dans Render, créez une variable d'environnement `GOOGLE_APPLICATION_CREDENTIALS_JSON` contenant le JSON complet :

```json
{
  "type": "service_account",
  "project_id": "votre-project-id",
  "private_key_id": "...",
  "private_key": "...",
  ...
}
```

Puis modifiez `app/pricing/google_sheets.py` pour lire depuis cette variable d'environnement.

**Option 2 : Fichier de credentials (plus simple pour tester)**

Uploadez `credentials.json` directement dans votre repo (⚠️ **DANGER** : ne commitez JAMAIS ce fichier sur un repo public !).

### 2. Créer un nouveau Web Service sur Render

1. Connectez-vous à [Render](https://render.com)
2. Cliquez sur "New +" → "Web Service"
3. Connectez votre repository GitHub
4. Sélectionnez le repository `Paradigm`

### 3. Configuration du service

Utilisez les paramètres suivants :

| Paramètre | Valeur |
|-----------|--------|
| **Name** | `paradigm-pricing` (ou votre choix) |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn run:app` |
| **Plan** | Free (ou payant selon vos besoins) |

### 4. Variables d'environnement

Ajoutez les variables d'environnement suivantes dans Render :

| Clé | Valeur | Description |
|-----|--------|-------------|
| `SECRET_KEY` | (généré automatiquement par Render) | Clé secrète Flask |
| `FLASK_ENV` | `production` | Environnement Flask |
| `GOOGLE_SHEET_URL` | `https://docs.google.com/spreadsheets/d/...` | URL de votre Google Sheet |
| `GOOGLE_CREDENTIALS_FILE` | `credentials.json` | Nom du fichier de credentials |
| `PYTHON_VERSION` | `3.11.0` | Version de Python |

**Important :** Pour `GOOGLE_APPLICATION_CREDENTIALS_JSON`, copiez tout le contenu de votre fichier `credentials.json`.

### 5. Déploiement automatique

Render déploiera automatiquement votre application à chaque push sur la branche `main`.

Pour déployer une autre branche, changez la configuration dans Render :
- Allez dans "Settings" → "Build & Deploy"
- Changez "Branch" vers votre branche souhaitée

### 6. Accéder à l'application

Une fois déployé, Render vous donnera une URL comme :
```
https://paradigm-pricing.onrender.com
```

Vous pourrez accéder à votre application à cette adresse.

## Gestion du fichier credentials.json sur Render

### Méthode 1 : Variable d'environnement (RECOMMANDÉE)

Modifiez `app/pricing/google_sheets.py` pour créer le fichier credentials à partir d'une variable d'environnement :

```python
import json
import os

def get_credentials():
    """Récupère les credentials depuis la variable d'environnement ou le fichier"""
    creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')

    if creds_json:
        # Sur Render : créer le fichier depuis la variable d'environnement
        creds_dict = json.loads(creds_json)
        with open('credentials.json', 'w') as f:
            json.dump(creds_dict, f)
        return 'credentials.json'
    else:
        # En local : utiliser le fichier existant
        return os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
```

### Méthode 2 : Secrets dans Render

Render permet aussi de créer des fichiers secrets :
1. Allez dans "Environment" → "Secret Files"
2. Créez un nouveau fichier secret `credentials.json`
3. Collez le contenu de votre fichier

## Troubleshooting

### Erreur "Google Sheets API not enabled"

Assurez-vous que les APIs suivantes sont activées dans votre projet Google Cloud :
- Google Sheets API
- Google Drive API

### Erreur "Permission denied"

Vérifiez que le Google Sheet est bien partagé avec l'email du service account (visible dans `credentials.json`, champ `client_email`).

### L'application ne démarre pas

Vérifiez les logs dans Render :
1. Allez dans "Logs"
2. Cherchez les erreurs de démarrage
3. Vérifiez que toutes les dépendances sont installées

### Erreur "ModuleNotFoundError"

Si vous voyez des erreurs de modules manquants, vérifiez que `requirements.txt` contient toutes les dépendances nécessaires.

## Coût

- **Plan Free** : Gratuit, mais l'application peut s'endormir après 15 minutes d'inactivité
- **Plan Starter** : 7$/mois, toujours actif
- **Plans supérieurs** : Pour plus de performances

## Performance

Sur le plan Free, l'application peut prendre 30-60 secondes à démarrer si elle est endormie.
Pour une application toujours active, utilisez un plan payant.

## Support

Pour toute question sur le déploiement, consultez :
- Documentation Render : https://render.com/docs
- Documentation Flask : https://flask.palletsprojects.com/

## Sécurité

⚠️ **IMPORTANT** :
- Ne commitez JAMAIS `credentials.json` dans un repo public
- Ne commitez JAMAIS `.env` dans un repo public
- Utilisez les variables d'environnement de Render pour les secrets
- Changez la `SECRET_KEY` en production (Render le fait automatiquement)
