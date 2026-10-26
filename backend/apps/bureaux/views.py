from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from apps.accounts.serializers import CreerUtilisateurSerializer
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
    BureauZoneSerializer,
    BureauMembreSerializer,
    BureauMembreMandatSerializer,
    BureauAdministrateurSerializer,
)

from .serializers_indep import (
    BureauMembreIndependantSerializer,
)
from .access import (
    _est_coordinateur,
    _est_national_general,
    _bureaux_administres,
    a_droit_bureau,
    _bureau_national_hommes,
    peut_creer_bureau_national,
    est_bureau_national_principal,
    est_bureau_national_secondaire,
)


# ============================================================
# CONSTANTES DE STRUCTURE DES BUREAUX
# ============================================================

# Bureau national principal.
#
# HOMMES = Bureau national général = Bureau national principal.
BUREAU_NATIONAL_PRINCIPAL = TypeBureau.HOMMES


# Les trois bureaux nationaux créés sous le Bureau national
# principal des Hommes.
TYPES_BUREAUX_NATIONAUX = {
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
}


# Tous les bureaux nationaux qui peuvent avoir une structure.
# Le bureau Hommes est le principal.
TYPES_BUREAUX_NATIONAUX_TOUS = {
    TypeBureau.HOMMES,
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
}


# Seuls les trois bureaux nationaux secondaires créent
# leurs bureaux zonaux.
#
# IMPORTANT :
# Le Bureau national des Hommes est volontairement absent.
TYPES_BUREAUX_ZONAUX = {
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
}


# ============================================================
# BUREAUX
# ============================================================

