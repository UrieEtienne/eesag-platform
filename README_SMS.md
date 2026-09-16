# SMS EESAG

Le projet utilise **FastAPI + Twilio** pour les SMS transactionnels et OTP.

- Django : gestion des comptes, OTP en attente et validation
- FastAPI : API interne d'envoi SMS
- Twilio : livraison SMS
- React / Flutter : appellent seulement l'API Django

Les secrets Twilio sont dans `sms_api/.env` et doivent rester privés.
