# EESAG — Flutter Mobile & Desktop

Ce dossier ajoute un client Flutter/Dart partageant la même API Django pour Android, iOS, Windows, Linux et macOS.

## Créer les runners natifs

Flutter n'était pas installé dans l'environnement de préparation de l'archive. Après installation de Flutter, exécuter depuis ce dossier :

```bash
flutter create --platforms=android,ios,windows,linux,macos .
flutter pub get
```

Pour le développement :

```bash
flutter run -d chrome
flutter run -d linux
flutter run -d windows
flutter run -d android
```

Pour pointer vers Django sur une autre machine :

```bash
flutter run --dart-define=API_URL=https://votre-domaine.tld/api
```

Le client comprend déjà : connexion JWT, restauration de session, notifications, déconnexion et mise à jour de la photo de profil via l'API Django.


### Sécurité des clés SMS
Ne mettez jamais `VONAGE_API_SECRET`, une clé secrète Supabase ou un token privé dans Flutter. L'application mobile appelle uniquement l'API Django; les secrets restent dans `backend/.env`. Vonage demande de conserver l'API secret de façon sécurisée et Supabase réserve les clés secret aux composants serveur.


### OTP
Le mobile doit demander/vérifier l'OTP via l'API Django EESAG. Aucune clé Vonage n'est embarquée dans l'application Flutter.
