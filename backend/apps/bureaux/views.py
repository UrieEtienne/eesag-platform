from django.db.models import Count, Q

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

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

from .access import (
    _est_coordinateur,
    _est_national_general,
    _bureaux_administres,
    a_droit_bureau,
    _bureau_national_hommes,
    _est_national_general,
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

    # ========================================================
    # QUERYSET
    # ========================================================

    def get_queryset(self):
        user = self.request.user

        qs = (
            Bureau.objects
            .select_related(
                "eglise",
                "bureau_parent",
            )
            .annotate(
                membres_actifs=Count(
                    "mandats",
                    filter=Q(
                        mandats__actif=True
                    ),
                )
            )
        )

        # --------------------------------------------------------
        # COORDINATEUR
        # --------------------------------------------------------

        if _est_coordinateur(user):
            return qs

        # --------------------------------------------------------
        # ADMINISTRATEUR D'UN BUREAU
        # --------------------------------------------------------

        bureaux_administres = _bureaux_administres(user)

        if bureaux_administres.exists():
            return (
                qs.filter(
                    Q(
                        id__in=bureaux_administres.values("id")
                    )
                    |
                    Q(
                        niveau=NiveauBureau.NATIONAL,
                        actif=True,
                    )
                )
                .distinct()
            )

        # --------------------------------------------------------
        # ADMIN LOCAL / PASTEUR
        # --------------------------------------------------------

        if (
            user.eglise_id
            and user.role in [
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            ]
        ):
            return (
                qs.filter(
                    Q(
                        niveau=NiveauBureau.NATIONAL,
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

        # --------------------------------------------------------
        # MEMBRE
        # --------------------------------------------------------

        return qs.filter(
            niveau=NiveauBureau.NATIONAL,
            actif=True,
        )

    # ========================================================
    # CRÉATION D'UN BUREAU
    # ========================================================

    def perform_create(self, serializer):
        user = self.request.user

        niveau = serializer.validated_data.get(
            "niveau",
            NiveauBureau.NATIONAL,
        )

        type_bureau = serializer.validated_data.get(
            "type_bureau",
            TypeBureau.AUTRE,
        )

        eglise = serializer.validated_data.get("eglise")

        bureau_parent = serializer.validated_data.get(
            "bureau_parent"
        )

        # ========================================================
        # COORDINATEUR
        # ========================================================

        if _est_coordinateur(user):

            # ----------------------------------------------------
            # CRÉATION D'UN BUREAU NATIONAL
            # ----------------------------------------------------

            if niveau == NiveauBureau.NATIONAL:

                if eglise is not None:
                    raise PermissionDenied(
                        "Un bureau national ne peut pas être "
                        "rattaché à une église."
                    )

                if type_bureau not in TYPES_BUREAUX_NATIONAUX_TOUS:
                    raise PermissionDenied(
                        "Type de bureau national non autorisé."
                    )

                # ------------------------------------------------
                # BUREAU NATIONAL DES HOMMES
                # ------------------------------------------------

                if type_bureau == TypeBureau.HOMMES:

                    if Bureau.objects.filter(
                        niveau=NiveauBureau.NATIONAL,
                        type_bureau=TypeBureau.HOMMES,
                        eglise__isnull=True,
                    ).exists():
                        raise PermissionDenied(
                            "Le Bureau national des Hommes existe "
                            "déjà."
                        )

                    serializer.save(
                        niveau=NiveauBureau.NATIONAL,
                        type_bureau=TypeBureau.HOMMES,
                        eglise=None,
                        bureau_parent=None,
                    )
                    return

                # ------------------------------------------------
                # BUREAUX NATIONAUX SECONDAIRES
                # ------------------------------------------------

                if type_bureau in TYPES_BUREAUX_NATIONAUX:

                    bureau_hommes = _bureau_national_hommes()

                    if not bureau_hommes:
                        raise PermissionDenied(
                            "Le Bureau national des Hommes doit "
                            "être créé avant les bureaux nationaux "
                            "Femmes, Jeunesse et Enfants."
                        )

                    if Bureau.objects.filter(
                        niveau=NiveauBureau.NATIONAL,
                        type_bureau=type_bureau,
                        eglise__isnull=True,
                    ).exists():
                        raise PermissionDenied(
                            "Ce bureau national existe déjà."
                        )

                    serializer.save(
                        niveau=NiveauBureau.NATIONAL,
                        type_bureau=type_bureau,
                        eglise=None,
                        bureau_parent=bureau_hommes,
                    )
                    return

                raise PermissionDenied(
                    "Type de bureau national invalide."
                )

            # ----------------------------------------------------
            # CRÉATION D'UN BUREAU ZONAL
            # ----------------------------------------------------

            if niveau == NiveauBureau.ZONAL:

                if not bureau_parent:
                    raise PermissionDenied(
                        "Un bureau zonal doit avoir un bureau "
                        "national parent."
                    )

                if bureau_parent.niveau != NiveauBureau.NATIONAL:
                    raise PermissionDenied(
                        "Le parent d'un bureau zonal doit être "
                        "un bureau national."
                    )

                if bureau_parent.type_bureau not in TYPES_BUREAUX_ZONAUX:
                    raise PermissionDenied(
                        "Seuls les bureaux nationaux Femmes, "
                        "Jeunesse et Enfants peuvent créer "
                        "des bureaux zonaux."
                    )

                serializer.save(
                    niveau=NiveauBureau.ZONAL,
                    bureau_parent=bureau_parent,
                    eglise=None,
                )
                return

            # ----------------------------------------------------
            # BUREAU LOCAL
            # ----------------------------------------------------

            if niveau == NiveauBureau.LOCAL:

                if not eglise:
                    raise PermissionDenied(
                        "Un bureau local doit être rattaché "
                        "à une église."
                    )

                serializer.save()
                return

            raise PermissionDenied(
                "Niveau de bureau invalide."
            )

        # ========================================================
        # BUREAU NATIONAL PRINCIPAL : HOMMES
        # ========================================================
        #
        # Le responsable du Bureau national des Hommes peut
        # créer les trois bureaux nationaux secondaires.
        #
        # Femmes / Jeunesse / Enfants.
        # ========================================================

        if niveau == NiveauBureau.NATIONAL:

            if type_bureau not in TYPES_BUREAUX_NATIONAUX:
                raise PermissionDenied(
                    "Seul le Bureau national des Hommes peut "
                    "créer les bureaux nationaux Femmes, "
                    "Jeunesse et Enfants."
                )

            bureau_hommes = _bureau_national_hommes()

            if not bureau_hommes:
                raise PermissionDenied(
                    "Le Bureau national des Hommes n'existe pas."
                )

            # Le compte doit avoir les droits de création
            # sur le Bureau national principal.
            if not a_droit_bureau(
                user,
                bureau_hommes,
                "peut_creer_bureaux_nationaux",
            ):
                # Compatibilité avec l'ancien nom de permission
                if not a_droit_bureau(
                    user,
                    bureau_hommes,
                    "peut_creer_bureaux",
                ):
                    raise PermissionDenied(
                        "Vous n'avez pas le droit de créer "
                        "les bureaux nationaux."
                    )

            if eglise is not None:
                raise PermissionDenied(
                    "Un bureau national ne peut pas être "
                    "rattaché à une église."
                )

            if Bureau.objects.filter(
                niveau=NiveauBureau.NATIONAL,
                type_bureau=type_bureau,
                eglise__isnull=True,
            ).exists():
                raise PermissionDenied(
                    "Ce bureau national existe déjà."
                )

            serializer.save(
                niveau=NiveauBureau.NATIONAL,
                type_bureau=type_bureau,
                eglise=None,
                bureau_parent=bureau_hommes,
            )

            return

        # ========================================================
        # BUREAU ZONAL
        # ========================================================

        if niveau == NiveauBureau.ZONAL:

            if not bureau_parent:
                raise PermissionDenied(
                    "Un bureau zonal doit avoir un bureau "
                    "national parent."
                )

            if bureau_parent.niveau != NiveauBureau.NATIONAL:
                raise PermissionDenied(
                    "Le bureau parent doit être national."
                )

            # Le Bureau Hommes principal ne crée PAS les
            # bureaux zonaux dans cette organisation.
            if bureau_parent.type_bureau not in TYPES_BUREAUX_ZONAUX:
                raise PermissionDenied(
                    "Seuls les bureaux nationaux Femmes, "
                    "Jeunesse et Enfants peuvent créer "
                    "leurs bureaux zonaux."
                )

            if not a_droit_bureau(
                user,
                bureau_parent,
                "peut_gerer_bureaux_zonaux",
            ):
                raise PermissionDenied(
                    "Vous n'avez pas le droit de créer "
                    "les bureaux zonaux de ce bureau national."
                )

            serializer.save(
                niveau=NiveauBureau.ZONAL,
                bureau_parent=bureau_parent,
                eglise=None,
            )

            return

        # ========================================================
        # BUREAU LOCAL
        # ========================================================

        if (
            user.role in (
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            )
            and user.eglise_id
        ):

            if niveau != NiveauBureau.LOCAL:
                raise PermissionDenied(
                    "Un administrateur d'église ne peut créer "
                    "qu'un bureau local."
                )

            serializer.save(
                niveau=NiveauBureau.LOCAL,
                eglise=user.eglise,
            )

            return

        raise PermissionDenied(
            "Vous ne pouvez pas créer ce bureau."
        )

        # ========================================================
        # MODIFICATION
        # ========================================================

        def perform_update(self, serializer):
            user = self.request.user
            bureau = self.get_object()

            # --------------------------------------------------------
            # COORDINATEUR
            # --------------------------------------------------------

            if _est_coordinateur(user):
                serializer.save(
                    niveau=bureau.niveau,
                    eglise=bureau.eglise,
                    type_bureau=bureau.type_bureau,
                )
                return

            # --------------------------------------------------------
            # ADMINISTRATEUR DU BUREAU
            # --------------------------------------------------------

            if not a_droit_bureau(
                user,
                bureau,
                "peut_gerer_membres",
            ):
                raise PermissionDenied(
                    "Vous ne pouvez pas modifier ce bureau."
                )

            # --------------------------------------------------------
            # PROTECTION DE LA STRUCTURE
            # --------------------------------------------------------

            serializer.save(
                niveau=bureau.niveau,
                eglise=bureau.eglise,
                type_bureau=bureau.type_bureau,
                bureau_parent=bureau.bureau_parent,
            )

        # ========================================================
        # SUPPRESSION
        # ========================================================

        def perform_destroy(self, instance):
            user = self.request.user

            # --------------------------------------------------------
            # COORDINATEUR
            # --------------------------------------------------------

            if _est_coordinateur(user):
                instance.delete()
                return

            # --------------------------------------------------------
            # BUREAU HOMMES
            # --------------------------------------------------------

            if est_bureau_national_principal(instance):
                raise PermissionDenied(
                    "Le Bureau national des hommes ne peut pas "
                    "être supprimé depuis cet espace."
                )

            # --------------------------------------------------------
            # AUTRES BUREAUX NATIONAUX
            # --------------------------------------------------------

            if est_bureau_national_secondaire(instance):

                if not a_droit_bureau(
                    user,
                    _bureau_national_hommes(),
                    "peut_creer_bureaux",
                ):
                    raise PermissionDenied(
                        "Vous ne pouvez pas supprimer ce bureau national."
                    )

                instance.delete()
                return

            # --------------------------------------------------------
            # BUREAU LOCAL
            # --------------------------------------------------------

            if not a_droit_bureau(
                user,
                instance,
                "peut_gerer_membres",
            ):
                raise PermissionDenied(
                    "Vous ne pouvez pas supprimer ce bureau."
                )

            instance.delete()

        # ========================================================
        # CRÉATION INITIALE DU BUREAU NATIONAL
        # ========================================================

        @action(
            detail=False,
            methods=["post"],
            url_path="creer-bureau-national",
        )
        def creer_bureau_national(self, request):
            """
            Création initiale du Bureau national.

            Cette opération est réservée exclusivement
            au Coordinateur.

            Un seul Bureau national général peut exister.
            """

            user = request.user

            # ----------------------------------------------------
            # 1. VÉRIFICATION DU COORDINATEUR
            # ----------------------------------------------------

            if not _est_coordinateur(user):
                raise PermissionDenied(
                    "Seul le Coordinateur peut créer le Bureau national."
                )

            # ----------------------------------------------------
            # 2. VÉRIFIER S'IL EXISTE DÉJÀ
            # ----------------------------------------------------

            bureau_existant = _bureau_national_general()

            if bureau_existant:
                return Response(
                    {
                        "detail": "Le Bureau national existe déjà.",
                        "existe": True,
                        "modifiable": False,
                        "bureau": BureauSerializer(
                            bureau_existant,
                            context={"request": request},
                        ).data,
                    },
                    status=400,
                )

            # ----------------------------------------------------
            # 3. RÉCUPÉRER LES DONNÉES
            # ----------------------------------------------------

            nom = str(
                request.data.get("nom")
                or "Bureau national"
            ).strip()

            description = str(
                request.data.get("description")
                or ""
            ).strip()

            if not nom:
                raise PermissionDenied(
                    "Le nom du Bureau national est obligatoire."
                )

            # ----------------------------------------------------
            # 4. DOUBLE PROTECTION CONTRE LES DOUBLONS
            # ----------------------------------------------------

            deja_existant = Bureau.objects.filter(
                niveau=NiveauBureau.NATIONAL,
                type_bureau=TypeBureau.AUTRE,
                eglise__isnull=True,
            ).exists()

            if deja_existant:
                raise PermissionDenied(
                    "Un Bureau national général existe déjà."
                )

            # ----------------------------------------------------
            # 5. CRÉATION
            # ----------------------------------------------------

            bureau = Bureau.objects.create(
                nom=nom,
                niveau=NiveauBureau.NATIONAL,
                type_bureau=TypeBureau.AUTRE,
                eglise=None,
                description=description,
                actif=True,
            )

            # ----------------------------------------------------
            # 6. RÉPONSE
            # ----------------------------------------------------

            return Response(
                {
                    "detail": (
                        "Le Bureau national a été créé "
                        "avec succès."
                    ),
                    "existe": True,
                    "modifiable": False,
                    "bureau": BureauSerializer(
                        bureau,
                        context={"request": request},
                    ).data,
                },
                status=201,
            )

        # ========================================================
        # MES BUREAUX
        # ========================================================

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

        # ========================================================
        # MEMBRES CANDIDATS
        # ========================================================

        @action(
            detail=False,
            methods=["get"],
            url_path="membres-candidats",
        )
        def membres_candidats(self, request):

            bureau_id = request.query_params.get("bureau")

            if not bureau_id:
                raise PermissionDenied(
                    "Le bureau est obligatoire."
                )

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
            from django.utils import timezone

            current_year = timezone.now().year

            base = (
                Utilisateur.objects
                .filter(actif=True)
                .exclude(role=Role.COORDINATEUR)
            )

            # ----------------------------------------------------
            # BUREAU NATIONAL
            # ----------------------------------------------------

            if bureau.niveau == NiveauBureau.NATIONAL:
                base = base.filter(
                    eglise__isnull=True
                )

            # ----------------------------------------------------
            # BUREAU LOCAL
            # ----------------------------------------------------

            else:
                base = base.filter(
                    eglise_id=bureau.eglise_id
                )

            # ----------------------------------------------------
            # EXCLURE LES PERSONNES DÉJÀ NOMMÉES
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # RÉPONSE
            # ----------------------------------------------------

            return Response(
                [
                    {
                        "id": utilisateur.id,
                        "identifiant": utilisateur.identifiant,
                        "nom_complet": (
                            f"{utilisateur.prenom} "
                            f"{utilisateur.nom}"
                        ),
                        "photo": (
                            utilisateur.photo.url
                            if utilisateur.photo
                            else None
                        ),
                        "telephone": utilisateur.telephone,
                    }
                    for utilisateur in base[:500]
                ]
            )


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
                "utilisateur",
            )
            .filter(actif=True)
        )

        if _est_coordinateur(user) or _est_national_general(user):
            return qs

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
            return (
                qs.filter(
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
            .select_related("bureau", "bureau__eglise")
            .filter(actif=True)
        )

        # --------------------------------------------------------
        # COORDINATEUR
        # --------------------------------------------------------
        if _est_coordinateur(user):
            return qs

        # --------------------------------------------------------
        # BUREAU NATIONAL
        # --------------------------------------------------------
        if user.role in ROLES_BUREAU_NATIONAL:
            return qs.filter(
                bureau__administrateurs__utilisateur=user,
                bureau__administrateurs__actif=True,
            ).distinct()

        # --------------------------------------------------------
        # ADMIN LOCAL / PASTEUR
        # --------------------------------------------------------
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

        # --------------------------------------------------------
        # MEMBRE SIMPLE
        # --------------------------------------------------------
        # Lecture publique des compositions nationales.
        return qs.filter(
            bureau__niveau=NiveauBureau.NATIONAL,
            actif=True,
        )

    def _verifier_gestion(self, bureau):
        user = self.request.user

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
