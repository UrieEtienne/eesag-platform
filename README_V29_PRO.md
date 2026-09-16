# EESAG Platform v29 Pro

## Corrections majeures

- « Mes fonctionnalités » est exclusivement accessible au Coordinateur.
- L’API système refuse toute activation/désactivation globale par les autres rôles.
- L’église locale ne peut pas activer un compte en attente.
- Le Bureau national général et le Coordinateur disposent des actions d’activation/désactivation des comptes dans Django Admin.
- La liste Django Admin est filtrée selon le rôle et le périmètre.
- L’espace Équipe reste discret en bas de la sidebar.
- L’activation de la plateforme d’une église reste une opération Django Admin réservée au Bureau national général.
- Le module Courriers propose une fiche membre automatique, une prévisualisation enrichie et une validation avant envoi.

## Navigation et sécurité de périmètre

- Les fonctionnalités système sont exclusives au Coordinateur et l’API renvoie 403 aux autres rôles.
- L’état `actif` des comptes est modifiable uniquement par le Coordinateur ou le Bureau national général.
- Une action d’activation dédiée apparaît dans la liste des comptes en attente pour ces deux rôles.
- Le lien « Équipe » est discret et placé en bas de l’administration.
- Le module de recommandation enrichit automatiquement la fiche membre et les données de destination.