class BureauViewSet(viewsets.ModelViewSet):
    serializer_class = BureauSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["niveau", "type_bureau", "eglise", "actif"]
    search_fields = ["nom", "code", "eglise__nom"]

    def get_queryset(self):
        user = self.request.user

        qs = (
            Bureau.objects
            .select_related(
                "eglise",
                "bureau_parent",
                "zone",
            )
            .annotate(
                membres_actifs=Count(
                    "mandats",
                    filter=Q(mandats__actif=True),
                )
            )
        )

        # ========================================================
        # COORDINATEUR
        # ========================================================
        if _est_coordinateur(user):
            return qs

        # ========================================================
        # ADMINISTRATEURS / RESPONSABLES BUREAU NATIONAL
        # ========================================================
        if user.role in ROLES_BUREAU_NATIONAL:
            affectations = BureauAdministrateur.objects.filter(
                utilisateur=user,
                actif=True,
                bureau__actif=True,
            ).values_list("bureau_id", flat=True)

            return qs.filter(
                id__in=affectations
            ).distinct()

        # ========================================================
        # ADMIN LOCAL / PASTEUR
        # ========================================================
        if (
            user.role in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            )
            and user.eglise_id
        ):
            return (
                qs.filter(
                    Q(
                        niveau=NiveauBureau.NATIONAL,
                        actif=True,
                    )
                    |
                    Q(
                        niveau=NiveauBureau.ZONAL,
                        actif=True,
                    )
                    |
                    Q(
                        niveau=NiveauBureau.LOCAL,
                        eglise_id=user.eglise_id,
                        actif=True,
                    )
                )
                .distinct()
            )

        # ========================================================
        # MEMBRE SIMPLE
        # ========================================================
        # Lecture seule de tous les bureaux actifs :
        # NATIONAL + ZONAL + LOCAL
        #
        # IMPORTANT :
        # Le membre pourra consulter les bureaux de différentes
        # structures, mais les méthodes perform_create(),
        # perform_update() et perform_destroy() ci-dessous
        # empêcheront toute modification.
        if user.role == Role.MEMBRE:
            return qs.filter(
                actif=True
            ).distinct()

        # ========================================================
        # AUTRES UTILISATEURS
        # ========================================================
        return qs.filter(
            niveau=NiveauBureau.NATIONAL,
            actif=True,
        )

    def _verifier_ecriture(self, user, bureau=None):
        """
        Les MEMBRES ont uniquement un accès en lecture.
        """

        if user.role == Role.MEMBRE:
            raise PermissionDenied(
                "Votre compte dispose uniquement d'un accès "
                "en lecture aux bureaux."
            )

        if bureau and not _est_coordinateur(user):
            if not a_droit_bureau(
                user,
                bureau,
                "peut_gerer_membres",
            ):
                raise PermissionDenied(
                    "Vous n'avez pas le droit de modifier ce bureau."
                )

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == Role.MEMBRE:
            raise PermissionDenied(
                "Un membre ne peut pas créer de bureau."
            )

        data = serializer.validated_data

        niveau = data.get(
            "niveau",
            NiveauBureau.NATIONAL,
        )
        type_bureau = data.get(
            "type_bureau",
            TypeBureau.AUTRE,
        )
        eglise = data.get("eglise")

        # --------------------------------------------------------
        # BUREAU NATIONAL
        # --------------------------------------------------------
        if niveau == NiveauBureau.NATIONAL:

            if not _est_coordinateur(user):
                raise PermissionDenied(
                    "Seul le Coordinateur peut créer un bureau national."
                )

            if eglise is not None:
                raise PermissionDenied(
                    "Un bureau national ne peut pas être rattaché "
                    "à une église."
                )

            if type_bureau not in TYPES_BUREAUX_NATIONAUX_TOUS:
                raise PermissionDenied(
                    "Type de bureau national invalide."
                )

            if Bureau.objects.filter(
                niveau=NiveauBureau.NATIONAL,
                type_bureau=type_bureau,
                eglise__isnull=True,
            ).exists():
                raise PermissionDenied(
                    "Ce bureau national existe déjà."
                )

            if type_bureau == TypeBureau.HOMMES:
                serializer.save(
                    niveau=NiveauBureau.NATIONAL,
                    type_bureau=TypeBureau.HOMMES,
                    eglise=None,
                    bureau_parent=None,
                )
                return

            bureau_hommes = _bureau_national_hommes()

            if bureau_hommes is None:
                raise PermissionDenied(
                    "Créez d'abord le Bureau national des Hommes."
                )

            serializer.save(
                niveau=NiveauBureau.NATIONAL,
                type_bureau=type_bureau,
                eglise=None,
                bureau_parent=bureau_hommes,
            )
            return

        # --------------------------------------------------------
        # BUREAU ZONAL
        # --------------------------------------------------------
        if niveau == NiveauBureau.ZONAL:

            if not _est_coordinateur(user):
                raise PermissionDenied(
                    "Seul le Coordinateur peut créer un bureau zonal."
                )

            bureau_parent = data.get("bureau_parent")
            zone = data.get("zone")

            if not bureau_parent:
                raise PermissionDenied(
                    "Un bureau zonal doit avoir un bureau national parent."
                )

            if bureau_parent.niveau != NiveauBureau.NATIONAL:
                raise PermissionDenied(
                    "Le bureau parent doit être national."
                )

            if bureau_parent.type_bureau not in TYPES_BUREAUX_ZONAUX:
                raise PermissionDenied(
                    "Ce bureau national ne peut pas créer "
                    "de bureaux zonaux."
                )

            if not zone:
                raise PermissionDenied(
                    "Une zone géographique est obligatoire."
                )

            serializer.save(
                niveau=NiveauBureau.ZONAL,
                bureau_parent=bureau_parent,
                eglise=None,
            )
            return

        # --------------------------------------------------------
        # BUREAU LOCAL
        # --------------------------------------------------------
        if niveau == NiveauBureau.LOCAL:

            if user.role not in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            ) and not _est_coordinateur(user):
                raise PermissionDenied(
                    "Vous ne pouvez pas créer ce bureau local."
                )

            if _est_coordinateur(user):
                if not eglise:
                    raise PermissionDenied(
                        "Un bureau local doit être rattaché à une église."
                    )

                serializer.save()
                return

            if not user.eglise_id:
                raise PermissionDenied(
                    "Votre compte n'est lié à aucune église."
                )

            serializer.save(
                eglise=user.eglise
            )
            return

        raise PermissionDenied(
            "Niveau de bureau invalide."
        )

    def perform_update(self, serializer):
        user = self.request.user
        bureau = self.get_object()

        # MEMBRE = lecture uniquement
        if user.role == Role.MEMBRE:
            raise PermissionDenied(
                "Vous pouvez consulter les bureaux, "
                "mais vous ne pouvez pas les modifier."
            )

        # Coordinateur
        if _est_coordinateur(user):
            serializer.save(
                niveau=bureau.niveau,
                type_bureau=bureau.type_bureau,
                eglise=bureau.eglise,
                bureau_parent=bureau.bureau_parent,
            )
            return

        # Gestionnaire habilité
        if not a_droit_bureau(
            user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous ne pouvez pas modifier ce bureau."
            )

        serializer.save(
            niveau=bureau.niveau,
            type_bureau=bureau.type_bureau,
            eglise=bureau.eglise,
            bureau_parent=bureau.bureau_parent,
        )

    def perform_destroy(self, instance):
        user = self.request.user

        # MEMBRE = lecture uniquement
        if user.role == Role.MEMBRE:
            raise PermissionDenied(
                "Vous pouvez consulter les bureaux, "
                "mais vous ne pouvez pas les supprimer."
            )

        if instance.niveau == NiveauBureau.NATIONAL:
            if not _est_coordinateur(user):
                raise PermissionDenied(
                    "Seul le Coordinateur peut supprimer "
                    "un bureau national."
                )

            instance.delete()
            return

        if _est_coordinateur(user):
            instance.delete()
            return

        if not a_droit_bureau(
            user,
            instance,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous ne pouvez pas supprimer ce bureau."
            )

        instance.delete()

