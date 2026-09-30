from django.db.models import Count, Q
from django.utils import timezone

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from apps.accounts.models import (
    Role,
    ROLES_BUREAU_NATIONAL,
)
from .models import (
    Bureau,
    BureauZone,
    BureauAdministrateur,
    BureauMembreMandat,
    BureauMembre,
    NiveauBureau,
    TypeBureau,
)
from .serializers import (
    BureauSerializer,
    BureauAdministrateurSerializer,
    BureauMembreMandatSerializer,
)
from .serializers_zones import (
    BureauZoneSerializer,
    BureauZonalSerializer,
)
from .serializers_indep import (
    BureauMembreIndependantSerializer,
)





# ============================================================
# CONSTANTES
# ============================================================

TYPES_BUREAUX_ZONAUX = {
    TypeBureau.HOMMES,
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
}


# ============================================================
# OUTILS DE PERMISSIONS
# ============================================================

def _est_coordinateur(user):
    """
    Le Coordinateur possède tous les droits sur les bureaux.

    Le superutilisateur Django est également considéré
    comme administrateur système.
    """
    return (
        user.role == Role.COORDINATEUR
        or user.is_superuser
    )


def _est_national_general(user):
    """
    Un utilisateur du Bureau national est considéré comme
    Bureau national général lorsqu'il n'a aucune attribution
    active dans un bureau spécialisé.

    Le Coordinateur possède également les droits du
    Bureau national général.
    """
    if _est_coordinateur(user):
        return True

    if user.role not in ROLES_BUREAU_NATIONAL:
        return False

    return not BureauAdministrateur.objects.filter(
        utilisateur=user,
        actif=True,
    ).exists()


def _bureaux_administres(user):
    """
    Retourne les bureaux dont l'utilisateur est administrateur.
    """
    return (
        Bureau.objects
        .filter(
            administrateurs__utilisateur=user,
            administrateurs__actif=True,
        )
        .distinct()
    )


def a_droit_bureau(user, bureau, droit):
    """
    Vérifie si l'utilisateur possède un droit précis
    sur un bureau.
    """

    # Coordinateur = accès complet
    if _est_coordinateur(user):
        return True

    if not bureau:
        return False

    # Bureau national général
    if (
        _est_national_general(user)
        and bureau.niveau == NiveauBureau.NATIONAL
    ):
        return True

    # Administration locale
    if user.role in (
        Role.ADMIN_LOCAL,
        Role.PASTEUR,
    ):
        return (
            bureau.niveau == NiveauBureau.LOCAL
            and bureau.eglise_id == user.eglise_id
        )

    # Administrateur d'un bureau spécialisé
    return BureauAdministrateur.objects.filter(
        utilisateur=user,
        bureau=bureau,
        actif=True,
        **{droit: True},
    ).exists()


# ============================================================
# BUREAUX
# ============================================================

