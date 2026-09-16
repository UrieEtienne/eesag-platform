# EESAG Platform v30 Pro

## Changements

### Création d'une église
Le Bureau national général peut créer une église et son premier administrateur local dans le même écran Django Admin ou depuis l'API/frontend.

Le compte reçoit automatiquement :
- un identifiant EESAG généré par la plateforme ;
- un code secret/mot de passe défini à la création ;
- un rattachement à l'église créée.

Le code secret n'est jamais stocké en clair dans la base. Il est affiché une seule fois dans la confirmation de création à l'agent qui vient de créer le compte.

### Activation
Une nouvelle église reste inactive tant que le Bureau national général ne l'a pas activée.
L'activation de l'église depuis Django Admin ouvre automatiquement les accès du premier administrateur local / pasteur rattaché à cette église.

### Permissions
- Coordinateur : contrôle global.
- Bureau national général : crée les églises, crée les comptes administrateurs locaux et active/désactive les églises et comptes autorisés.
- Bureau national spécialisé : espace de son propre bureau, sans administration des comptes d'église.
- Église locale : gestion limitée à sa propre église.

### Configuration système
Les fonctionnalités système, la monétisation, les annonces système et le profil développeur sont réservés au Coordinateur.

### SMS
Le mode SMS de test reste contrôlé par `SMS_ENABLED=False` tant que Twilio Trial n'est pas disponible pour tous les destinataires.

### Vérification
Les modules Python principaux ont été compilés avec `py_compile`/`compileall` pendant la préparation de cette archive.
