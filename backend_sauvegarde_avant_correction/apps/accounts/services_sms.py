import logging
import re
import secrets
from datetime import timedelta

import httpx
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("sms")


def normaliser_telephone(telephone: str) -> str:
    raw = str(telephone or "").strip()
    if not raw:
        raise ValueError("Le numéro de téléphone est obligatoire.")
    raw = re.sub(r"[\s().-]", "", raw)
    if raw.startswith("00"):
        raw = "+" + raw[2:]
    if raw.startswith("+"):
        candidate = "+" + re.sub(r"\D", "", raw[1:])
    else:
        digits = re.sub(r"\D", "", raw)
        if len(digits) == 9 and digits.startswith("6"):
            candidate = "+224" + digits
        elif digits.startswith("224") and len(digits) == 12:
            candidate = "+" + digits
        else:
            raise ValueError(
                "Le numéro doit être au format international, par exemple +224626483701. "
                "Vous pouvez aussi saisir un numéro guinéen local de 9 chiffres, par exemple 626483701."
            )
    if not re.fullmatch(r"\+[1-9]\d{7,14}", candidate):
        raise ValueError("Numéro de téléphone invalide. Exemple attendu : +224626483701.")
    return candidate


def _journaliser(telephone, message, type_message, fournisseur, statut, provider_sid="", erreur="", utilisateur=None):
    try:
        from .models import JournalSMS
        JournalSMS.objects.create(
            utilisateur=utilisateur,
            telephone=telephone,
            type_message=type_message,
            fournisseur=fournisseur,
            statut=statut,
            message=message,
            provider_sid=provider_sid or "",
            erreur=erreur or "",
        )
    except Exception:
        logger.exception("Impossible d'enregistrer le journal SMS")


def _call_sms_api(path: str, payload: dict) -> dict:
    """Appelle FastAPI uniquement lorsque SMS_ENABLED=True."""
    # MODE TEST : aucun appel réseau, mais le parcours OTP reste réel.
    if not getattr(settings, "SMS_ENABLED", False):
        return {
            "ok": True,
            "provider": "test",
            "status": "SIMULE",
            "message_sid": "TEST-SMS-DESACTIVE",
            "test_mode": True,
        }

    base = str(getattr(settings, "SMS_API_URL", "") or "").strip().rstrip("/")
    api_key = str(getattr(settings, "SMS_API_KEY", "") or "").strip()
    timeout = getattr(settings, "SMS_REQUEST_TIMEOUT", 20)

    if not base:
        return {"ok": False, "provider": "twilio", "error": "SMS_API_URL est vide."}
    if not api_key:
        return {"ok": False, "provider": "twilio", "error": "SMS_API_KEY est vide."}

    url = f"{base}/v1/sms/{path.lstrip('/')}"

    try:
        response = httpx.post(
            url,
            json=payload,
            headers={"X-SMS-API-Key": api_key, "Accept": "application/json"},
            timeout=timeout,
        )
    except httpx.TimeoutException:
        return {"ok": False, "provider": "twilio", "error": f"L'API SMS a dépassé le délai de {timeout} secondes."}
    except httpx.RequestError as exc:
        return {"ok": False, "provider": "twilio", "error": f"API SMS FastAPI inaccessible : {exc}"}
    except Exception as exc:
        logger.exception("Erreur inattendue lors de l'appel FastAPI")
        return {"ok": False, "provider": "twilio", "error": f"Erreur API SMS : {exc}"}

    try:
        data = response.json()
    except ValueError:
        data = {"detail": response.text}

    if response.status_code >= 400:
        return {
            "ok": False,
            "provider": "twilio",
            "status_code": response.status_code,
            "error": data.get("detail") or data.get("error") or response.text,
        }

    return {"ok": True, "provider": "twilio", **data}


def _creer_verification(utilisateur, code: str):
    from .models import VerificationTelephone
    VerificationTelephone.objects.filter(utilisateur=utilisateur, utilise=False).update(utilise=True)
    return VerificationTelephone.objects.create(
        utilisateur=utilisateur,
        code=code,
        expire_le=timezone.now() + timedelta(minutes=10),
        utilise=False,
        tentatives=0,
    )