class BureauViewSet(viewsets.ModelViewSet):
    serializer_class = BureauSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
    ]

    filterset_fields = [
        "niveau",
        "type_bureau",
        "eglise",
        "actif",
    ]

    search_fields = [
        "nom",
        "code",
        "eglise__nom",
    ]

    def get_queryset(self):
        user = self.request.user

        qs = (
            Bureau.objects
            .select_related(
                "eglise",
                "zone",
                "bureau_parent",
            )
            .annotate(
                membres_actifs=Count(
                    "mandats",
                    filter=Q(mandats__actif=True),
                )
            )
        )

        # Coordinateur / Bureau national général
        if (
            _est_coordinateur(user)
            or _est_national_general(user)
        ):
            return qs

        # Bureau national spécialisé
        if user.role in ROLES_BUREAU_NATIONAL:
            return (
                qs
                .filter(
                    administrateurs__utilisateur=user,
                    administrateurs__actif=True,
                )
                .distinct()
            )

        # Administration locale
        if (
            user.eglise_id
            and user.role in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            )
        ):
            return (
                qs
                .filter(
                    Q(
                        niveau=NiveauBureau.NATIONAL
                    )
                    |
                    Q(
                        niveau=NiveauBureau.LOCAL,
                        eglise_id=user.eglise_id,
                    )
                )
                .distinct()
            )

        # Membre simple :
        # uniquement l'annuaire national
        return qs.filter(
            niveau=NiveauBureau.NATIONAL
        )

    def perform_create(self, serializer):
        user = self.request.user

        # Coordinateur / Bureau national général
        if (
            _est_coordinateur(user)
            or _est_national_general(user)
        ):
            serializer.save()
            return

        # Administration locale
        if (
            user.role in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            )
            and user.eglise_id
        ):
            serializer.save(
                niveau=NiveauBureau.LOCAL,
                eglise=user.eglise,
            )
            return

        raise PermissionDenied(
            "Vous ne pouvez pas créer ce bureau."
        )

    def perform_update(self, serializer):
        bureau = self.get_object()

        if not a_droit_bureau(
            self.request.user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous ne pouvez pas administrer ce bureau."
            )

        serializer.save(
            niveau=bureau.niveau,
            eglise=bureau.eglise,
        )

    def perform_destroy(self, instance):
        if not _est_coordinateur(self.request.user):
            raise PermissionDenied(
                "Seul le Coordinateur peut supprimer un bureau."
            )

        instance.delete()

    @action(
        detail=False,
        methods=["get"],
        url_path="mes-bureaux",
    )
    def mes_bureaux(self, request):
        qs = (
            _bureaux_administres(request.user)
            .annotate(
                membres_actifs=Count(
                    "mandats",
                    filter=Q(mandats__actif=True),
                )
            )
        )

        return Response(
            BureauSerializer(
                qs,
                many=True,
                context={"request": request},
            ).data
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="membres-candidats",
    )
    def membres_candidats(self, request):
        bureau_id = request.query_params.get("bureau")

        bureau = (
            Bureau.objects
            .filter(
                pk=bureau_id,
                actif=True,
            )
            .first()
        )

        if not bureau:
            raise PermissionDenied(
                "Bureau introuvable."
            )

        if not a_droit_bureau(
            request.user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas accès à ce bureau."
            )

        from apps.accounts.models import Utilisateur

        current_year = timezone.now().year

        base = (
            Utilisateur.objects
            .filter(actif=True)
            .exclude(role=Role.COORDINATEUR)
        )

        # Bureau national :
        # comptes sans église
        if bureau.niveau == NiveauBureau.NATIONAL:
            base = base.filter(
                eglise__isnull=True
            )

        # Bureau local :
        # comptes de l'église
        else:
            base = base.filter(
                eglise_id=bureau.eglise_id
            )

        used_ids = (
            bureau.mandats
            .filter(
                annee=current_year,
                actif=True,
            )
            .values_list(
                "utilisateur_id",
                flat=True,
            )
        )

        base = (
            base
            .exclude(id__in=used_ids)
            .order_by("nom", "prenom")
        )

        return Response([
            {
                "id": u.id,
                "identifiant": u.identifiant,
                "nom_complet": (
                    f"{u.prenom} {u.nom}"
                ),
                "photo": (
                    u.photo.url
                    if u.photo
                    else None
                ),
                "telephone": u.telephone,
            }
            for u in base[:500]
        ])


# ============================================================
# ZONES
# ============================================================

class BureauZoneViewSet(viewsets.ModelViewSet):
    """
    Gestion des zones géographiques.

    Création / modification :
        - Coordinateur
        - Bureau national général

    Suppression :
        - Coordinateur uniquement

    Les bureaux nationaux spécialisés peuvent consulter
    les zones existantes.
    """

    serializer_class = BureauZoneSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user = self.request.user

        qs = (
            BureauZone.objects
            .select_related("region")
            .annotate(
                bureaux_count=Count("bureaux")
            )
            .filter(actif=True)
        )

        if _est_coordinateur(user):
            return qs

        if _est_national_general(user):
            return qs

        # Bureau national spécialisé :
        # consultation uniquement
        if user.role in (
            Role.SUPERADMIN_INTL,
            Role.SUPERADMIN_NATIONAL,
        ):
            return qs

        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user

        if (
            _est_coordinateur(user)
            or _est_national_general(user)
        ):
            serializer.save()
            return

        raise PermissionDenied(
            "Seul le Coordinateur ou le Bureau national "
            "général peut créer une zone."
        )

    def perform_update(self, serializer):
        user = self.request.user

        if (
            _est_coordinateur(user)
            or _est_national_general(user)
        ):
            serializer.save()
            return

        raise PermissionDenied(
            "Vous ne pouvez pas modifier cette zone."
        )

    def perform_destroy(self, instance):
        user = self.request.user

        if not _est_coordinateur(user):
            raise PermissionDenied(
                "Seul le Coordinateur peut supprimer une zone."
            )

        if instance.bureaux.exists():
            raise PermissionDenied(
                "Cette zone contient encore des bureaux zonaux."
            )

        instance.delete()


# ============================================================
# BUREAUX ZONAUX
# ============================================================

