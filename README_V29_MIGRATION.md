# Migration v29

Dans `backend` :

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Puis redémarrer Django et Vite.

Le flux SMS reste désactivé en développement conformément à la configuration v25.
