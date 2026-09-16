from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def scope_label(context):
    user = context.get("user")
    if not user or not getattr(user, "is_authenticated", False):
        return "Visiteur"
    role = getattr(user, "role", "")
    if role == "COORDINATEUR" or getattr(user, "is_superuser", False):
        return "Coordinateur · Propriétaire du système"
    if role in {"SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"}:
        try:
            from apps.bureaux.models import BureauAdministrateur
            bureau = (BureauAdministrateur.objects.filter(utilisateur=user, actif=True)
                      .select_related("bureau").first())
            if bureau and bureau.bureau:
                return bureau.bureau.nom
        except Exception:
            pass
        return "Bureau national"
    eglise = getattr(user, "eglise", None)
    return getattr(eglise, "nom", None) or "Espace membre"


@register.simple_tag(takes_context=True)
def scope_is_national_general(context):
    request = context.get("request")
    user = getattr(request, "user", None) if request else None
    try:
        from apps.core.admin_scopes import is_national_general
        return is_national_general(user)
    except Exception:
        return False
