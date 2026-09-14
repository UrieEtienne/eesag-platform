# Plateforme Nationale de Gestion des Églises

Système complet de recensement et de gestion des églises (religion, région,
préfecture, district, commune), avec gestion des membres, des rôles
(coordinateur, super admin international/national, admin local, pasteur,
membre), des lettres de mission/recommandation en PDF A4, des notifications,
de la comptabilité par église et des statistiques nationales/locales.

- **Backend :** Python / Django / Django REST Framework (API)
- **Frontend web :** React (Vite)
- **Mobile / Desktop :** Flutter (non inclus dans cette première version —
  voir la section "Prochaines étapes" en bas de ce fichier)

---

## 1. Structure du projet

```
eglises_platform/
├── backend/          # API Django REST Framework
│   ├── apps/
│   │   ├── accounts/       # Utilisateurs, rôles, identifiants, SMS
│   │   ├── geo/            # Région > Préfecture > District > Commune
│   │   ├── churches/       # Religions, Églises, Départements
│   │   ├── members/        # Historique des affectations
│   │   ├── letters/        # Lettres de mission/recommandation (PDF A4)
│   │   ├── documents/      # Documents sécurisés envoyés/reçus par église
│   │   ├── notifications/  # Notifications + publications
│   │   ├── finance/        # Comptabilité (dîme, offrande, dons, projets)
│   │   └── dashboard/      # Statistiques nationales/locales
│   ├── config/             # Réglages Django (settings, urls)
│   ├── manage.py
│   └── requirements.txt
└── frontend/         # Application web React (Vite)
    └── src/
        ├── pages/          # Écrans (connexion, dashboard, églises, etc.)
        ├── components/     # Formulaires, mise en page
        ├── context/        # Authentification
        └── api/            # Client HTTP (axios)
```

---

## 2. Installation en local

### Prérequis
- Python 3.11+ et pip
- Node.js 18+ et npm
- (Optionnel en production) PostgreSQL

### 2.1 Backend Django

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env              # puis modifiez SECRET_KEY si besoin

python manage.py migrate
python manage.py bootstrap_demo   # crée un compte Coordinateur + données de démo
python manage.py runserver
```

Le compte créé par `bootstrap_demo` :
- **Identifiant :** `COORD-001`
- **Code secret :** `admin1234`

⚠️ Changez ce code secret dès la première connexion (menu profil → à ajouter
côté frontend, ou via l'endpoint `POST /api/auth/changer-code-secret/`).

L'API est disponible sur `http://127.0.0.1:8000/api/`
L'interface d'administration Django sur `http://127.0.0.1:8000/admin/`
(créez un superutilisateur avec `python manage.py createsuperuser` si vous
préférez gérer les données depuis l'admin plutôt que le compte de démo).

### 2.2 Frontend React

Dans un **second terminal** :

```bash
cd frontend
npm install
cp .env.example .env              # VITE_API_URL doit pointer vers votre backend
npm run dev
```

Ouvrez ensuite `http://localhost:5173` et connectez-vous avec `COORD-001` /
`admin1234`.

---

## 3. Rôles du système (rappel)

| Rôle                     | Pouvoirs |
|--------------------------|----------|
| Coordinateur             | Contrôle total de la plateforme |
| Super Admin International| Affecte les missionnaires |
| Super Admin National     | Crée/modifie/supprime les églises, affecte les pasteurs, crée les admins locaux, envoie les notifications |
| Admin Local              | Gère UNIQUEMENT son église : membres, départements, comptabilité, courriers |
| Pasteur                  | Gère les membres de son église, programme les lettres de recommandation |
| Membre                   | Consulte son église, le bureau national, ses notifications |

Toutes les règles d'accès sont appliquées **côté serveur** (permissions DRF
dans `apps/accounts/permissions.py`), pas seulement dans l'interface : un
utilisateur ne peut pas contourner les restrictions même en modifiant le code
du frontend.

---

## 4. Fonctionnalités déjà codées

- Recensement des églises par religion / région / préfecture / district / commune
- Liste complète + recherche + création + modification + suppression d'église
- Affectation d'un pasteur à une église (avec historique + notification automatique)
- Recherche d'un membre par identifiant ou nom
- Gestion des départements par église
- Tableau de bord national ET tableau de bord par église (graphiques : répartition hommes/femmes, enfants/jeunes/adultes, églises par région, top des églises par effectif)
- Comptabilité par église (dîme, offrande, dons, entrées/sorties) + projets, avec accès strictement limité à l'admin local concerné et au national
- Lettres de mission / recommandation générées en **PDF A4**, un seul exemplaire, avec un texte d'exemple que vous pouvez modifier avant de régénérer le PDF (`POST /api/courriers/<id>/regenerer_pdf/`)
- Notifications automatiques : nouvel enregistrement, nouvelle affectation, document reçu, nouveau courrier, nouvelle publication d'église
- Création nationale d'une église avec compte administrateur local dans une même opération
- Annuaire national des églises avec recherche ; les détails et membres internes restent cloisonnés par église
- Documents sécurisés : envoi vers une ou plusieurs églises, suivi de lecture et notifications automatiques
- Gestion des annexes/implantations propre à chaque église
- Abonnement d'un membre aux publications d'une autre église
- OTP SMS : Supabase Auth. La livraison réelle exige l’activation de Phone Auth et la configuration d’un fournisseur SMS dans Supabase. EESAG bloque l’activation du compte tant que l’OTP n’est pas vérifié.

