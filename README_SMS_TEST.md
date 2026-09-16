# Mode test SMS EESAG

Pour continuer sans dépendre de Twilio, le projet utilise `SMS_ENABLED=False` dans `backend/.env`. Aucun appel réseau n'est effectué. Le serveur génère quand même un OTP aléatoire de 6 chiffres, l'enregistre pour 10 minutes, l'affiche uniquement dans la réponse du mode test et dans la page React, puis active le compte après validation. Le SMS de bienvenue est simulé.

Pour réactiver Twilio : `SMS_ENABLED=True`, puis démarrer FastAPI et configurer les credentials Twilio dans `sms_api/.env`.
