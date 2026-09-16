# EESAG SMS API

Service optionnel FastAPI + Twilio.

Développement EESAG : `SMS_ENABLED=False` côté Django, donc aucun SMS réel n'est requis pour les tests locaux.

Production : copier `.env.example` vers `.env`, renseigner les credentials Twilio, puis lancer :

```bash
python -m uvicorn sms_api.main:app --host 127.0.0.1 --port 8010
```

Django appelle :
- `POST /v1/sms/otp`
- `POST /v1/sms/information`

avec l'en-tête privé `X-SMS-API-Key`.
