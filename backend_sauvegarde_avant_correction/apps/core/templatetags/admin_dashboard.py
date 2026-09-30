from django import template
from django.apps import apps
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

register = template.Library()


def count_model(app_label, model_name, **filters):
    try:
        return apps.get_model(app_label, model_name).objects.filter(**filters).count()
    except (LookupError, AttributeError):
        return 0


@register.simple_tag(takes_context=True)
def platform_metrics(context):
    user = context.get("user")
    empty = {
        "eglises": 0, "eglises_actives": 0, "membres": 0, "membres_nationaux": 0,
        "documents": 0, "notifications": 0, "departements": 0, "annexes": 0,
        "projets": 0, "projets_nationaux": 0, "transactions": 0,
        "finance_entrees": 0, "finance_sorties": 0, "finance_solde": 0,
        "finance_nationale_entrees": 0, "finance_nationale_sorties": 0,
        "bureau_national": 0, "nouvelles_eglises_7j": 0, "nouveaux_membres_7j": 0,
        "eglises_actives_percent": 0, "bureau_membres": 0, "scope_label": "EESAG",
    }
    try:
        from apps.accounts.models import Role, Utilisateur
        from apps.bureaux.models import BureauAdministrateur, BureauMembre
        eglise_model = apps.get_model("churches", "Eglise")
        document_model = apps.get_model("documents", "Document")
        notification_model = apps.get_model("notifications", "Notification")
        transaction_model = apps.get_model("finance", "Transaction")
        project_model = apps.get_model("finance", "Projet")
        if not user or not user.is_authenticated:
            return empty
        is_coord = user.role == Role.COORDINATEUR or user.is_superuser
        assigned = BureauAdministrateur.objects.filter(utilisateur=user, actif=True).select_related("bureau").first()
        if is_coord:
            scope = "Coordinateur · Propriétaire du système"
            eglises = eglise_model.objects.all()
            utilisateurs = Utilisateur.objects.filter(actif=True)
        elif assigned:
            scope = assigned.bureau.nom
            bureau = assigned.bureau
            bm = BureauMembre.objects.filter(bureau=bureau, actif=True).count()
            empty.update({"scope_label": scope, "bureau_membres": bm})
            return empty
        elif user.role in (Role.ADMIN_LOCAL, Role.PASTEUR) and user.eglise_id:
            scope = user.eglise.nom
            eglises = eglise_model.objects.filter(pk=user.eglise_id)
            utilisateurs = Utilisateur.objects.filter(actif=True, eglise_id=user.eglise_id)
        else:
            scope = "Bureau national"
            eglises = eglise_model.objects.all()
            utilisateurs = Utilisateur.objects.filter(actif=True, eglise__isnull=True)
        transactions = transaction_model.objects.filter(eglise__in=eglises) if hasattr(transaction_model, "eglise") else transaction_model.objects.none()
        entrees = transactions.exclude(type_transaction="SORTIE").aggregate(s=Sum("montant"))["s"] or 0
        sorties = transactions.filter(type_transaction="SORTIE").aggregate(s=Sum("montant"))["s"] or 0
        total = eglises.count()
        actifs = eglises.filter(statut="ACTIVE").count()
        return {
            **empty,
            "eglises": total, "eglises_actives": actifs,
            "membres": utilisateurs.count(), "membres_nationaux": utilisateurs.filter(eglise__isnull=True).count(),
            "documents": document_model.objects.filter(eglise__in=eglises).count() if hasattr(document_model, "eglise") else 0,
            "notifications": notification_model.objects.filter(destinataire=user).count() if hasattr(notification_model, "destinataire") else 0,
            "departements": apps.get_model("churches", "Departement").objects.count() if not assigned else 0,
            "annexes": apps.get_model("churches", "Annexe").objects.filter(eglise__in=eglises, active=True).count(),
            "transactions": transactions.count(), "finance_entrees": entrees, "finance_sorties": sorties, "finance_solde": entrees-sorties,
            "bureau_national": Utilisateur.objects.filter(role__in=["SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"], eglise__isnull=True, actif=True).count(),
            "scope_label": scope,
        }
    except Exception:
        return empty
