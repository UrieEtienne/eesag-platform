"""Couche IA optionnelle.

L'application fonctionne sans fournisseur externe grâce à un mode local déterministe.
Lorsqu'une clé OPENAI_API_KEY est configurée, le service utilise la Responses API.
Aucune donnée n'est modifiée automatiquement par l'IA : elle propose et l'utilisateur
valide l'action métier.
"""

import json
import os
import urllib.error
import urllib.request


OPENAI_URL = "https://api.openai.com/v1/responses"


def _local_fallback(action: str, context: dict) -> str:
    if action == "BROUILLON":
        sujet = context.get("sujet") or "Information importante"
        return (
            f"Objet : {sujet}\n\nBonjour,\n\nNous vous informons que {context.get('message', 'une nouvelle information est disponible')}.\n"
            "Merci de consulter votre espace EESAG et de prendre les dispositions nécessaires.\n\nBureau / Administration"
        )
    if action == "MISE_A_JOUR":
        return (
            "Suggestions de mise à jour :\n"
            "1. Vérifier les membres sans téléphone ou sans département.\n"
            "2. Vérifier les comptes inactifs depuis longtemps.\n"
            "3. Contrôler les doublons potentiels sur téléphone et identifiant.\n"
            "4. Vérifier les responsables de département et les affectations arrivées à échéance.\n\n"
            "Aucune modification n'est appliquée automatiquement."
        )
    stats = context.get("stats", {})
    return (
        "Synthèse automatique :\n"
        f"- Églises actives : {stats.get('eglises_actives', 0)}\n"
        f"- Membres actifs : {stats.get('membres', 0)}\n"
        f"- Départements : {stats.get('departements', 0)}\n"
        f"- Notifications : {stats.get('notifications', 0)}\n\n"
        "Le résultat est une aide à la décision et doit être vérifié avant toute action."
    )


def _extract_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return payload["output_text"].strip()
    chunks = []
    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def generer_assistance(action: str, context: dict) -> tuple[str, str, bool]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    if not api_key:
        return _local_fallback(action, context), "local", True

    instructions = (
        "Tu es l'assistant administratif d'EESAG. Tu aides à analyser, rédiger et "
        "proposer des mises à jour. Tu ne prends jamais de décision disciplinaire, financière "
        "ou d'accès sans validation humaine. N'invente aucune donnée. Utilise uniquement le contexte fourni. "
        "Réponds en français, de façon structurée et concise."
    )
    prompt = json.dumps({"action": action, "contexte": context}, ensure_ascii=False)
    body = json.dumps({
        "model": model,
        "instructions": instructions,
        "input": prompt,
        "store": False,
    }).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
        text = _extract_text(payload)
        if text:
            return text, "openai", True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        pass
    return _local_fallback(action, context), "local-secours", False
