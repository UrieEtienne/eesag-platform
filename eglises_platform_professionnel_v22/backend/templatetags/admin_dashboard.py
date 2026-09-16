from datetime import timedelta

from django import template
from django.utils import timezone
from django.db.models import Sum

from apps.accounts.models import Utilisateur, Role, ROLES_NATIONAUX, ROLES_BUREAU_NATIONAL
from apps.churches.models import Eglise, Departement, Annexe
from apps.documents.models import Document
from apps.notifications.models import Notification
from apps.finance.models import Transaction, Projet

register = template.Library()


@register.simple_tag
def platform_metrics():
    """Données réelles utilisées par l'accueil de l'admin Django."""
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    total_entrees = Transaction.objects.exclude(type_transaction="SORTIE").aggregate(v=Sum("montant"))["v"] or 0
    total_sorties = Transaction.objects.filter(type_transaction="SORTIE").aggregate(v=Sum("montant"))["v"] or 0

    return {
        "eglises": Eglise.objects.count(),
        "eglises_actives": Eglise.objects.filter(statut=Eglise.Statut.ACTIVE).count(),
        "membres": Utilisateur.objects.filter(actif=True).count(),
        "bureau_national": Utilisateur.objects.filter(role__in=ROLES_BUREAU_NATIONAL, actif=True, eglise__isnull=True).count(),
        "departements": Departement.objects.count(),
        "annexes": Annexe.objects.filter(active=True).count(),
        "documents": Document.objects.count(),
        "notifications": Notification.objects.count(),
        "nouveaux_membres_7j": Utilisateur.objects.filter(date_enregistrement__gte=week_ago).count(),
        "nouvelles_eglises_7j": Eglise.objects.filter(date_enregistrement_systeme__gte=week_ago).count(),
        "transactions": Transaction.objects.count(),
        "projets": Projet.objects.count(),
        "finance_entrees": total_entrees,
        "finance_sorties": total_sorties,
        "finance_solde": total_entrees - total_sorties,
        "eglises_actives_percent": round((Eglise.objects.filter(statut=Eglise.Statut.ACTIVE).count() / Eglise.objects.count()) * 100) if Eglise.objects.count() else 0,
    }