---

## Configuration Supabase OTP SMS

1. Dans Supabase, ouvrez **Authentication → Providers → Phone** et activez Phone Auth.
2. Configurez un fournisseur SMS pris en charge dans Supabase (par exemple Vonage ou MessageBird).
3. Dans `backend/.env` :

```env
SMS_PROVIDER=supabase
SUPABASE_URL=https://VOTRE-PROJET.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_VOTRE_CLE
```

4. Vérifiez la configuration sans afficher de secret :

```bash
python manage.py diagnostiquersupabase
```

5. Testez l’OTP réel :

```bash
python manage.py tester_sms +224XXXXXXXX
```

Le backend ne peut pas, à lui seul, livrer un SMS : Supabase Auth orchestre l’OTP et le fournisseur SMS configuré dans Supabase effectue l’envoi.

## 5. Déploiement en ligne

### 5.1 Backend (exemple avec Render.com ou Railway.app)

1. Poussez le dossier `backend/` sur un dépôt Git (GitHub/GitLab).
2. Créez un nouveau service web sur Render/Railway, branché sur ce dépôt.
3. Renseignez les variables d'environnement (reprises de `.env.example`) :
   `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=votredomaine.com`,
   `DATABASE_URL` (fournie automatiquement si vous ajoutez une base
   PostgreSQL gérée par la plateforme), `CORS_ALLOWED_ORIGINS`.
4. Commande de build : `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
5. Commande de démarrage : `gunicorn config.wsgi` (déjà dans le `Procfile`).
6. Une fois déployé, créez le compte coordinateur :
   `python manage.py bootstrap_demo` (via le terminal/"shell" de la plateforme).

### 5.2 Frontend (exemple avec Vercel ou Netlify)

1. Poussez le dossier `frontend/` sur un dépôt Git.
2. Créez un nouveau projet sur Vercel/Netlify, branché sur ce dépôt.
3. Commande de build : `npm run build` — dossier de sortie : `dist`.
4. Variable d'environnement : `VITE_API_URL=https://votre-backend.onrender.com/api`
5. Déployez : votre plateforme est en ligne.

### 5.3 Nom de domaine / HTTPS
La plupart de ces hébergeurs fournissent un sous-domaine gratuit
(`*.onrender.com`, `*.vercel.app`) avec HTTPS automatique. Vous pouvez y
attacher votre propre nom de domaine ensuite depuis les réglages du projet.

---

## 6. Prochaines étapes (non incluses dans cette version)

- **Application mobile/desktop Flutter** : consommera la même API REST
  (`/api/...`). Structure de dossiers et écrans à définir dans une prochaine
  itération — dites-moi quand vous voulez que je la démarre.
- Connexion à un vrai fournisseur SMS (le point d'intégration est déjà prêt
  dans `apps/accounts/services_sms.py`).
- Export PDF/Excel des statistiques et listes de membres.
- Système de permissions plus fin par département si besoin.

---

## 7. Support

Tous les fichiers sont commentés en français. Le code suit une architecture
standard Django (apps séparées par domaine métier) + React (pages/composants)
pour rester facile à faire évoluer, y compris par un autre développeur.

## 8. Règle d'isolement des espaces

Chaque compte possède un rattachement `eglise`. Les données internes (membres, départements, annexes, projets, finances, documents reçus/envoyés et communications) sont filtrées côté API par cette église. Les rôles nationaux disposent d'une vue de coordination nationale ; le portail local ne doit jamais être utilisé pour consulter le contenu interne d'une autre église.

Le bureau national peut rechercher une église dans l'annuaire, lui adresser un document ou une notification, et effectuer les affectations pastorales. La création d'une église peut également créer immédiatement son compte `ADMIN_LOCAL`; l'identifiant est généré automatiquement et le mot de passe choisi lors de l'enregistrement est conservé uniquement sous forme de hash.

Après les modifications, régénérez les migrations dans votre environnement Django :

```bash
cd backend
source venv/bin/activate
python manage.py makemigrations
python manage.py migrate
python manage.py check
```

Puis, pour le frontend :

```bash
cd frontend
npm install
npm run build
npm run dev
```
# eglises_platform
# eglises_platform
