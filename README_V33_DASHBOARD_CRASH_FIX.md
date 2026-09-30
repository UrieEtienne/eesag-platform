# EESAG V33 — Correction définitive du tableau de bord national

## Cause corrigée
Le composant frontend/src/pages/TableauDeBordNational. appelait useMemo() après des retours conditionnels (Chargement / Erreur).

Conséquence : au premier rendu, le hook n'était pas appelé ; au rendu suivant, il l'était. React détectait alors un changement dans l'ordre des hooks et la page entière tombait dans ErrorBoundary, avec le message :

> Cette page a rencontré une erreur

## Correction
- Suppression du useMemo() problématique.
- Le tableau activityData est maintenant calculé avec une opération JavaScript normale, sans hook.
- Accès défensifs avec stats?. pour les données facultatives.
- Le endpoint /api/stats/national/ corrigé en V32 est conservé.
- Le tableau de bord reste disponible pour le Coordinateur et le Bureau national général.

## Installation
Aucune migration Django n'est requise pour cette correction frontend.

bash
cd ~/Documents/Eglise\ AD/eglises_platform
unzip -o eglises_platform_professionnel_v33_dashboard_crash_fix.zip
cd frontend
npm install
npm run dev


Pour le backend :

bash
cd ~/Documents/Eglise\ AD/eglises_platform/backend
source venv/bin/activate
python manage.py check
python manage.py runserver

