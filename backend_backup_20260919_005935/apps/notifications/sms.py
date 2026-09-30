import os
import re

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


def normaliser_numero_guinee(numero):
    if not numero:
        raise ValueError("Le numéro de téléphone est obligatoire.")

    numero = re.sub(r"[\s\-\(\)]", "", numero)

    if numero.startswith("+224"):
        pass
    elif numero.startswith("00224"):
        numero = "+224" + numero[5:]
    elif numero.startswith("224"):
        numero = "+" + numero
    elif numero.startswith("6") and len(numero) == 9:
        numero = "+224" + numero
    else:
        raise ValueError(
            "Numéro guinéen invalide. Exemple : +224621234567"
        )

    if not re.fullmatch(r"\+224\d{9}", numero):
        raise ValueError(f"Numéro guinéen invalide : {numero}")

    return numero


def envoyer_sms(telephone, message):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not account_sid:
        raise RuntimeError(
            "TWILIO_ACCOUNT_SID n'est pas configuré."
        )

    if not auth_token:
        raise RuntimeError(
            "TWILIO_AUTH_TOKEN n'est pas configuré."
        )

    if not messaging_service_sid and not from_number:
        raise RuntimeError(
            "Configurez TWILIO_MESSAGING_SERVICE_SID "
            "ou TWILIO_FROM_NUMBER."
        )

    telephone = normaliser_numero_guinee(telephone)

    client = Client(account_sid, auth_token)

    try:
        params = {
            "body": message,
            "to": telephone,
        }

        if messaging_service_sid:
            params["messaging_service_sid"] = messaging_service_sid
        else:
            params["from_"] = from_number

        sms = client.messages.create(**params)

        return sms.sid

    except TwilioRestException as exc:
        raise RuntimeError(
            f"Erreur Twilio : {exc.msg}"
        ) from exc