# ============================================================
# MANDATS DES BUREAUX
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
                "bureau__zone",
                "bureau__bureau_parent",
                "utilisateur",
            )
            .filter(actif=True)
        )

        # ========================================================
        # COORDINATEUR / BUREAU NATIONAL GENERAL
        # ========================================================
        if (
            _est_coordinateur(user)
            or _est_national_general(user)
        ):
            return qs

        # ========================================================
        # ADMINISTRATEURS BUREAU NATIONAL
        # ========================================================
        if user.role in ROLES_BUREAU_NATIONAL:
            return (
                qs.filter(
                    bureau__administrateurs__utilisateur=user,
                    bureau__administrateurs__actif=True,
                )
                .distinct()
            )

        # ========================================================
        # ADMIN LOCAL / PASTEUR
        # ========================================================
        if (
            user.role in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            )
            and user.eglise_id
        ):
            return (
                qs.filter(
                    Q(
                        bureau__niveau=NiveauBureau.NATIONAL
                    )
                    |
                    Q(
                        bureau__niveau=NiveauBureau.ZONAL
                    )
                    |
                    Q(
                        bureau__niveau=NiveauBureau.LOCAL,
                        bureau__eglise_id=user.eglise_id,
                    )
                )
                .distinct()
            )

        # ========================================================
        # MEMBRE SIMPLE
        # ========================================================
        # Lecture de tous les mandats actifs de tous les bureaux.
        if user.role == Role.MEMBRE:
            return qs.filter(
                bureau__actif=True,
                actif=True,
            ).distinct()

        return qs.none()

    def _verifier_gestion(self, bureau):

        user = self.request.user

        # Un MEMBRE ne peut jamais gérer.
        if user.role == Role.MEMBRE:
            raise PermissionDenied(
                "Vous disposez uniquement d'un accès "
                "en lecture aux membres des bureaux."
            )

        if not bureau:
            raise PermissionDenied(
                "Bureau introuvable."
            )

        if _est_coordinateur(user):
            return

        if not a_droit_bureau(
            user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de gérer "
                "la composition de ce bureau."
            )

    def perform_create(self, serializer):

        bureau = serializer.validated_data["bureau"]

        self._verifier_gestion(bureau)

        serializer.save()

    def perform_update(self, serializer):

        bureau = self.get_object().bureau

        self._verifier_gestion(bureau)

        serializer.save()

    def perform_destroy(self, instance):

        self._verifier_gestion(instance.bureau)

        instance.delete()


