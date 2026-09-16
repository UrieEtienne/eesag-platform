# EESAG - configuration SMS

## Développement
Pour tester sans fournisseur réel : `SMS_PROVIDER=console`. Les SMS sont alors écrits dans le terminal et dans le Journal SMS.

## Production / Twilio
Configurer dans `backend/.env` :

```env
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM=EESAG
# ou : TWILIO_MESSAGING_SERVICE_SID=VA...
```

Les numéros sont normalisés en format international, par exemple `+224...`. Le système journalise chaque tentative d'envoi dans l'administration Django sous **Accounts > Journal SMS**.

Commande de test :

```bash
python manage.py tester_sms +224XXXXXXXX
```

Pour un compte créé par une église ou le Bureau national, EESAG envoie :
1. un SMS court contenant le code OTP ;
2. un SMS court contenant l'identifiant et les informations d'accès.

Le compte reste inactif jusqu'à la confirmation du téléphone.