class BureauZonalViewSet(viewsets.ModelViewSet):
    """
    Gestion des bureaux zonaux.

    Un bureau zonal appartient obligatoirement à :

        Bureau national spécialisé
                    ↓
             Bureau zonal
                    ↓
                  Zone
    """

    serializer_class = BureauSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        qs = (
            Bureau.objects
            .select_related(
                "zone",
                "zone__region",
                "bureau_parent",
            )
            .filter(
                niveau=NiveauBureau.ZONAL,
                actif=True,
            )
        )

        # Coordinateur
        if _est_coordinateur(user):
            return qs

        # Bureau national général
        if _est_national_general(user):
            return qs

        # Bureau national spécialisé :
        # uniquement les bureaux zonaux de son bureau parent
        return (
            qs
            .filter(
                bureau_parent__administrateurs__utilisateur=user,
                bureau_parent__administrateurs__actif=True,
            )
            .distinct()
        )

    def perform_create(self, serializer):
        user = self.request.user

        zone = serializer.validated_data.get("zone")

        bureau_parent = serializer.validated_data.get(
            "bureau_parent"
        )

        if not zone:
            raise PermissionDenied(
                "Une zone est obligatoire."
            )

        if not bureau_parent:
            raise PermissionDenied(
                "Le bureau national parent est obligatoire."
            )

        if bureau_parent.niveau != NiveauBureau.NATIONAL:
            raise PermissionDenied(
                "Le bureau parent doit être national."
            )

        if (
            bureau_parent.type_bureau
            not in TYPES_BUREAUX_ZONAUX
        ):
            raise PermissionDenied(
                "Ce bureau national ne possède pas "
                "de bureaux zonaux."
            )

        # Coordinateur
        if _est_coordinateur(user):
            self._creer_bureau(
                serializer,
                bureau_parent,
                zone,
            )
            return

        # Bureau national général
        if _est_national_general(user):
            self._creer_bureau(
                serializer,
                bureau_parent,
                zone,
            )
            return

        # Bureau national spécialisé
        if not a_droit_bureau(
            user,
            bureau_parent,
            "peut_gerer_bureaux_zonaux",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de créer "
                "les bureaux zonaux de ce bureau national."
            )

        self._creer_bureau(
            serializer,
            bureau_parent,
            zone,
        )

    def _creer_bureau(
        self,
        serializer,
        bureau_parent,
        zone,
    ):
        noms = {
            TypeBureau.HOMMES:
                "Bureau zonal des hommes",

            TypeBureau.FEMMES:
                "Bureau zonal des femmes",

            TypeBureau.JEUNESSE:
                "Bureau zonal des jeunes",

            TypeBureau.ENFANTS:
                "Bureau zonal des enfants",
        }

        nom_base = noms.get(
            bureau_parent.type_bureau,
            "Bureau zonal",
        )

        nom = f"{nom_base} — {zone.nom}"

        serializer.save(
            nom=nom,
            niveau=NiveauBureau.ZONAL,
            type_bureau=bureau_parent.type_bureau,
            bureau_parent=bureau_parent,
            zone=zone,
        )

    def perform_update(self, serializer):
        user = self.request.user
        bureau = self.get_object()

        if _est_coordinateur(user):
            serializer.save(
                niveau=NiveauBureau.ZONAL,
                type_bureau=bureau.type_bureau,
                bureau_parent=bureau.bureau_parent,
                zone=bureau.zone,
                nom=bureau.nom,
            )
            return

        if not a_droit_bureau(
            user,
            bureau.bureau_parent,
            "peut_gerer_bureaux_zonaux",
        ):
            raise PermissionDenied(
                "Vous ne pouvez pas modifier "
                "ce bureau zonal."
            )

        serializer.save(
            niveau=NiveauBureau.ZONAL,
            type_bureau=bureau.type_bureau,
            bureau_parent=bureau.bureau_parent,
            zone=bureau.zone,
            nom=bureau.nom,
        )

    def perform_destroy(self, instance):
        user = self.request.user

        if _est_coordinateur(user):
            instance.delete()
            return

        if not a_droit_bureau(
            user,
            instance.bureau_parent,
            "peut_gerer_bureaux_zonaux",
        ):
            raise PermissionDenied(
                "Vous ne pouvez pas supprimer "
                "ce bureau zonal."
            )

        instance.delete()


# ============================================================
# MANDATS DES MEMBRES
# ============================================================

