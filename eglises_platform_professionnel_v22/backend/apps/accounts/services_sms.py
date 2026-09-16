import json
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger("sms")


def normaliser_telephone(telephone: str) -> str:
    """Normalise un numéro vers E.164.

    EESAG utilise principalement les numéros guinéens (+224).
    Les formats suivants sont acceptés pour la Guinée :
      +224626483701
      00224626483701
      224626483701
      626483701
      626 48 37 01 (espaces/ponctuation)
    Pour les autres pays, le numéro doit être déjà international.
    """
    raw = str(telephone or '').strip()
    if not raw:
        raise ValueError('Le numéro de téléphone est obligatoire.')

    # Conserver uniquement + au début et les chiffres.
    raw = re.sub(r'[\s().\-]', '', raw)

    if raw.startswith('00'):
        raw = '+' + raw[2:]

    if raw.startswith('+'):
        digits_only = re.sub(r'\D', '', raw[1:])
        candidate = '+' + digits_only
    else:
        digits_only = re.sub(r'\D', '', raw)
        # Numéro guinéen local : 9 chiffres, généralement 6xxxxxxxx.
        if len(digits_only) == 9 and digits_only.startswith('6'):
            candidate = '+224' + digits_only
        elif digits_only.startswith('224') and len(digits_only) == 12:
            candidate = '+' + digits_only
        else:
            raise ValueError(
                'Le numéro doit être au format international, par exemple +224626483701. '
                'Vous pouvez aussi saisir un numéro guinéen local de 9 chiffres, par exemple 626483701.'
            )

    if not re.fullmatch(r'\+[1-9]\d{7,14}', candidate):
        raise ValueError(
            'Numéro de téléphone invalide. Exemple attendu : +224626483701.'
        )

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


def _supabase_request(path: str, payload: dict) -> tuple[bool, dict, str]:
    """Appelle l'API Auth Supabase avec la clé publishable côté serveur."""
    base_url = str(getattr(settings, "SUPABASE_URL", "") or "").strip().rstrip("/")
    publishable_key = str(getattr(settings, "SUPABASE_PUBLISHABLE_KEY", "") or "").strip()

    if not base_url:
        return False, {}, (
            "SUPABASE_URL est vide. Ajoutez dans backend/.env l'URL de votre projet, "
            "par exemple https://xxxxxxxx.supabase.co."
        )

    if not publishable_key:
        return False, {}, (
            "SUPABASE_PUBLISHABLE_KEY est vide. Copiez la Publishable key depuis "
            "Supabase → Settings → API Keys et placez-la dans backend/.env."
        )

    if not base_url.startswith(("https://", "http://")):
        return False, {}, "SUPABASE_URL doit commencer par https:// ou http://."

    url = f"{base_url}/auth/v1/{path.lstrip('/')}"
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "apikey": publishable_key,
            "Authorization": f"Bearer {publishable_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw or "{}") if raw else {}
            return True, data, ""
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
        try:
            data = json.loads(raw or "{}")
        except json.JSONDecodeError:
            data = {"message": raw or str(exc)}
        error = data.get("msg") or data.get("message") or data.get("error_description") or str(exc)
        return False, data, error
    except (URLError, TimeoutError, OSError) as exc:
        return False, {}, f"Erreur réseau Supabase : {exc}"
    except json.JSONDecodeError as exc:
        return False, {}, f"Réponse Supabase invalide : {exc}"


def envoyer_otp_supabase(telephone: str, *, utilisateur=None, creer_utilisateur=True) -> dict:
    """Demande à Supabase Auth d'envoyer un OTP SMS."""
    try:
        to_number = normaliser_telephone(telephone)
    except ValueError as exc:
        _journaliser(str(telephone), "OTP Supabase", "OTP", "supabase", "ECHEC", erreur=str(exc), utilisateur=utilisateur)
        return {"ok": False, "provider": "supabase", "status": "ECHEC", "error": str(exc)}

    payload = {
        "phone": to_number,
        "create_user": bool(creer_utilisateur),
    }
    ok, data, error = _supabase_request("otp", payload)
    if ok:
        user_id = (data.get("user") or {}).get("id", "") if isinstance(data, dict) else ""
        _journaliser(
            to_number,
            "OTP de confirmation envoyé par Supabase Auth.",
            "OTP",
            "supabase",
            "ENVOYE",
            provider_sid=user_id,
            utilisateur=utilisateur,
        )
        return {
            "ok": True,
            "provider": "supabase",
            "status": "ENVOYE",
            "to": to_number,
            "supabase_user_id": user_id,
        }

    _journaliser(
        to_number,
        "OTP Supabase",
        "OTP",
        "supabase",
        "ECHEC",
        erreur=error,
        utilisateur=utilisateur,
    )
    return {"ok": False, "provider": "supabase", "status": "ECHEC", "to": to_number, "error": error}


