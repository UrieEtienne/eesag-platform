# EESAG v17 — gouvernance par périmètre

Cette version renforce l'isolation des espaces et la gestion par structure.

## Bureaux
- Les membres simples consultent uniquement l'annuaire public des bureaux nationaux.
- Un administrateur de bureau national ne voit et ne gère que le bureau qui lui est attribué.
- Un bureau local est limité à l'église concernée.
- La composition des bureaux est annuelle et inclut photo, nom, identifiant et poste.
- Le Bureau National générique est créé automatiquement au premier `post_migrate`.

## Courriers
- Lettre de recommandation : création, aperçu, personnalisation Word et envoi réservés au pasteur.
- Le pasteur de l'église destinataire réceptionne le courrier.
- Les marqueurs Word `{{NOM}}`, `{{PRENOM}}`, `{{NOM_COMPLET}}`, `{{IDENTIFIANT}}`, `{{TELEPHONE}}`, `{{FONCTION}}`, `{{EGLISE}}`, `{{CODE_EGLISE}}`, `{{EGLISE_DESTINATION}}`, `{{CODE_EGLISE_DESTINATION}}`, `{{DATE}}` peuvent être remplacés automatiquement.

## Finances et projets
Le périmètre est déterminé côté serveur :
- Coordinateur : global.
- Église : propre église.
- Bureau thématique : propre bureau.
- Bureau national général : socle national, sans église et sans bureau thématique.
Aucun sélecteur de changement de structure n'est utilisé dans le frontend.

## Rapports
Le frontend demande un aperçu avant export. Les rapports sont générés uniquement pour le périmètre de l'utilisateur.

## SMS / OTP
Le flux de confirmation téléphone reste basé sur Supabase Auth OTP côté backend. La livraison SMS exige la configuration du fournisseur SMS dans le projet Supabase.

## Vérification
La syntaxe Python du backend a été compilée avec succès dans l'environnement de préparation. Les dépendances Django et Node de l'environnement local utilisateur ne sont pas incluses dans l'archive.