def generer_code_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def envoyer_otp(telephone: str, *, utilisateur=None, origine="EESAG", creer_utilisateur=False) -> dict:
    try:
        numero = normaliser_telephone(telephone)
    except ValueError as exc:
        erreur = str(exc)
        _journaliser(str(telephone), "OTP de confirmation", "OTP", "test" if not getattr(settings, "SMS_ENABLED", False) else "twilio", "ECHEC", erreur=erreur, utilisateur=utilisateur)
        return {"ok": False, "provider": "test" if not getattr(settings, "SMS_ENABLED", False) else "twilio", "error": erreur, "status": "ECHEC"}

    code = generer_code_otp()
    result = _call_sms_api("otp", {"phone": numero, "to": numero, "code": code, "origin": origine})

    if result.get("ok"):
        if utilisateur is not None:
            _creer_verification(utilisateur, code)

        provider_sid = result.get("message_sid") or result.get("sid") or ""
        statut = "SIMULE" if result.get("test_mode") else "ENVOYE"
        _journaliser(numero, f"OTP de confirmation · {origine}", "OTP", result.get("provider", "twilio"), statut, provider_sid=provider_sid, utilisateur=utilisateur)

        result.update({"to": numero, "status": statut, "message_sid": provider_sid})
        if result.get("test_mode"):
            # Exposé uniquement parce que SMS_ENABLED=False.
            result["test_code"] = code
        return result

    erreur = result.get("error", "Erreur lors de l'envoi du SMS.")
    _journaliser(numero, f"OTP de confirmation · {origine}", "OTP", "twilio", "ECHEC", erreur=erreur, utilisateur=utilisateur)
    result.update({"to": numero, "status": "ECHEC"})
    return result


def verifier_otp(telephone: str, code: str) -> dict:
    try:
        numero = normaliser_telephone(telephone)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    otp = str(code or "").strip()
    if not re.fullmatch(r"\d{6}", otp):
        return {"ok": False, "error": "Le code doit contenir exactement 6 chiffres."}

    from .models import VerificationTelephone
    verification = (
        VerificationTelephone.objects
        .filter(utilisateur__telephone=numero, utilise=False, expire_le__gt=timezone.now())
        .select_related("utilisateur")
        .order_by("-cree_le")
        .first()
    )

    if not verification or verification.tentatives >= 5:
        return {"ok": False, "error": "Aucun code de confirmation valide n'est disponible pour ce compte."}

    if verification.code != otp:
        verification.tentatives += 1
        verification.save(update_fields=["tentatives"])
        return {"ok": False, "error": "Code de confirmation incorrect ou expiré."}

    return {"ok": True, "verification": verification}


def envoyer_sms_detail(telephone: str, message: str, *, type_message="INFORMATION", utilisateur=None, origine="EESAG") -> dict:
    try:
        numero = normaliser_telephone(telephone)
    except ValueError as exc:
        erreur = str(exc)
        _journaliser(str(telephone), message, type_message, "test" if not getattr(settings, "SMS_ENABLED", False) else "twilio", "ECHEC", erreur=erreur, utilisateur=utilisateur)
        return {"ok": False, "provider": "test" if not getattr(settings, "SMS_ENABLED", False) else "twilio", "error": erreur, "status": "ECHEC"}

    result = _call_sms_api("information", {"phone": numero, "to": numero, "message": message, "origin": origine})
    statut = "SIMULE" if result.get("test_mode") else ("ENVOYE" if result.get("ok") else "ECHEC")
    provider_sid = result.get("message_sid") or result.get("sid") or ""
    _journaliser(numero, f"{origine} : {message}", type_message, result.get("provider", "twilio"), statut, provider_sid=provider_sid, erreur=result.get("error", ""), utilisateur=utilisateur)
    return {**result, "to": numero, "status": statut, "message_sid": provider_sid}


def envoyer_sms(telephone: str, message: str, *, type_message="INFORMATION", utilisateur=None, origine="EESAG") -> bool:
    return bool(envoyer_sms_detail(telephone, message, type_message=type_message, utilisateur=utilisateur, origine=origine).get("ok"))


def notifier_nouvel_identifiant(utilisateur, code_secret_clair, code_otp=None, origine=None):
    """Envoie uniquement l'OTP. Le message de bienvenue part après validation."""
    origine_finale = origine or (utilisateur.eglise.nom if utilisateur.eglise else "Bureau national EESAG")
    return [envoyer_otp(utilisateur.telephone, utilisateur=utilisateur, origine=origine_finale, creer_utilisateur=True)]


def diagnostic_sms() -> dict:
    return {
        "enabled": bool(getattr(settings, "SMS_ENABLED", False)),
        "provider": getattr(settings, "SMS_PROVIDER", "twilio"),
        "sms_api_url_present": bool(getattr(settings, "SMS_API_URL", "")),
        "sms_api_key_present": bool(getattr(settings, "SMS_API_KEY", "")),
    }
