# EESAG v27 — Correctif Sidebar

Correction principale : toutes les routes protégées du frontend sont maintenant rendues à l'intérieur de `Layout`, ce qui restaure la sidebar et ses options après connexion.

La connexion et l'inscription restent sans sidebar.

Les routes protégées utilisent le même Layout afin de conserver :
- le nom de la structure dans la barre supérieure ;
- la sidebar adaptée au rôle ;
- les notifications ;
- le profil ;
- la déconnexion ;
- les options propres au Coordinateur, Bureau national et église locale.

Le correctif est dans `frontend/src/App.jsx`.
