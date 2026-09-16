# Configuration SMS EESAG — FastAPI + Twilio

EESAG utilise désormais un microservice **FastAPI Python** pour les SMS. Django reste le cœur métier et appelle l'API interne ; les secrets Twilio ne sont jamais envoyés à React/Flutter.

## 1. Django (`backend/.env`)

```env
SMS_PROVIDER=twilio
SMS_API_URL=http://127.0.0.1:8010
SMS_API_KEY=change-cette-cle-interne
SMS_REQUEST_TIMEOUT=20
```

## 2. FastAPI (`sms_api/.env`)

```env
SMS_API_KEY=change-cette-cle-interne
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_MESSAGING_SERVICE_SID=
TWILIO_FROM=EESAG
TWILIO_STATUS_CALLBACK=
HOST=127.0.0.1
PORT=8010
```

`SMS_API_KEY` doit être la même valeur dans les deux fichiers.

## 3. Démarrer l'API SMS

```bash
cd sms_api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 127.0.0.1 --port 8010 --reload
```

## 4. Tester

Dans un autre terminal, dans `backend` :

```bash
source ../venv/bin/activate
python manage.py diagnostiquersms
python manage.py tester_sms 626483701
```

## 5. Flux EESAG

Création du compte :

1. Django crée le compte inactif.
2. Django génère un OTP de 6 chiffres valable 10 minutes.
3. FastAPI appelle Twilio pour envoyer le code.
4. L'utilisateur confirme le code via l'API Django.
5. Le compte est activé.
6. Un SMS de bienvenue peut être envoyé avec le nom de l'église ou du Bureau national.

## 6. Important pour la Guinée

Twilio publie des exigences spécifiques à la Guinée : le Sender ID alphanumérique peut nécessiter un pré-enregistrement, et les règles diffèrent selon les opérateurs. Consultez les SMS Guidelines de Twilio avant le passage en production.
