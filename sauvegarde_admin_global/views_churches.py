from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.accounts.models import Role, ROLES_NATIONAUX, Utilisateur
from django.utils import timezone
from apps.accounts.permissions import (
    EstAdminLocalOuPlus,
    EstCoordinateurOuGestionEglise,
    EstCoordinateurOuBureauNationalGeneral,
    EstSuperAdminNationalOuPlus,
)
from apps.bureaux.models import BureauAdministrateur
from .models import (
    Annexe,
    Departement,
    Eglise,
    RoleEglise,
)
from .serializers import (
    EgliseAnnuaireSerializer,
    EgliseCreateSerializer,
    EgliseDetailSerializer,
    EgliseListSerializer,
    AnnexeSerializer,
    DepartementSerializer,
    RoleEgliseSerializer,
)


# ============================================================
# 2. BUREAU NATIONAL SPÉCIFIQUE
# ============================================================

def _est_bureau_specifique(user):
    """
    Retourne True lorsqu'un SUPERADMIN est rattaché
    à un bureau national spécialisé.
    """

    return (
        user.role in (
            Role.SUPERADMIN_INTL,
            Role.SUPERADMIN_NATIONAL,
        )
        and BureauAdministrateur.objects.filter(
            utilisateur=user,
            actif=True,
        ).exists()
    )


# ============================================================
# 3. BUREAU NATIONAL GÉNÉRAL
# ============================================================

def _est_national_general(user):
    """
    Coordinateur / superadmin système / bureau national général.
    """

    return (
        user.role == Role.COORDINATEUR
        or user.is_superuser
        or (
            user.role in (
                Role.SUPERADMIN_INTL,
                Role.SUPERADMIN_NATIONAL,
            )
            and not _est_bureau_specifique(user)
        )
    )

# ============================================================
# 4. ÉGLISES
# ============================================================

class EgliseViewSet(viewsets.ModelViewSet):

    queryset = (
        Eglise.objects
        .select_related(
            "region",
            "prefecture",
            "district",
            "commune",
            "responsable",
        )
        .annotate(
            nb_membres=Count(
                "utilisateurs",
                filter=Q(utilisateurs__actif=True),
            )
        )
    )

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "region",
        "prefecture",
        "district",
        "commune",
        "statut",
        "plateforme_active",
    ]

    search_fields = [
        "nom",
        "code",
        "telephone",
        
        "adresse_precise",
    ]

    ordering_fields = [
        "nom",
        "code",
        "date_creation",
        "date_enregistrement_systeme",
    ]

    ordering = ["nom"]

    # --------------------------------------------------------
    # 4.1 SERIALIZER
    # --------------------------------------------------------

    def get_serializer_class(self):
        user = self.request.user

        if self.action == "create":
            return EgliseCreateSerializer

        if self.action == "retrieve":
            return EgliseDetailSerializer

        if _est_bureau_specifique(user):
            return EgliseAnnuaireSerializer

        if user.role not in ROLES_NATIONAUX:
            return EgliseAnnuaireSerializer

        return EgliseListSerializer

    # --------------------------------------------------------
    # 4.2 PERMISSIONS
    # --------------------------------------------------------

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]

        return [EstCoordinateurOuBureauNationalGeneral()]

    # --------------------------------------------------------
    # 4.3 QUERYSET GÉNÉRAL
    # --------------------------------------------------------

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Coordinateur / superutilisateur
        if (
            user.role == Role.COORDINATEUR
            or user.is_superuser
        ):
            return qs

        # Bureau national général
        if _est_national_general(user):
            return qs

        # Bureau national spécialisé
        if _est_bureau_specifique(user):
            bureau = BureauAdministrateur.objects.filter(
                utilisateur=user,
                actif=True,
            ).first()

            if not bureau:
                return qs.none()

            if hasattr(bureau, "eglises"):
                return qs.filter(
                    id__in=bureau.eglises.values_list(
                        "id",
                        flat=True,
                    )
                )

            return qs.none()

        # Utilisateur rattaché à une église
        eglise_id = getattr(user, "eglise_id", None)

        if eglise_id:
            return qs.filter(id=eglise_id)

        return qs.none()
        # --------------------------------------------------------
    # 4.4 ACTIVATION / DÉSACTIVATION DE LA PLATEFORME
    # Réservé exclusivement au Coordinateur
    # --------------------------------------------------------

    def _verifier_coordinateur(self, request):
        if (
            not request.user.is_authenticated
            or request.user.role != Role.COORDINATEUR
        ):
            raise PermissionDenied(
                "Seul le Coordinateur peut modifier l'accès à la plateforme."
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="activer_plateforme",
        permission_classes=[IsAuthenticated],
    )
    def activer_plateforme(self, request, pk=None):
        self._verifier_coordinateur(request)

        eglise = self.get_object()

        if not eglise.plateforme_active:
            eglise.plateforme_active = True
            eglise.date_activation_plateforme = timezone.now()
            eglise.activee_par = request.user
            eglise.save(update_fields=[
                "plateforme_active",
                "date_activation_plateforme",
                "activee_par",
            ])

        return Response({
            "detail": f"La plateforme de {eglise.nom} est activée.",
            "eglise": EgliseListSerializer(
                eglise,
                context={"request": request},
            ).data,
        })

    @action(
        detail=True,
        methods=["post"],
        url_path="desactiver_plateforme",
        permission_classes=[IsAuthenticated],
    )
    def desactiver_plateforme(self, request, pk=None):
        self._verifier_coordinateur(request)

        eglise = self.get_object()

        if eglise.plateforme_active:
            eglise.plateforme_active = False
            eglise.save(update_fields=["plateforme_active"])

        return Response({
            "detail": f"La plateforme de {eglise.nom} est désactivée.",
            "eglise": EgliseListSerializer(
                eglise,
                context={"request": request},
            ).data,
        })

    # --------------------------------------------------------
    # 4.4 ANNUAIRE DES ÉGLISES DESTINATAIRES
    # --------------------------------------------------------

    @action(
        detail=False,
        methods=["get"],
        url_path="annuaire_destinations",
        permission_classes=[IsAuthenticated],
        filter_backends=[],
    )
    def annuaire_destinations(self, request):
        """
        Retourne uniquement les églises :
        - dont le statut est ACTIVE ;
        - dont la plateforme est activée.

        Cet endpoint ne modifie pas les restrictions de /eglises/.
        Il sert à choisir une église destinataire d'un courrier.
        """

        eglises = (
            Eglise.objects
            .filter(
                statut=Eglise.Statut.ACTIVE,
                plateforme_active=True,
            )
            .order_by("nom")
        )

        # Pour un utilisateur rattaché à une église,
        # exclure son église de l'annuaire des destinations.
        eglise_origine_id = getattr(
            request.user,
            "eglise_id",
            None,
        )

        if eglise_origine_id:
            eglises = eglises.exclude(
                id=eglise_origine_id
            )

        serializer = EgliseAnnuaireSerializer(
            eglises,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data)

    # --------------------------------------------------------
    # 4.5 AFFECTER UN PASTEUR
    # --------------------------------------------------------

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[EstSuperAdminNationalOuPlus],
    )
    def affecter_pasteur(self, request, pk=None):

        if not _est_national_general(request.user):
            return Response(
                {
                    "detail": (
                        "Seul le Coordinateur ou le "
                        "Bureau national général peut "
                        "affecter un pasteur."
                    )
                },
                status=403,
            )

        eglise = self.get_object()
        utilisateur_id = request.data.get("utilisateur_id")

        try:
            nouveau = Utilisateur.objects.get(
                pk=utilisateur_id
            )
        except (
            Utilisateur.DoesNotExist,
            ValueError,
            TypeError,
        ):
            return Response(
                {"detail": "Utilisateur introuvable."},
                status=404,
            )

        ancien = eglise.responsable

        if ancien and ancien != nouveau:
            if ancien.role == Role.PASTEUR:
                ancien.role = Role.MEMBRE
                ancien.save(update_fields=["role"])

        nouveau.role = Role.PASTEUR
        nouveau.eglise = eglise
        nouveau.save(update_fields=["role", "eglise"])

        eglise.responsable = nouveau
        eglise.save(update_fields=["responsable"])

        return Response(
            EgliseDetailSerializer(
                eglise,
                context={"request": request},
            ).data
        )