class BureauMembreMandatViewSet(viewsets.ModelViewSet):
    serializer_class = BureauMembreMandatSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
    ]

    filterset_fields = [
        "bureau",
        "annee",
        "actif",
        "utilisateur",
    ]

    search_fields = [
        "utilisateur__identifiant",
        "utilisateur__nom",
        "utilisateur__prenom",
        "poste",
    ]

    def get_queryset(self):
        user = self.request.user

        qs = (
            BureauMembreMandat.objects
            .select_related(
                "bureau",
                "bureau__eglise",
                "utilisateur",
            )
            .filter(actif=True)
        )

        if (
            _est_coordinateur(user)
            or _est_national_general(user)
        ):
            return qs

        if user.role in ROLES_BUREAU_NATIONAL:
            return (
                qs
                .filter(
                    bureau__administrateurs__utilisateur=user,
                    bureau__administrateurs__actif=True,
                )
                .distinct()
            )

        if (
            user.role in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            )
            and user.eglise_id
        ):
            return (
                qs
                .filter(
                    Q(
                        bureau__niveau=NiveauBureau.NATIONAL
                    )
                    |
                    Q(
                        bureau__niveau=NiveauBureau.LOCAL,
                        bureau__eglise_id=user.eglise_id,
                    )
                )
                .distinct()
            )

        # Membre simple :
        # annuaire national uniquement
        return qs.filter(
            bureau__niveau=NiveauBureau.NATIONAL
        )

    def perform_create(self, serializer):
        bureau = serializer.validated_data["bureau"]

        if not a_droit_bureau(
            self.request.user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de gérer "
                "la composition de ce bureau."
            )

        serializer.save()

    def perform_update(self, serializer):
        bureau = self.get_object().bureau

        if not a_droit_bureau(
            self.request.user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de modifier "
                "ce mandat."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if not a_droit_bureau(
            self.request.user,
            instance.bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de supprimer "
                "ce mandat."
            )

        instance.delete()


# ============================================================
# ADMINISTRATEURS DE BUREAUX
# ============================================================

class BureauAdministrateurViewSet(viewsets.ModelViewSet):
    serializer_class = BureauAdministrateurSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
    ]

    filterset_fields = [
        "bureau",
        "actif",
    ]

    def get_queryset(self):
        user = self.request.user

        qs = (
            BureauAdministrateur.objects
            .select_related(
                "bureau",
                "bureau__eglise",
                "utilisateur",
            )
        )

        if _est_coordinateur(user):
            return qs

        if _est_national_general(user):
            return qs.filter(
                bureau__niveau=NiveauBureau.NATIONAL
            )

        if user.role in ROLES_BUREAU_NATIONAL:
            return (
                qs
                .filter(
                    bureau__administrateurs__utilisateur=user,
                    bureau__administrateurs__actif=True,
                )
                .distinct()
            )

        if (
            user.role in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            )
            and user.eglise_id
        ):
            return qs.filter(
                bureau__niveau=NiveauBureau.LOCAL,
                bureau__eglise_id=user.eglise_id,
            )

        return qs.none()

    def perform_create(self, serializer):
        bureau = serializer.validated_data["bureau"]

        if not a_droit_bureau(
            self.request.user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Seul un gestionnaire habilité peut "
                "créer un administrateur de bureau."
            )

        serializer.save()

    def perform_update(self, serializer):
        bureau = self.get_object().bureau

        if not a_droit_bureau(
            self.request.user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de modifier "
                "cet administrateur."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if not a_droit_bureau(
            self.request.user,
            instance.bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de supprimer "
                "cet administrateur."
            )

        instance.delete()


# ============================================================
# MEMBRES INDÉPENDANTS DES BUREAUX
# ============================================================

class BureauMembreIndependantViewSet(viewsets.ModelViewSet):
    serializer_class = BureauMembreIndependantSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
    ]

    filterset_fields = [
        "bureau",
        "annee",
        "actif",
    ]

    def get_queryset(self):
        user = self.request.user

        qs = (
            BureauMembre.objects
            .select_related(
                "bureau",
                "bureau__eglise",
            )
        )

        if (
            _est_coordinateur(user)
            or _est_national_general(user)
        ):
            return qs

        if user.role in ROLES_BUREAU_NATIONAL:
            return (
                qs
                .filter(
                    bureau__administrateurs__utilisateur=user,
                    bureau__administrateurs__actif=True,
                )
                .distinct()
            )

        if (
            user.role in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            )
            and user.eglise_id
        ):
            return qs.filter(
                bureau__niveau=NiveauBureau.LOCAL,
                bureau__eglise_id=user.eglise_id,
            )

        # Membre simple :
        # annuaire national uniquement
        return qs.filter(
            bureau__niveau=NiveauBureau.NATIONAL,
            actif=True,
        )

    def perform_create(self, serializer):
        bureau = serializer.validated_data["bureau"]

        if not a_droit_bureau(
            self.request.user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit d'ajouter "
                "un membre à ce bureau."
            )

        serializer.save()

    def perform_update(self, serializer):
        bureau = self.get_object().bureau

        if not a_droit_bureau(
            self.request.user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de modifier "
                "ce membre."
            )

        serializer.save()

    def perform_destroy(self, instance):
        if not a_droit_bureau(
            self.request.user,
            instance.bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de supprimer "
                "ce membre."
            )

        instance.delete()
