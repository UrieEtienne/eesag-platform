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