# ============================================================
# 5. DÉPARTEMENTS
# ============================================================

class DepartementViewSet(viewsets.ModelViewSet):
    serializer_class = DepartementSerializer
    permission_classes = [EstCoordinateurOuGestionEglise]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = ["nom"]
    ordering_fields = ["nom"]
    ordering = ["nom"]

    def get_queryset(self):
        user = self.request.user

        if _est_bureau_specifique(user):
            return Departement.objects.none()

        return Departement.objects.order_by("nom")

    def perform_create(self, serializer):
        if _est_bureau_specifique(self.request.user):
            raise PermissionDenied(
                "Un bureau national spécialisé ne peut pas gérer les départements."
            )
        serializer.save()


# ============================================================
#  RÔLES D'ÉGLISE
# ============================================================

class RoleEgliseViewSet(viewsets.ModelViewSet):
    serializer_class = RoleEgliseSerializer
    permission_classes = [EstCoordinateurOuGestionEglise]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]

    filterset_fields = ["actif"]
    search_fields = ["nom"]
    ordering = ["nom"]

    def get_queryset(self):
        user = self.request.user

        if _est_bureau_specifique(user):
            return RoleEglise.objects.none()

        return RoleEglise.objects.order_by("nom")

    def perform_create(self, serializer):
        if _est_bureau_specifique(self.request.user):
            raise PermissionDenied(
                "Un bureau national spécialisé ne peut pas gérer les rôles d'église."
            )
        serializer.save()



# ============================================================
# 7. ANNEXES
# ============================================================

class AnnexeViewSet(viewsets.ModelViewSet):

    serializer_class = AnnexeSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
    ]

    filterset_fields = [
        "eglise",
        "active",
    ]

    search_fields = [
        "nom",
        "code",
        "adresse",
        "telephone",
    ]

    def get_permissions(self):

        if self.request.method in (
            "GET",
            "HEAD",
            "OPTIONS",
        ):
            return [
                IsAuthenticated()
            ]

        return [
            EstAdminLocalOuPlus()
        ]

    def get_queryset(self):

        qs = Annexe.objects.select_related(
            "eglise",
            "responsable",
        )

        user = self.request.user

        # Bureau national spécialisé :
        # aucune gestion directe des annexes
        if _est_bureau_specifique(user):
            return qs.none()

        # Coordinateur / national général
        if (
            user.role in ROLES_NATIONAUX
            or user.is_superuser
        ):
            return qs

        # Gestionnaire local
        if getattr(user, "eglise_id", None):
            return qs.filter(
                eglise_id=user.eglise_id
            )

        return qs.none()

    def perform_create(self, serializer):

        user = self.request.user

        if _est_bureau_specifique(user):

            raise PermissionDenied(
                "Un bureau national spécifique ne peut "
                "pas gérer les annexes d'une église."
            )

        if (
            user.role in ROLES_NATIONAUX
            or user.is_superuser
        ):
            serializer.save()

        else:
            serializer.save(
                eglise=user.eglise
            )