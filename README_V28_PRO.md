# EESAG v28 Pro – gouvernance, périmètres et administration

Cette version sépare les espaces EESAG selon le rôle connecté.

## Règles principales

- Coordinateur : contrôle global du système, fonctionnalités globales, monétisation, annonces et informations développeur.
- Bureau national général : administration Django de niveau national, gestion des églises et activation/désactivation de leur accès à la plateforme. Il ne gère pas directement les membres des églises.
- Bureau national spécialisé : administration limitée à son bureau/composition et à ses fonctions propres ; pas d’administration des membres ou départements d’une église.
- Église locale : administration privée de son église, avec membres, départements, annexes, administrateurs/droits et fonctions locales disponibles.

## Activation d’une église

Une nouvelle église est créée avec `plateforme_active=False`. L’activation ne passe plus par l’interface React et l’API ne permet plus l’activation. Elle se fait uniquement dans Django Admin par le Bureau national général.

Lors de l’activation, les comptes `ADMIN_LOCAL` et `PASTEUR` de l’église reçoivent l’accès Django Admin. Lors de la désactivation, leur accès Django Admin est retiré.

## Fonctionnalités désactivées

`FonctionnaliteSysteme.actif_global=False` est un verrou propriétaire. Un autre rôle reçoit un HTTP 403 s’il tente de la réactiver. Côté React, une option globalement désactivée est rendue inactive et non cliquable ; une URL directe affiche l’état verrouillé.

## Équipe

L’entrée « Équipe » est placée en bas de la barre latérale et reste visible à tous les utilisateurs authentifiés.

## Migration après extraction

```bash
cd backend
source ../venv/bin/activate
python manage.py makemigrations accounts churches core
python manage.py migrate
python manage.py check
```

Pour un projet dont la base existante a déjà été initialisée avant ces changements, vérifiez les migrations proposées avant de les appliquer.


## Base existante : synchroniser les accès Django Admin

Après déploiement sur une base déjà utilisée, exécutez :

```bash
cd backend
source ../venv/bin/activate
python manage.py synchroniser_acces_admin
```

Cette commande garantit :
- Coordinateur et comptes nationaux : accès Django Admin ;
- `ADMIN_LOCAL` / `PASTEUR` : accès Django Admin uniquement si leur église est activée et leur compte actif ;
- membres : aucun accès Django Admin.
