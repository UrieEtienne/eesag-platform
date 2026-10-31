import os
import re
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# Clé privée utilisée uniquement entre Django et FastAPI.
SMS_API_KEY = env("SMS_API_KEY")

# Identifiants du fournisseur eSMS Africa.
ESMS_API_KEY = env("ESMS_API_KEY")
ESMS_SENDER_ID = env("ESMS_SENDER_ID", "EESAG")
ESMS_API_URL = env(
    "ESMS_API_URL",
    "https://sms.esmsafrica.io/api/messages/send",
)
ESMS_TIMEOUT = float(env("ESMS_TIMEOUT", "20"))

app = FastAPI(title="EESAG SMS API", version="2.0.0")


class OTPRequest(BaseModel):
    phone: str = Field(..., min_length=9, max_length=30)
    code: str = Field(..., min_length=6, max_length=6)
    origin: str = Field(..., min_length=1, max_length=120)


class InformationRequest(BaseModel):
    phone: str = Field(..., min_length=9, max_length=30)
    message: str = Field(..., min_length=1, max_length=900)
    origin: str = Field(..., min_length=1, max_length=120)


def normalize_phone(phone: str) -> str:
    value = re.sub(r"[^\d+]", "", phone or "")

    if value.startswith("00"):
        value = "+" + value[2:]

    if value.startswith("224") and not value.startswith("+"):
        value = "+" + value

    if value.startswith("+224"):
        if len(value) != 13:
            raise ValueError("Numéro guinéen invalide.")
        return value

    if len(value) == 9 and value.isdigit():
        return "+224" + value

    raise ValueError("Numéro de téléphone invalide.")


def check_api_key(x_sms_api_key: Optional[str]) -> None:
    if not SMS_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="La clé interne SMS_API_KEY n'est pas configurée.",
        )
    if x_sms_api_key != SMS_API_KEY:
        raise HTTPException(status_code=401, detail="Clé API SMS invalide.")


def send_sms(to: str, body: str) -> str:
    if not ESMS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="La clé ESMS_API_KEY n'est pas configurée.",
        )

    if not ESMS_SENDER_ID:
        raise HTTPException(
            status_code=503,
            detail="L'identifiant expéditeur ESMS_SENDER_ID n'est pas configuré.",
        )

    try:
        response = httpx.post(
            ESMS_API_URL,
            headers={
                "Authorization": f"Bearer {ESMS_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "to": to,
                "text": body,
                "sender_id": ESMS_SENDER_ID,
            },
            timeout=ESMS_TIMEOUT,
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Le fournisseur SMS n'a pas répondu dans le délai prévu.",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Impossible de joindre le fournisseur SMS.",
        ) from exc

    try:
        result = response.json()
    except ValueError:
        result = {}

    if response.status_code >= 400:
        # Ne pas renvoyer de secrets ni le contenu complet de la requête.
        detail = (
            result.get("message")
            or result.get("error")
            or result.get("detail")
            or f"Le fournisseur SMS a répondu HTTP {response.status_code}."
        )
        raise HTTPException(status_code=502, detail=str(detail)[:500])

    # L'API peut renvoyer différents noms de référence selon sa réponse.
    reference = (
        result.get("message_id")
        or result.get("messageId")
        or result.get("message_sid")
        or result.get("reference")
        or result.get("id")
        or ""
    )

    return str(reference)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "provider": "esmsafrica",
        "service": "EESAG SMS API",
        "configured": bool(SMS_API_KEY and ESMS_API_KEY and ESMS_SENDER_ID),
    }


@app.post("/v1/sms/otp")
def send_otp(
    data: OTPRequest,
    x_sms_api_key: Optional[str] = Header(
        default=None,
        alias="X-SMS-API-Key",
    ),
):
    check_api_key(x_sms_api_key)

    try:
        phone = normalize_phone(data.phone)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    body = (
        f"EESAG - {data.origin}: votre code de confirmation est "
        f"{data.code}. Il expire dans 10 minutes. "
        "Ne partagez jamais ce code."
    )

    reference = send_sms(phone, body)

    return {
        "success": True,
        "type": "otp",
        "provider": "esmsafrica",
        "phone": phone,
        "message_sid": reference,
    }


@app.post("/v1/sms/information")
def send_information(
    data: InformationRequest,
    x_sms_api_key: Optional[str] = Header(
        default=None,
        alias="X-SMS-API-Key",
    ),
):
    check_api_key(x_sms_api_key)

    try:
        phone = normalize_phone(data.phone)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    reference = send_sms(
        phone,
        f"EESAG - {data.origin}: {data.message}",
    )

    return {
        "success": True,
        "type": "information",
        "provider": "esmsafrica",
        "phone": phone,
        "message_sid": reference,
    }
