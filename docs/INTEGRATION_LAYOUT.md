# EESAG V32 — intégration du menu Église locale

Le problème visible sur la capture vient de Layout. : le lien « Bureaux internes » est encore affiché dans la sidebar.

## 1. Importer le menu

Dans frontend/src/components/Layout. :


import MenuEgliseLocale from "./MenuEgliseLocale";
import { useAuth } from "../context/AuthContext";


Dans le composant Layout, récupérer :


const { utilisateur, estNational } = useAuth();
const estEgliseLocale = Boolean(utilisateur?.eglise && !estNational);


## 2. Sidebar locale

Dans la zone <aside> / sidebar, lorsque estEgliseLocale est vrai, afficher :


{estEgliseLocale ? (
  <MenuEgliseLocale />
) : (
  /* ton menu national/existant */
)}


Le composant MenuEgliseLocale affiche exactement :

- Tableau de bord
- Membres
- Départements
- Annexes
- Documents
- Notifications
- Finances
- Rapports
- Réunions
- Administration de l'église — ADMIN_LOCAL uniquement

## 3. Supprimer le lien Bureaux internes du menu local

Ne mets surtout pas le lien /bureaux dans MenuEgliseLocale.

La route /bureaux reste protégée dans App. par :


roles: ["SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"]


Donc un utilisateur d'église ne doit ni voir ni pouvoir ouvrir le Bureau national/interne.

## 4. Importer le CSS

Ajouter dans main. ou le fichier CSS principal :


import "./styles/eglise-locale.css";


Si app.css est déjà importé depuis main., tu peux aussi copier le contenu de styles/eglise-locale.css à la fin de app.css.
