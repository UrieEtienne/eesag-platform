# EESAG V30 — gouvernance et sécurité des périmètres

## 1. Hiérarchie

### Coordinateur du système
- propriétaire fonctionnel de la plateforme ;
- contrôle global des comptes, églises, permissions, modules et paramètres ;
- seul rôle qui peut créer/gérer les administrateurs du Bureau national ;
- aucun Bureau national ne peut modifier, supprimer, suspendre ou désactiver son compte.

### Bureau national
- contrôle national des utilisateurs sauf le Coordinateur ;
- crée une église ;
- crée et rattache son administrateur principal ;
- modifie une église ;
- suspend, active et supprime une église selon les règles métier ;
- peut gérer les administrateurs d'églises ;
- ne gère pas les membres, départements et annexes comme s'il était un administrateur local.

### Église locale
- périmètre strictement limité à son eglise_id ;
- membres ;
- départements ;
- annexes ;
- documents, notifications, finances selon permissions ;
- administration locale : création d'administrateurs locaux délégués ;
- choix des permissions fonctionnelles de chaque administrateur ;
- aucun accès au Coordinateur ni aux paramètres nationaux.

## 2. Permissions locales

Les permissions existantes PermissionEglise / DelegationEglise sont conservées.
Un compte ADMIN_LOCAL reçoit ses droits par délégation :

- membres
- départements
- annexes
- documents
- notifications
- finances
- rapports
- réunions
- courriers
- assistant IA

Le serveur doit vérifier ces permissions. Le frontend ne constitue jamais une frontière de sécurité.

## 3. Bureau interne

Le lien /bureaux est réservé aux rôles nationaux. Il ne doit pas apparaître dans la navigation locale.

## 4. Point important avant déploiement

Le pack contient le frontend V30 et la politique Python centrale. Pour une intégration backend complète, il faut appliquer cette politique aux ViewSets existants et ajouter une migration si DelegationEglise reçoit un champ de statut/principal.

Ne remplacez pas models.py ou views.py complet avec un fichier généré sans comparer vos versions actuelles : ces fichiers contiennent d'autres fonctionnalités EESAG (SMS/OTP, notifications, etc.).
