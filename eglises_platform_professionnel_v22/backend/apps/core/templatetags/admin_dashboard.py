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
    try:
        eglise_model = apps.get_model("churches", "Eglise")
        user_model = apps.get_model("accounts", "Utilisateur")
        transaction_model = apps.get_model("finance", "Transaction")
        project_model = apps.get_model("finance", "Projet")
        notification_model = apps.get_model("notifications", "Notification")
        document_model = apps.get_model("documents", "Document")
        departement_model = apps.get_model("churches", "Departement")
        annexe_model = apps.get_model("churches", "Annexe")

        eglises = eglise_model.objects.all()
        utilisateurs = user_model.objects.filter(actif=True)
        transactions = transaction_model.objects.all()
        entrees = transactions.exclude(type_transaction="SORTIE").aggregate(s=Sum("montant"))["s"] or 0
        sorties = transactions.filter(type_transaction="SORTIE").aggregate(s=Sum("montant"))["s"] or 0
        projets = project_model.objects.all()
        week_ago = timezone.now() - timedelta(days=7)

        return {
            "eglises": eglises.count(),
            "eglises_actives": eglises.filter(statut="ACTIVE").count(),
            "membres": utilisateurs.exclude(eglise__isnull=True).count(),
            "membres_nationaux": utilisateurs.filter(eglise__isnull=True).count(),
            "documents": document_model.objects.count(),
            "notifications": notification_model.objects.count(),
            "departements": departement_model.objects.count(),
            "annexes": annexe_model.objects.filter(active=True).count(),
            "projets": projets.count(),
            "projets_nationaux": projets.filter(eglise__isnull=True).count(),
            "transactions": transactions.count(),
            "finance_entrees": entrees,
            "finance_sorties": sorties,
            "finance_solde": entrees - sorties,
            "finance_nationale_entrees": transactions.filter(eglise__isnull=True).exclude(type_transaction="SORTIE").aggregate(s=Sum("montant"))["s"] or 0,
            "finance_nationale_sorties": transactions.filter(eglise__isnull=True, type_transaction="SORTIE").aggregate(s=Sum("montant"))["s"] or 0,
            "bureau_national": user_model.objects.filter(role__in=["SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"], eglise__isnull=True, actif=True).count(),
            "nouvelles_eglises_7j": eglise_model.objects.filter(date_enregistrement_systeme__gte=week_ago).count(),
            "nouveaux_membres_7j": user_model.objects.filter(date_enregistrement__gte=week_ago).count(),
            "eglises_actives_percent": round((eglises.filter(statut="ACTIVE").count() / eglises.count()) * 100) if eglises.count() else 0,
        }
    except Exception:
        return {
            "eglises": 0, "eglises_actives": 0, "membres": 0, "membres_nationaux": 0,
            "documents": 0, "notifications": 0, "departements": 0, "annexes": 0,
            "projets": 0, "projets_nationaux": 0, "transactions": 0,
            "finance_entrees": 0, "finance_sorties": 0, "finance_solde": 0,
            "finance_nationale_entrees": 0, "finance_nationale_sorties": 0,
            "bureau_national": 0, "nouvelles_eglises_7j": 0, "nouveaux_membres_7j": 0, "eglises_actives_percent": 0,
        }
