from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Role, ROLES_BUREAU_NATIONAL
from apps.accounts.permissions import PeutGererFinances, PeutGererProjets
from apps.bureaux.models import BureauAdministrateur
from .models import Transaction, Projet
from .serializers import TransactionSerializer, ProjetSerializer


def perimetre_financier_utilisateur(user):
    if user.role == Role.COORDINATEUR or user.is_superuser:
        return {"type": "GLOBAL"}
    if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR] and user.eglise_id:
        return {"type": "EGLISE", "eglise_id": user.eglise_id}
    admin = BureauAdministrateur.objects.filter(utilisateur=user, actif=True, peut_gerer_finances=True).select_related("bureau").first()
    if admin:
        return {"type": "BUREAU", "bureau_id": admin.bureau_id, "bureau_nom": admin.bureau.nom}
    if user.role in ROLES_BUREAU_NATIONAL:
        return {"type": "NATIONAL"}
    return {"type": "NONE"}


def perimetre_projet_utilisateur(user):
    if user.role == Role.COORDINATEUR or user.is_superuser:
        return {"type": "GLOBAL"}
    if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR] and user.eglise_id:
        return {"type": "EGLISE", "eglise_id": user.eglise_id}
    admin = BureauAdministrateur.objects.filter(utilisateur=user, actif=True, peut_gerer_projets=True).select_related("bureau").first()
    if admin:
        return {"type": "BUREAU", "bureau_id": admin.bureau_id, "bureau_nom": admin.bureau.nom}
    if user.role in ROLES_BUREAU_NATIONAL:
        return {"type": "NATIONAL"}
    return {"type": "NONE"}


def _filter_scope(qs, scope):
    if scope["type"] == "GLOBAL":
        return qs
    if scope["type"] == "EGLISE":
        return qs.filter(eglise_id=scope["eglise_id"])
    if scope["type"] == "BUREAU":
        return qs.filter(bureau_id=scope["bureau_id"])
    if scope["type"] == "NATIONAL":
        return qs.filter(eglise__isnull=True, bureau__isnull=True)
    return qs.none()


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [PeutGererFinances]
    def get_queryset(self):
        return _filter_scope(Transaction.objects.select_related("eglise", "bureau", "enregistre_par"), perimetre_financier_utilisateur(self.request.user))
    def perform_create(self, serializer):
        scope = perimetre_financier_utilisateur(self.request.user)
        if scope["type"] == "EGLISE":
            serializer.save(enregistre_par=self.request.user, eglise_id=scope["eglise_id"], bureau=None)
        elif scope["type"] == "BUREAU":
            serializer.save(enregistre_par=self.request.user, eglise=None, bureau_id=scope["bureau_id"])
        elif scope["type"] == "NATIONAL":
            serializer.save(enregistre_par=self.request.user, eglise=None, bureau=None)
        elif scope["type"] == "GLOBAL":
            serializer.save(enregistre_par=self.request.user)
        else:
            raise PermissionError("Aucun périmètre financier autorisé.")
    @action(detail=False, methods=["get"])
    def resume(self, request):
        qs = self.get_queryset()
        entrees = qs.exclude(type_transaction="SORTIE").aggregate(total=Sum("montant"))["total"] or 0
        sorties = qs.filter(type_transaction="SORTIE").aggregate(total=Sum("montant"))["total"] or 0
        par_type = qs.values("type_transaction").annotate(total=Sum("montant"))
        scope = perimetre_financier_utilisateur(request.user)
        return Response({"total_entrees": entrees, "total_sorties": sorties, "solde": entrees - sorties, "par_type": list(par_type), "perimetre": scope})


class ProjetViewSet(viewsets.ModelViewSet):
    serializer_class = ProjetSerializer
    permission_classes = [PeutGererProjets]
    def get_queryset(self):
        return _filter_scope(Projet.objects.select_related("eglise", "bureau", "responsable"), perimetre_projet_utilisateur(self.request.user))
    def perform_create(self, serializer):
        scope = perimetre_projet_utilisateur(self.request.user)
        if scope["type"] == "EGLISE":
            serializer.save(eglise_id=scope["eglise_id"], bureau=None)
        elif scope["type"] == "BUREAU":
            serializer.save(eglise=None, bureau_id=scope["bureau_id"])
        elif scope["type"] == "NATIONAL":
            serializer.save(eglise=None, bureau=None)
        elif scope["type"] == "GLOBAL":
            serializer.save()
        else:
            raise PermissionError("Aucun périmètre de projet autorisé.")
