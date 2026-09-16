from django.db.models import Count, Q
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.models import Role, ROLES_NATIONAUX, Utilisateur
from apps.accounts.permissions import EstAdminLocalOuPlus, EstCoordinateurOuGestionEglise, EstCoordinateurOuBureauNationalGeneral, EstSuperAdminNationalOuPlus
from apps.bureaux.models import BureauAdministrateur
from .models import Annexe, Departement, Eglise, Religion, RoleEglise
from .serializers import EgliseAnnuaireSerializer, EgliseCreateSerializer, EgliseDetailSerializer, EgliseListSerializer, AnnexeSerializer, DepartementSerializer, ReligionSerializer, RoleEgliseSerializer


def _est_bureau_specifique(user):
    return user.role in (Role.SUPERADMIN_INTL, Role.SUPERADMIN_NATIONAL) and BureauAdministrateur.objects.filter(utilisateur=user, actif=True).exists()

def _est_national_general(user):
    return (user.role == Role.COORDINATEUR or user.is_superuser) or (user.role in (Role.SUPERADMIN_INTL, Role.SUPERADMIN_NATIONAL) and not _est_bureau_specifique(user))


class ReligionViewSet(viewsets.ModelViewSet):
    queryset = Religion.objects.all()
    serializer_class = ReligionSerializer
    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"): return [IsAuthenticated()]
        return [EstSuperAdminNationalOuPlus()]


class EgliseViewSet(viewsets.ModelViewSet):
    queryset = Eglise.objects.select_related("religion", "region", "prefecture", "district", "commune", "responsable").annotate(nb_membres=Count("utilisateurs", filter=Q(utilisateurs__actif=True)))
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["religion", "region", "prefecture", "district", "commune", "statut", "plateforme_active"]
    search_fields = ["nom", "code", "adresse_precise"]
    ordering_fields = ["nom", "date_creation", "date_enregistrement_systeme"]

    def get_serializer_class(self):
        user = self.request.user
        if self.action == "create": return EgliseCreateSerializer
        if _est_bureau_specifique(user): return EgliseAnnuaireSerializer
        if self.action == "retrieve": return EgliseDetailSerializer
        if user.role not in ROLES_NATIONAUX: return EgliseAnnuaireSerializer
        return EgliseListSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"): return [IsAuthenticated()]
        return [EstCoordinateurOuBureauNationalGeneral()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if _est_bureau_specifique(user): return qs
        if user.role in ROLES_NATIONAUX or user.is_superuser: return qs
        if self.action == "list": return qs
        return qs.filter(id=user.eglise_id)

    @action(detail=True, methods=["post"], permission_classes=[EstSuperAdminNationalOuPlus])
    def affecter_pasteur(self, request, pk=None):
        if not _est_national_general(request.user):
            return Response({"detail": "Seul le Coordinateur ou le Bureau national général peut affecter un pasteur."}, status=403)
        eglise=self.get_object(); utilisateur_id=request.data.get("utilisateur_id")
        try: nouveau=Utilisateur.objects.get(pk=utilisateur_id)
        except Utilisateur.DoesNotExist: return Response({"detail":"Utilisateur introuvable."}, status=404)
        ancien=eglise.responsable
        if ancien and ancien != nouveau: ancien.role=Role.MEMBRE if ancien.role==Role.PASTEUR else ancien.role; ancien.save(update_fields=["role"])
        nouveau.role=Role.PASTEUR; nouveau.eglise=eglise; nouveau.save(update_fields=["role","eglise"])
        eglise.responsable=nouveau; eglise.save(update_fields=["responsable"])
        return Response(EgliseDetailSerializer(eglise, context={"request":request}).data)


class DepartementViewSet(viewsets.ModelViewSet):
    serializer_class=DepartementSerializer
    permission_classes=[EstCoordinateurOuGestionEglise]
    filter_backends=[DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields=["nom"]; ordering_fields=["nom"]
    def get_queryset(self):
        if _est_bureau_specifique(self.request.user): return Departement.objects.none()
        return Departement.objects.all().annotate(nb_membres=Count("membres_departement", filter=Q(membres_departement__actif=True))).order_by("nom")


class RoleEgliseViewSet(viewsets.ModelViewSet):
    serializer_class=RoleEgliseSerializer
    permission_classes=[EstCoordinateurOuGestionEglise]
    filter_backends=[DjangoFilterBackend, filters.SearchFilter]
    search_fields=["nom"]
    def get_queryset(self):
        if _est_bureau_specifique(self.request.user): return RoleEglise.objects.none()
        return RoleEglise.objects.order_by("nom")


class AnnexeViewSet(viewsets.ModelViewSet):
    serializer_class=AnnexeSerializer
    filter_backends=[DjangoFilterBackend, filters.SearchFilter]
    filterset_fields=["eglise","active"]; search_fields=["nom","code","adresse"]
    def get_permissions(self):
        if self.request.method in ("GET","HEAD","OPTIONS"): return [IsAuthenticated()]
        return [EstAdminLocalOuPlus()]
    def get_queryset(self):
        qs=Annexe.objects.select_related("eglise","responsable"); user=self.request.user
        if _est_bureau_specifique(user): return qs.none()
        if user.role in ROLES_NATIONAUX or user.is_superuser: return qs
        return qs.filter(eglise_id=user.eglise_id)
    def perform_create(self, serializer):
        user=self.request.user
        if _est_bureau_specifique(user): raise PermissionDenied("Un bureau national spécifique ne peut pas gérer les annexes d'une église.")
        if user.role in ROLES_NATIONAUX or user.is_superuser: serializer.save()
        else: serializer.save(eglise=user.eglise)