def verifier_otp_supabase(telephone: str, code: str) -> dict:
    """Vérifie un OTP SMS Supabase."""
    try:
        to_number = normaliser_telephone(telephone)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

    otp = str(code or "").strip()
    if not re.fullmatch(r"\d{6}", otp):
        return {"ok": False, "error": "Le code doit contenir exactement 6 chiffres."}

    ok, data, error = _supabase_request(
        "verify",
        {"phone": to_number, "token": otp, "type": "sms"},
    )
    if not ok:
        return {"ok": False, "provider": "supabase", "error": error}

    return {
        "ok": True,
        "provider": "supabase",
        "session": data.get("session") if isinstance(data, dict) else None,
        "user": data.get("user") if isinstance(data, dict) else None,
    }


def envoyer_sms_detail(telephone: str, message: str, *, type_message="INFORMATION", utilisateur=None) -> dict:
    """
    Compatibilité avec les anciens appels.

    Avec EESAG, les SMS transactionnels passent désormais par Supabase Auth.
    Pour un OTP, utilisez envoyer_otp_supabase(). Les messages libres ne sont
    pas envoyés artificiellement : ils sont journalisés afin d'éviter de faire
    croire qu'un SMS a été livré alors qu'aucun fournisseur n'est configuré.
    """
    provider = str(getattr(settings, "SMS_PROVIDER", "supabase") or "supabase").lower().strip()
    if provider != "supabase":
        error = "EESAG utilise désormais Supabase Auth pour les OTP SMS. Configurez SMS_PROVIDER=supabase."
        _journaliser(str(telephone), message, type_message, provider, "ECHEC", erreur=error, utilisateur=utilisateur)
        return {"ok": False, "provider": provider, "status": "ECHEC", "error": error}

    if type_message == "OTP":
        return envoyer_otp_supabase(telephone, utilisateur=utilisateur)

    error = (
        "Supabase Auth gère l'OTP de téléphone, pas l'envoi de SMS transactionnels arbitraires. "
        "Le message d'information est enregistré dans EESAG."
    )
    _journaliser(str(telephone), message, type_message, "supabase", "NON_ENVOYE", erreur=error, utilisateur=utilisateur)
    return {"ok": False, "provider": "supabase", "status": "NON_ENVOYE", "error": error}


def envoyer_sms(telephone: str, message: str, *, type_message="INFORMATION", utilisateur=None) -> bool:
    return bool(envoyer_sms_detail(telephone, message, type_message=type_message, utilisateur=utilisateur)["ok"])


def notifier_nouvel_identifiant(utilisateur, code_secret_clair, code_otp=None, origine=None):
    """Déclenche l'OTP Supabase et conserve le message d'information dans EESAG."""
    origine = origine or (utilisateur.eglise.nom if utilisateur.eglise else "Bureau national EESAG")
    otp_result = envoyer_otp_supabase(utilisateur.telephone, utilisateur=utilisateur, creer_utilisateur=True)

    if not otp_result.get("ok"):
        return [otp_result]

    # Le secret n'est jamais envoyé par SMS. Il doit être remis par le créateur
    # selon la politique interne de l'organisation.
    _journaliser(
        utilisateur.telephone,
        f"Compte créé par {origine}. Identifiant {utilisateur.identifiant}.",
        "BIENVENUE",
        "supabase",
        "NON_ENVOYE",
        utilisateur=utilisateur,
    )
    return [otp_result]
