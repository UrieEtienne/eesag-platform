import os
import re
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


SMS_API_KEY = env("SMS_API_KEY")
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
TWILIO_MESSAGING_SERVICE_SID = env("TWILIO_MESSAGING_SERVICE_SID")
TWILIO_FROM = env("TWILIO_FROM", "EESAG")

app = FastAPI(title="EESAG SMS API", version="1.0.0")


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
    if len(value) == 9:
        return "+224" + value
    raise ValueError("Numéro de téléphone invalide.")


def check_api_key(x_sms_api_key: Optional[str]) -> None:
    if not SMS_API_KEY:
        raise HTTPException(status_code=500, detail="SMS_API_KEY n'est pas configurée.")
    if x_sms_api_key != SMS_API_KEY:
        raise HTTPException(status_code=401, detail="Clé API SMS invalide.")


def twilio_client() -> Client:
    if not TWILIO_ACCOUNT_SID:
        raise HTTPException(status_code=500, detail="TWILIO_ACCOUNT_SID n'est pas configuré.")
    if not TWILIO_AUTH_TOKEN:
        raise HTTPException(status_code=500, detail="TWILIO_AUTH_TOKEN n'est pas configuré.")
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_sms(to: str, body: str) -> str:
    client = twilio_client()
    kwargs = {"to": to, "body": body}
    if TWILIO_MESSAGING_SERVICE_SID:
        kwargs["messaging_service_sid"] = TWILIO_MESSAGING_SERVICE_SID
    else:
        if not TWILIO_FROM:
            raise HTTPException(status_code=500, detail="TWILIO_FROM n'est pas configuré.")
        kwargs["from_"] = TWILIO_FROM
    try:
        return client.messages.create(**kwargs).sid
    except TwilioRestException as exc:
        raise HTTPException(status_code=502, detail=f"Twilio a refusé l'envoi : {exc.msg}") from exc


@app.get("/health")
def health():
    return {"status": "ok", "provider": "twilio", "service": "EESAG SMS API"}


@app.post("/v1/sms/otp")
def send_otp(data: OTPRequest, x_sms_api_key: Optional[str] = Header(default=None, alias="X-SMS-API-Key")):
    check_api_key(x_sms_api_key)
    try:
        phone = normalize_phone(data.phone)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    body = f"EESAG - {data.origin}: votre code de confirmation est {data.code}. Il expire dans 10 minutes. Ne partagez jamais ce code."
    sid = send_sms(phone, body)
    return {"success": True, "type": "otp", "phone": phone, "message_sid": sid}


@app.post("/v1/sms/information")
def send_information(data: InformationRequest, x_sms_api_key: Optional[str] = Header(default=None, alias="X-SMS-API-Key")):
    check_api_key(x_sms_api_key)
    try:
        phone = normalize_phone(data.phone)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    sid = send_sms(phone, f"EESAG - {data.origin}: {data.message}")
    return {"success": True, "type": "information", "phone": phone, "message_sid": sid}
