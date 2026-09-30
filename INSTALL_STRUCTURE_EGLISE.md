# Installation de la structure locale des églises

Cette version corrige le cloisonnement des départements et des postes.

## 1. Sauvegarder la base

Avant toute modification du schéma, faites une copie de backend/db.sqlite3 si vous utilisez SQLite.

## 2. Installer les nouvelles colonnes

Dans le terminal :

bash
cd ~/Documents/Eglise\ AD/eglises_platform/backend
source venv/bin/activate
python manage.py installer_structure_eglises
python manage.py check


La commande est idempotente : vous pouvez la relancer sans recréer les colonnes déjà présentes.

## 3. Redémarrer Django

bash
python manage.py runserver


## 4. Redémarrer le frontend

Dans un second terminal :

bash
cd ~/Documents/Eglise\ AD/eglises_platform/frontend
npm install
npm run dev


## Règles mises en place

- Un ADMIN_LOCAL/PASTEUR ne voit que les départements de son église.
- Un département créé depuis une église est rattaché à cette église.
- Un poste est rattaché à l'église et peut être rattaché à un département.
- Un membre ne peut recevoir qu'un département et un poste appartenant à son église.
- Les anciennes lignes sans église sont conservées mais ne sont plus proposées dans les espaces locaux.
- L'option « Bureaux internes » est supprimée de l'espace d'une église.
- La route /bureaux reste réservée aux rôles nationaux.
- Les pages Membres, Départements et Annexes affichent maintenant une erreur explicite au lieu de planter si une API échoue.
