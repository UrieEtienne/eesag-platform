from datetime import timedelta

from django import template
from django.utils import timezone
from django.db.models import Sum

from apps.accounts.models import Utilisateur, Role, ROLES_BUREAU_NATIONAL
from apps.churches.models import Eglise, Departement, Annexe
from apps.documents.models import Document
from apps.notifications.models import Notification
from apps.finance.models import Transaction, Projet

register = template.Library()


@register.simple_tag(takes_context=True)
def platform_metrics(context):
    """Données du tableau d'administration, calculées selon le périmètre connecté."""
    request = context.get("request")
    user = getattr(request, "user", None)
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    is_coord = bool(user and user.is_authenticated and (getattr(user, "role", "") == Role.COORDINATEUR or user.is_superuser))

    bureau = None
    if user and user.is_authenticated and getattr(user, "role", "") in {"SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"}:
        try:
            bureau = user.bureaux_administres.filter(actif=True).select_related("bureau").first()
        except Exception:
            bureau = None

    is_special = bool(bureau)
    is_general = bool(user and user.is_authenticated and getattr(user, "role", "") in {"SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"} and not bureau)
    eglise = getattr(user, "eglise", None) if user else None
    is_local = bool(user and user.is_authenticated and getattr(user, "role", "") in {"ADMIN_LOCAL", "PASTEUR"} and getattr(user, "eglise_id", None))

    total_entrees = Transaction.objects.exclude(type_transaction="SORTIE").aggregate(v=Sum("montant"))["v"] or 0
    total_sorties = Transaction.objects.filter(type_transaction="SORTIE").aggregate(v=Sum("montant"))["v"] or 0

    if is_coord:
        scope_label = "Coordinateur · Propriétaire du système"
        membres = Utilisateur.objects.filter(actif=True).count()
        annexes = Annexe.objects.filter(active=True).count()
        documents = Document.objects.count()
        notifications = Notification.objects.count()
        bureau_membres = 0
    elif is_general:
        scope_label = "Bureau national"
        membres = Utilisateur.objects.filter(eglise__isnull=True, actif=True).count()
        annexes = 0
        documents = Document.objects.filter(eglise_expediteur__isnull=True).count()
        notifications = Notification.objects.filter(destinataire=user).count()
        try:
            bureau_membres = sum(b.membres_independants.filter(actif=True).count() for b in user.bureaux_administres.all()[:20])
        except Exception:
            bureau_membres = 0
    elif is_special:
        scope_label = bureau.bureau.nom
        membres = bureau.bureau.membres_independants.filter(actif=True).count()
        annexes = 0
        documents = Document.objects.filter(expediteur=user).count()
        notifications = Notification.objects.filter(destinataire=user).count()
        bureau_membres = membres
    elif is_local:
        scope_label = eglise.nom
        membres = eglise.utilisateurs.filter(actif=True).count()
        annexes = eglise.annexes.filter(active=True).count()
        documents = Document.objects.filter(eglise_expediteur=eglise).count()
        notifications = Notification.objects.filter(destinataire=user).count()
        bureau_membres = 0
    else:
        scope_label = "Espace EESAG"
        membres = 0
        annexes = 0
        documents = 0
        notifications = Notification.objects.filter(destinataire=user).count() if user and user.is_authenticated else 0
        bureau_membres = 0

    return {
        "eglises": Eglise.objects.count(),
        "eglises_actives": Eglise.objects.filter(statut=Eglise.Statut.ACTIVE, plateforme_active=True).count(),
        "eglises_a_activer": Eglise.objects.filter(plateforme_active=False).count(),
        "membres": membres,
        "bureau_national": Utilisateur.objects.filter(role__in=ROLES_BUREAU_NATIONAL, actif=True, eglise__isnull=True).count(),
        "bureau_membres": bureau_membres,
        "departements": Departement.objects.count() if (is_coord or is_local) else 0,
        "annexes": annexes,
        "documents": documents,
        "notifications": notifications,
        "nouveaux_membres_7j": Utilisateur.objects.filter(date_enregistrement__gte=week_ago).count(),
        "nouvelles_eglises_7j": Eglise.objects.filter(date_enregistrement_systeme__gte=week_ago).count(),
        "transactions": Transaction.objects.count(),
        "projets": Projet.objects.count(),
        "finance_entrees": total_entrees,
        "finance_sorties": total_sorties,
        "finance_solde": total_entrees - total_sorties,
        "scope_label": scope_label,
        "eglises_actives_percent": round((Eglise.objects.filter(plateforme_active=True).count() / Eglise.objects.count()) * 100) if Eglise.objects.count() else 0,
    }