# ============================================================
# ADMINISTRATEURS DES BUREAUX
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
                qs.filter(
                    bureau__administrateurs__utilisateur=user,
                    bureau__administrateurs__actif=True,
                )
                .distinct()
            )

        if (
            user.role in [
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            ]
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


# ============================================================
# MEMBRES INDÉPENDANTS DES BUREAUX
# ============================================================

class BureauMembreIndependantViewSet(viewsets.ModelViewSet):

    serializer_class = BureauMembreIndependantSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
    ]

    filterset_fields = [
        "bureau",
        "annee",
        "actif",
    ]

    search_fields = [
        "nom_complet",
        "poste",
        "bureau__nom",
        "bureau__code",
    ]

    def get_queryset(self):

        user = self.request.user

        qs = (
            BureauMembre.objects
            .select_related(
                "bureau",
                "bureau__eglise",
                "bureau__zone",
                "bureau__bureau_parent",
            )
            .filter(
                actif=True,
                bureau__actif=True,
            )
        )

        # ========================================================
        # COORDINATEUR
        # ========================================================
        if _est_coordinateur(user):
            return qs

        # ========================================================
        # BUREAU NATIONAL
        # ========================================================
        if user.role in ROLES_BUREAU_NATIONAL:
            return (
                qs.filter(
                    bureau__administrateurs__utilisateur=user,
                    bureau__administrateurs__actif=True,
                )
                .distinct()
            )

        # ========================================================
        # ADMIN LOCAL / PASTEUR
        # ========================================================
        if (
            user.role in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            )
            and user.eglise_id
        ):
            return (
                qs.filter(
                    Q(
                        bureau__niveau=NiveauBureau.NATIONAL
                    )
                    |
                    Q(
                        bureau__niveau=NiveauBureau.ZONAL
                    )
                    |
                    Q(
                        bureau__niveau=NiveauBureau.LOCAL,
                        bureau__eglise_id=user.eglise_id,
                    )
                )
                .distinct()
            )

        # ========================================================
        # MEMBRE SIMPLE
        # ========================================================
        # Le membre peut consulter les membres des différents
        # bureaux sans disposer d'aucun droit de gestion.
        if user.role == Role.MEMBRE:
            return (
                qs.filter(
                    actif=True,
                    bureau__actif=True,
                )
                .distinct()
            )

        return qs.none()

    def _verifier_gestion(self, bureau):

        user = self.request.user

        # MEMBRE = lecture uniquement
        if user.role == Role.MEMBRE:
            raise PermissionDenied(
                "Vous pouvez consulter les membres des bureaux, "
                "mais vous ne pouvez pas les modifier."
            )

        if not bureau:
            raise PermissionDenied(
                "Bureau introuvable."
            )

        if _est_coordinateur(user):
            return

        if not a_droit_bureau(
            user,
            bureau,
            "peut_gerer_membres",
        ):
            raise PermissionDenied(
                "Vous n'avez pas le droit de gérer "
                "les membres de ce bureau."
            )

    def perform_create(self, serializer):

        bureau = serializer.validated_data.get("bureau")

        self._verifier_gestion(bureau)

        serializer.save()

    def perform_update(self, serializer):

        bureau = self.get_object().bureau

        self._verifier_gestion(bureau)

        serializer.save()

    def perform_destroy(self, instance):

        self._verifier_gestion(instance.bureau)

        instance.delete()

# ============================================================
# ZONES GÉOGRAPHIQUES
# ============================================================

class BureauZoneViewSet(viewsets.ModelViewSet):
    """
    Gestion des zones géographiques.

    Création / modification :
        - Coordinateur
        - Bureau national général

    Suppression :
        - Coordinateur uniquement
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

        # Les bureaux nationaux spécialisés peuvent consulter
        # les zones existantes.
        if user.role in ROLES_BUREAU_NATIONAL:
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

    Structure :

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

        if _est_coordinateur(user):
            return qs

        if _est_national_general(user):
            return qs

        # Bureau national spécialisé :
        # uniquement ses propres bureaux zonaux.
        if user.role in ROLES_BUREAU_NATIONAL:
            return (
                qs
                .filter(
                    bureau_parent__administrateurs__utilisateur=user,
                    bureau_parent__administrateurs__actif=True,
                )
                .distinct()
            )

        return qs.none()

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

        if bureau_parent.type_bureau not in TYPES_BUREAUX_ZONAUX:
            raise PermissionDenied(
                "Ce bureau national ne possède pas "
                "de bureaux zonaux."
            )

        if _est_coordinateur(user):
            self._creer_bureau(
                serializer,
                bureau_parent,
                zone,
            )
            return

        if _est_national_general(user):
            self._creer_bureau(
                serializer,
                bureau_parent,
                zone,
            )
            return

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
            TypeBureau.HOMMES: "Bureau zonal des hommes",
            TypeBureau.FEMMES: "Bureau zonal des femmes",
            TypeBureau.JEUNESSE: "Bureau zonal des jeunes",
            TypeBureau.ENFANTS: "Bureau zonal des enfants",
        }

        nom_base = noms.get(
            bureau_parent.type_bureau,
            "Bureau zonal",
        )

        serializer.save(
            nom=f"{nom_base} — {zone.nom}",
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
                "Vous ne pouvez pas modifier ce bureau zonal."
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
                "Vous ne pouvez pas supprimer ce bureau zonal."
            )

        instance.delete()
