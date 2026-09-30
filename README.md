# EESAG V32 — Église locale

Correction frontend ciblée sur l'espace Église locale.

## Objectif

Un utilisateur rattaché à une église ne voit que son espace local. Le lien « Bureaux internes » est exclu du menu local.

Seul ADMIN_LOCAL voit Administration de l'église.

## Fichiers

- frontend/src/App.
- frontend/src/context/AuthContext.
- frontend/src/components/RouteProtegee.
- frontend/src/components/MenuEgliseLocale.
- frontend/src/config/optionsEgliseLocale.js
- frontend/src/styles/eglise-locale.css
- docs/INTEGRATION_LAYOUT.md

## Installation

Copier les fichiers dans le projet :

bash
cd ~/Documents/Eglise\ AD/eglises_platform


Puis importer MenuEgliseLocale dans Layout. et remplacer le menu de sidebar local conformément à docs/INTEGRATION_LAYOUT.md.

Ajouter le CSS :


import "./styles/eglise-locale.css";


Puis tester :

bash
cd frontend
npm run build
npm run dev


## Résultat

ADMIN_LOCAL : menu local + Administration de l'église.

PASTEUR : menu local sans Administration de l'église.

Bureau national : menu national, pas menu local.

Coordinateur : conserve ses espaces de contrôle global.
