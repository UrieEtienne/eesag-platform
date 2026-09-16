# Migration V26

1. Sauvegarder la base de données.
2. Depuis `backend/` : `python manage.py makemigrations churches core accounts`.
3. Puis : `python manage.py migrate`.
4. Créer/renseigner un profil développeur dans Django Admin.
5. Renseigner les fonctionnalités système.
6. Vérifier les droits par rôle avec des comptes de test distincts.

La migration ne doit pas être exécutée sur une base de production sans sauvegarde préalable.
