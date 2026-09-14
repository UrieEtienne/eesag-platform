# ECG CONNECT — Version professionnelle

## Gouvernance
- **Coordinateur** : compte racine de la plateforme. Il crée les comptes du Bureau national, sans rattachement à une église.
- **Bureau national** : comptes nationaux, contrôle transversal de toutes les églises, création des administrateurs/pasteurs locaux rattachés à une église.
- **Église locale** : espace privé et isolé pour ses membres, départements, annexes, finances, projets, documents et notifications.
- **Membre** : accès limité à son portail, son profil, notifications, documents/courriers autorisés et Bureau national.

## Comptabilité
Le module finance gère deux périmètres :
1. **Bureau national** : `eglise = NULL`.
2. **Église locale** : `eglise = ID de l'église`.

Le Bureau national peut sélectionner une église dans l'interface et consulter sa comptabilité. Un compte local est automatiquement limité à son église côté API et administration Django.

## Administration Django
Le dashboard admin inclut un centre financier et des liens directs vers :
- Journal comptable
- Projets & budgets
- Églises
- Administrateurs du Bureau / des églises

Le formulaire utilisateur est contextuel : le Coordinateur peut créer les comptes nationaux ; un membre du Bureau national peut créer les comptes rattachés à une église. Les comptes nationaux hors Coordinateur ne deviennent pas superutilisateurs.

## Frontend
Le frontend React utilise un layout commun : sidebar, barre supérieure, identité du périmètre, navigation nationale/locale et style cohérent. Le menu expose la comptabilité nationale au Bureau national et la comptabilité locale aux gestionnaires d'église.

## Vérification après installation
```bash
cd backend
source ../venv/bin/activate
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Puis :
```bash
cd ../frontend
npm install
npm run dev
```


## EESAG — évolution v13
- Paramètres du Coordinateur : couleur, mode clair/sombre, luminosité et taille de police.
- Photo de profil réelle dans les interfaces.
- Le Coordinateur reste invisible dans les listes génériques d'utilisateurs et peut modifier son compte depuis un accès dédié.
- Page Bureau national basée sur les mandats annuels, sans afficher le compte propriétaire.
- Rapports personnalisables par période et rubriques membres/finances/projets.
- Réunions et visioconférences avec périmètre national ou église.
