from django.db.models import Count, Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.permissions import EstSuperAdminNationalOuPlus, EstAdminLocalOuPlus
from apps.accounts.models import ROLES_NATIONAUX, Role, Utilisateur
from .models import Religion, Eglise, Departement, RoleEglise, Annexe
from .serializers import (
    ReligionSerializer, EgliseListSerializer, EgliseDetailSerializer, EgliseCreateSerializer,
    DepartementSerializer, RoleEgliseSerializer, AnnexeSerializer,
)


class ReligionViewSet(viewsets.ModelViewSet):
    queryset = Religion.objects.all()
    serializer_class = ReligionSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [EstSuperAdminNationalOuPlus()]


class EgliseViewSet(viewsets.ModelViewSet):
    queryset = Eglise.objects.select_related(
        "religion", "region", "prefecture", "district", "commune", "responsable"
    ).annotate(nb_membres=Count("utilisateurs", filter=Q(utilisateurs__actif=True)))
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["religion", "region", "prefecture", "district", "commune", "statut"]
    search_fields = ["nom", "code", "adresse_precise"]
    ordering_fields = ["nom", "date_creation", "date_enregistrement_systeme"]

    def get_serializer_class(self):
        if self.action == "create":
            return EgliseCreateSerializer
        if self.action == "retrieve":
            return EgliseDetailSerializer
        if self.action == "list" and self.request.user.role not in ROLES_NATIONAUX:
            return EgliseAnnuaireSerializer
        return EgliseListSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [EstSuperAdminNationalOuPlus()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role in ROLES_NATIONAUX:
            return qs
        # L'annuaire peut être recherché par nom/code, mais le détail interne
        # d'une église étrangère n'est jamais exposé.
        if self.action in ("list",):
            return qs
        return qs.filter(id=user.eglise_id)

    @action(detail=True, methods=["post"], permission_classes=[EstSuperAdminNationalOuPlus])
    def affecter_pasteur(self, request, pk=None):
        eglise = self.get_object()
        utilisateur_id = request.data.get("utilisateur_id")
        try:
            nouveau_pasteur = Utilisateur.objects.get(pk=utilisateur_id)
        except Utilisateur.DoesNotExist:
            return Response({"detail": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)

        ancien = eglise.responsable
        if ancien and ancien != nouveau_pasteur:
            ancien.role = Role.MEMBRE if ancien.role == Role.PASTEUR else ancien.role
            ancien.save(update_fields=["role"])

        nouveau_pasteur.role = Role.PASTEUR
        nouveau_pasteur.eglise = eglise
        nouveau_pasteur.save(update_fields=["role", "eglise"])
        eglise.responsable = nouveau_pasteur
        eglise.save(update_fields=["responsable"])

        from apps.members.models import Affectation
        Affectation.objects.filter(eglise=eglise, type_affectation="PASTEUR", actif=True).update(actif=False)
        Affectation.objects.create(utilisateur=nouveau_pasteur, eglise=eglise, type_affectation="PASTEUR", affecte_par=request.user)

        from apps.notifications.models import Notification
        Notification.objects.create(
            destinataire=nouveau_pasteur, eglise=eglise, titre="Nouvelle affectation pastorale",
            message=f"Vous êtes officiellement affecté comme pasteur de {eglise.nom}.", type_notification="AFFECTATION"
        )
        return Response(EgliseDetailSerializer(eglise).data)


class DepartementViewSet(viewsets.ModelViewSet):
    """Référentiel global des départements, sans rattachement à une église."""
    serializer_class = DepartementSerializer
    permission_classes = [EstAdminLocalOuPlus]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nom"]
    ordering_fields = ["nom"]

    def get_queryset(self):
        return Departement.objects.annotate(
            nb_membres=Count("membres_departement", filter=Q(membres_departement__actif=True))
        ).order_by("nom")

    def perform_create(self, serializer):
        serializer.save()


class RoleEgliseViewSet(viewsets.ModelViewSet):
    """Référentiel global et dynamique des rôles/fonctions d'église."""
    serializer_class = RoleEgliseSerializer
    permission_classes = [EstAdminLocalOuPlus]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["actif"]
    search_fields = ["nom"]
    ordering_fields = ["nom"]
    queryset = RoleEglise.objects.order_by("nom")


class AnnexeViewSet(viewsets.ModelViewSet):
    serializer_class = AnnexeSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [EstAdminLocalOuPlus()]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["eglise", "active"]
    search_fields = ["nom", "code", "adresse"]

    def get_queryset(self):
        qs = Annexe.objects.select_related("eglise", "responsable")
        user = self.request.user
        if user.role in ROLES_NATIONAUX:
            return qs
        return qs.filter(eglise_id=user.eglise_id)

    def perform_create(self, serializer):
        if self.request.user.role in ROLES_NATIONAUX:
            serializer.save()
        else:
            serializer.save(eglise=self.request.user.eglise)
