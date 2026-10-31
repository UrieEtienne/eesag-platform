from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db import transaction
from apps.accounts.models import Role, DelegationEglise, ROLES_BUREAU_NATIONAL
from apps.accounts.permissions import PeutGererFinances, PeutGererProjets
from apps.bureaux.models import BureauAdministrateur
from .models import Transaction, Projet
from .serializers import TransactionSerializer, ProjetSerializer


def perimetre_financier_utilisateur(user):
    """Retourne l'unique périmètre financier explicitement autorisé."""
    aucun = {"type": "NONE"}

    if not user or not user.is_authenticated or not user.actif:
        return aucun

    # Le Coordinateur et les superutilisateurs n'ont aucun
    # accès financier automatique.
    if user.role == Role.COORDINATEUR or user.is_superuser:
        return aucun

    roles_financiers_autorises = {
        Role.SUPERADMIN_INTL,
        Role.SUPERADMIN_NATIONAL,
        Role.ADMIN_LOCAL,
        Role.PASTEUR,
        Role.RESPONSABLE_DEPARTEMENT,
    }

    if user.role not in roles_financiers_autorises:
        return aucun

    delegation = (
        DelegationEglise.objects.filter(
            utilisateur=user,
            actif=True,
            permissions__code="GESTION_FINANCES",
        )
        .distinct()
        .first()
    )

    if delegation and not user.eglise_id:
        return aucun

    if delegation and user.role in ROLES_BUREAU_NATIONAL:
        return aucun

    affectations = list(
        BureauAdministrateur.objects.filter(
            utilisateur=user,
            actif=True,
            bureau__actif=True,
            peut_gerer_finances=True,
        ).select_related("bureau")[:2]
    )

    # Une seule structure financière par utilisateur.
    if len(affectations) > 1 or (delegation and affectations):
        return aucun

    if delegation:
        return {
            "type": "EGLISE",
            "eglise_id": user.eglise_id,
        }

    if len(affectations) == 1:
        admin = affectations[0]
        return {
            "type": "BUREAU",
            "bureau_id": admin.bureau_id,
            "bureau_nom": admin.bureau.nom,
            "niveau": admin.bureau.niveau,
        }

    return aucun


def perimetre_projet_utilisateur(user):
    """Périmètre des projets, distinct de l'autorisation financière."""
    aucun = {"type": "NONE"}

    if not user or not user.is_authenticated:
        return aucun

    if user.role == Role.COORDINATEUR or user.is_superuser:
        return aucun

    if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR] and user.eglise_id:
        return {"type": "EGLISE", "eglise_id": user.eglise_id}

    affectations = list(
        BureauAdministrateur.objects.filter(
            utilisateur=user,
            actif=True,
            bureau__actif=True,
            peut_gerer_projets=True,
        ).select_related("bureau")[:2]
    )

    if len(affectations) != 1:
        return aucun

    admin = affectations[0]
    return {
        "type": "BUREAU",
        "bureau_id": admin.bureau_id,
        "bureau_nom": admin.bureau.nom,
    }


def _filter_scope(queryset, scope):
    if not scope:
        return queryset.none()

    if scope.get("type") == "EGLISE":
        return queryset.filter(
            eglise_id=scope.get("eglise_id"),
            bureau__isnull=True,
        )

    if scope.get("type") == "BUREAU":
        return queryset.filter(
            bureau_id=scope.get("bureau_id"),
            eglise__isnull=True,
        )

    return queryset.none()


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [PeutGererFinances]

    def get_queryset(self):
        scope = perimetre_financier_utilisateur(self.request.user)
        return _filter_scope(
            Transaction.objects.select_related(
                "eglise", "bureau", "enregistre_par"
            ),
            scope,
        )

    def perform_create(self, serializer):
        scope = perimetre_financier_utilisateur(self.request.user)

        if scope["type"] == "EGLISE":
            serializer.save(
                enregistre_par=self.request.user,
                eglise_id=scope["eglise_id"],
                bureau=None,
            )
        elif scope["type"] == "BUREAU":
            serializer.save(
                enregistre_par=self.request.user,
                eglise=None,
                bureau_id=scope["bureau_id"],
            )
        else:
            raise PermissionDenied(
                "Aucun périmètre financier ne vous est attribué."
            )

    @action(detail=False, methods=["get"])
    def resume(self, request):
        scope = perimetre_financier_utilisateur(request.user)

        if scope["type"] == "NONE":
            raise PermissionDenied("Accès financier non autorisé.")

        qs = self.get_queryset()
        entrees = (
            qs.exclude(type_transaction="SORTIE")
            .aggregate(total=Sum("montant"))["total"] or 0
        )
        sorties = (
            qs.filter(type_transaction="SORTIE")
            .aggregate(total=Sum("montant"))["total"] or 0
        )
        par_type = qs.values("type_transaction").annotate(
            total=Sum("montant")
        )

        return Response({
            "total_entrees": entrees,
            "total_sorties": sorties,
            "solde": entrees - sorties,
            "par_type": list(par_type),
            "perimetre": scope,
        })


class ProjetViewSet(viewsets.ModelViewSet):
    serializer_class = ProjetSerializer
    permission_classes = [PeutGererProjets]

    def get_queryset(self):
        return _filter_scope(
            Projet.objects.select_related(
                "eglise", "bureau", "responsable"
            ),
            perimetre_projet_utilisateur(self.request.user),
        )

    def perform_create(self, serializer):
        scope = perimetre_projet_utilisateur(self.request.user)

        if scope["type"] == "EGLISE":
            serializer.save(
                eglise_id=scope["eglise_id"],
                bureau=None,
            )
        elif scope["type"] == "BUREAU":
            serializer.save(
                eglise=None,
                bureau_id=scope["bureau_id"],
            )
        else:
            raise PermissionDenied(
                "Aucun périmètre de projet ne vous est attribué."
            )