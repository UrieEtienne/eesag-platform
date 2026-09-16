# EESAG Platform — v26 Pro

Version de travail orientée multi-périmètres : Coordinateur, Bureau national général, bureaux nationaux spécialisés, églises locales et membres.

## Changements principaux
- Isolation du Bureau national spécialisé : pas de gestion des membres/départements des églises.
- Gestion des membres limitée aux responsables d’église.
- Activation/désactivation de l’espace d’une église.
- Administrateurs locaux créés depuis le périmètre national autorisé.
- Fonctionnalités activables par périmètre avec verrouillage global du Coordinateur.
- Catalogue de mises à jour et annonces administrables par le Coordinateur.
- Page publique « Informations & développeurs » administrable.
- Administration Django restylée dans l’esprit AdminLTE de la référence fournie.
- Proxy Vite `/api` en développement pour éviter le mélange localhost/127.0.0.1.
- Tableau national défensif lorsque des champs statistiques sont absents.
- Mode SMS de développement conservé séparément du chemin Twilio.

## Migration
```bash
cd backend
source ../venv/bin/activate
python manage.py makemigrations churches core accounts
python manage.py migrate
python manage.py check
```

## Frontend
```bash
cd frontend
npm install
npm run build
npm run dev
```

## SMS
Développement : `SMS_ENABLED=False`.
Production : réactiver Twilio après configuration des restrictions et de la conformité du compte.
