# EESAG — Réactivation des fonctionnalités

Cette version corrige le verrouillage des fonctionnalités.

## Corrections
- /systeme/fonctionnalites/ est désormais consultable par tout utilisateur authentifié afin que les routes puissent connaître l'état réel.
- Seul le Coordinateur peut modifier l'état global.
- Une fonctionnalité désactivée peut maintenant être réactivée avec le bouton **Activer**.
- Ajout du bouton **Réactiver toutes** dans **Centre de gestion → Mes fonctionnalités**.
- **Réactiver toutes** remet toutes les fonctionnalités globales à actif=True et réactive les éventuels verrouillages locaux.
- Une panne temporaire de l'API des fonctionnalités ne verrouille plus toute l'application côté frontend.

## Pour remettre immédiatement tout en service
1. Connectez-vous avec le compte Coordinateur.
2. Ouvrez **Mes fonctionnalités**.
3. Cliquez sur **Réactiver toutes**.
4. Rechargez les autres comptes/structures.

Après cette action, les fonctionnalités sont accessibles pour toutes les structures tant qu'elles ne sont pas à nouveau désactivées par le Coordinateur.

## Vérification backend
bash
cd ~/Documents/Eglise\ AD/eglises_platform/backend
source venv/bin/activate
python manage.py check
python manage.py runserver


## Vérification frontend
bash
cd ~/Documents/Eglise\ AD/eglises_platform/frontend
npm install
npm run dev

