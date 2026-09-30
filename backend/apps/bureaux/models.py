from django.core.exceptions import ValidationError
from django.db import models


# ============================================================
# NIVEAUX DES BUREAUX
# ============================================================

class NiveauBureau(models.TextChoices):
    NATIONAL = "NATIONAL", "Bureau national"
    ZONAL = "ZONAL", "Bureau zonal"
    LOCAL = "LOCAL", "Bureau d'église"


# ============================================================
# TYPES DE BUREAUX
# ============================================================

class TypeBureau(models.TextChoices):
    GENERAL = "GENERAL", "Bureau national général"
    FEMMES = "FEMMES", "Bureau national des femmes"
    JEUNESSE = "JEUNESSE", "Bureau national de la jeunesse"
    ENFANTS = "ENFANTS", "Bureau national des enfants"
    EVANGELISATION = "EVANGELISATION", "Équipe nationale d'évangélisation"
    HOMMES = "HOMMES", "Bureau national des hommes"
    COMMUNICATION = "COMMUNICATION", "Bureau de la communication"
    MUSIQUE = "MUSIQUE", "Bureau de la musique / chorale"
    MISSIONS = "MISSIONS", "Bureau des missions"
    AUTRE = "AUTRE", "Autre bureau / commission"


# ============================================================
# ZONES GÉOGRAPHIQUES
# ============================================================

class BureauZone(models.Model):
    """
    Zone géographique utilisée pour organiser les bureaux zonaux.

    Une zone appartient à une région administrative.
    Plusieurs bureaux zonaux peuvent être rattachés à une même zone.
    """

    nom = models.CharField(
        max_length=180,
        unique=True,
    )

    code = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
    )

    region = models.ForeignKey(
        "geo.Region",
        on_delete=models.PROTECT,
        related_name="zones_bureaux",
    )

    description = models.TextField(
        blank=True,
    )

    actif = models.BooleanField(
        default=True,
    )

    date_creation = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "region__nom",
            "nom",
        ]

    def clean(self):
        if not self.nom:
            raise ValidationError({
                "nom": "Le nom de la zone est obligatoire."
            })

        if not self.region_id:
            raise ValidationError({
                "region": "La région est obligatoire."
            })

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.code:
            base = f"ZONE-{self.region.code}-{self.nom}"

            # Nettoyage du code
            code_base = (
                base.upper()
                .replace(" ", "-")
            )[:34]

            code = code_base

            if BureauZone.objects.exclude(pk=self.pk).filter(
                code=code
            ).exists():
                i = 2

                while BureauZone.objects.exclude(
                    pk=self.pk
                ).filter(
                    code=f"{code_base[:35]}-{i}"[:40]
                ).exists():
                    i += 1

                code = f"{code_base[:35]}-{i}"[:40]

            self.code = code

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} · {self.region.nom}"


# ============================================================
# BUREAUX
# ============================================================

class Bureau(models.Model):
    """
    Espace de gouvernance indépendant :
    - national
    - zonal
    - local à une église
    """

    nom = models.CharField(
        max_length=180,
    )

    code = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
    )

    niveau = models.CharField(
        max_length=20,
        choices=NiveauBureau.choices,
        default=NiveauBureau.NATIONAL,
    )

    type_bureau = models.CharField(
        max_length=30,
        choices=TypeBureau.choices,
        default=TypeBureau.AUTRE,
    )

    eglise = models.ForeignKey(
        "churches.Eglise",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="bureaux",
    )

    # --------------------------------------------------------
    # ZONE GÉOGRAPHIQUE
    # --------------------------------------------------------

    zone = models.ForeignKey(
        BureauZone,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="bureaux",
    )

    # --------------------------------------------------------
    # BUREAU NATIONAL PARENT
    # --------------------------------------------------------

    bureau_parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="bureaux_zonaux",
        limit_choices_to={
            "niveau": NiveauBureau.NATIONAL,
        },
    )

    description = models.TextField(
        blank=True,
    )

    actif = models.BooleanField(
        default=True,
    )

    date_creation = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "niveau",
            "nom",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "niveau",
                    "type_bureau",
                    "eglise",
                ],
                name="uniq_bureau_type_niveau_eglise",
            ),

            models.UniqueConstraint(
                fields=[
                    "type_bureau",
                ],
                condition=models.Q(
                    niveau=NiveauBureau.NATIONAL,
                    type_bureau=TypeBureau.GENERAL,
                    eglise__isnull=True,
                ),
                name="uniq_bureau_national_general",
            ),
        ]

    def clean(self):
        # ----------------------------------------------------
        # BUREAU NATIONAL
        # ----------------------------------------------------

        if (
            self.niveau == NiveauBureau.NATIONAL
            and self.eglise_id
        ):
            raise ValidationError({
                "eglise": (
                    "Un bureau national ne peut pas "
                    "être lié à une église."
                )
            })

        if (
            self.niveau == NiveauBureau.NATIONAL
            and self.zone_id
        ):
            raise ValidationError({
                "zone": (
                    "Un bureau national ne peut pas "
                    "être rattaché à une zone."
                )
            })

        if (
            self.niveau == NiveauBureau.NATIONAL
            and self.bureau_parent_id
        ):
            raise ValidationError({
                "bureau_parent": (
                    "Un bureau national ne peut pas "
                    "avoir de bureau national parent."
                )
            })

        # ----------------------------------------------------
        # BUREAU ZONAL
        # ----------------------------------------------------

        if self.niveau == NiveauBureau.ZONAL:

            if not self.zone_id:
                raise ValidationError({
                    "zone": (
                        "Un bureau zonal doit être "
                        "rattaché à une zone."
                    )
                })

            if not self.bureau_parent_id:
                raise ValidationError({
                    "bureau_parent": (
                        "Un bureau zonal doit avoir "
                        "un bureau national parent."
                    )
                })

            if self.eglise_id:
                raise ValidationError({
                    "eglise": (
                        "Un bureau zonal ne peut pas "
                        "être rattaché directement à une église."
                    )
                })

            if self.bureau_parent_id:
                parent = self.bureau_parent

                if parent and parent.niveau != NiveauBureau.NATIONAL:
                    raise ValidationError({
                        "bureau_parent": (
                            "Le bureau parent doit être "
                            "un bureau national."
                        )
                    })

                if parent and parent.type_bureau not in {
                    TypeBureau.HOMMES,
                    TypeBureau.FEMMES,
                    TypeBureau.JEUNESSE,
                    TypeBureau.ENFANTS,
                }:
                    raise ValidationError({
                        "bureau_parent": (
                            "Ce type de bureau national "
                            "ne possède pas de structure zonale."
                        )
                    })

        # ----------------------------------------------------
        # BUREAU LOCAL
        # ----------------------------------------------------

        if self.niveau == NiveauBureau.LOCAL:

            if not self.eglise_id:
                raise ValidationError({
                    "eglise": (
                        "Un bureau local doit être "
                        "rattaché à une église."
                    )
                })

            if self.zone_id:
                raise ValidationError({
                    "zone": (
                        "Un bureau local ne peut pas "
                        "être rattaché à une zone."
                    )
                })

        # ----------------------------------------------------
        # BUREAU GÉNÉRAL
        # ----------------------------------------------------

        if (
            self.type_bureau == TypeBureau.GENERAL
            and self.niveau != NiveauBureau.NATIONAL
        ):
            raise ValidationError({
                "type_bureau": (
                    "Le Bureau national général doit "
                    "être de niveau national."
                )
            })

        if (
            self.type_bureau == TypeBureau.GENERAL
            and self.eglise_id
        ):
            raise ValidationError({
                "eglise": (
                    "Le Bureau national général ne peut "
                    "pas être rattaché à une église."
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.code:

            if self.niveau == NiveauBureau.NATIONAL:
                base = f"BN-{self.type_bureau}"

            elif self.niveau == NiveauBureau.ZONAL:
                parent_code = (
                    self.bureau_parent.code
                    if self.bureau_parent_id
                    else "NATIONAL"
                )

                zone_code = (
                    self.zone.code
                    if self.zone_id
                    else "ZONE"
                )

                base = (
                    f"BZ-{parent_code}-{zone_code}"
                    f"-{self.type_bureau}"
                )

            else:
                eglise_code = (
                    self.eglise.code
                    if self.eglise_id
                    else "EGL"
                )

                base = (
                    f"BL-{eglise_code}"
                    f"-{self.type_bureau}"
                )

            code = base[:40]

            if Bureau.objects.exclude(
                pk=self.pk
            ).filter(
                code=code
            ).exists():

                i = 2

                while Bureau.objects.exclude(
                    pk=self.pk
                ).filter(
                    code=f"{base[:35]}-{i}"[:40]
                ).exists():
                    i += 1

                code = f"{base[:35]}-{i}"[:40]

            self.code = code

        super().save(*args, **kwargs)

    def __str__(self):
        if self.niveau == NiveauBureau.LOCAL and self.eglise:
            return f"{self.nom} · {self.eglise.nom}"

        if self.niveau == NiveauBureau.ZONAL and self.zone:
            return f"{self.nom} · {self.zone.nom}"

        return self.nom


# ============================================================
# ADMINISTRATEURS DES BUREAUX
# ============================================================

class BureauAdministrateur(models.Model):
    """
    Droits d'un compte à l'intérieur d'un bureau spécifique.
    """

    bureau = models.ForeignKey(
        Bureau,
        on_delete=models.CASCADE,
        related_name="administrateurs",
    )

    utilisateur = models.ForeignKey(
        "accounts.Utilisateur",
        on_delete=models.CASCADE,
        related_name="bureaux_administres",
    )

    peut_gerer_membres = models.BooleanField(
        default=True,
    )

    peut_gerer_finances = models.BooleanField(
        default=False,
    )

    peut_gerer_projets = models.BooleanField(
        default=True,
    )

    peut_envoyer_notifications = models.BooleanField(
        default=True,
    )

    peut_gerer_rapports = models.BooleanField(
        default=True,
    )

    peut_gerer_utilisateurs = models.BooleanField(
        default=False,
    )

    peut_creer_bureaux = models.BooleanField(
        default=False,
    )

    peut_gerer_eglises = models.BooleanField(
        default=False,
    )

    peut_gerer_bureaux_zonaux = models.BooleanField(
        default=False,
    )

    actif = models.BooleanField(
        default=True,
    )

    date_attribution = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "bureau",
                    "utilisateur",
                ],
                name="uniq_admin_bureau_utilisateur",
            )
        ]

        ordering = [
            "bureau__nom",
            "utilisateur__nom",
            "utilisateur__prenom",
        ]

    def __str__(self):
        return (
            f"{self.utilisateur} · "
            f"{self.bureau.nom}"
        )


# ============================================================
# MANDATS DES MEMBRES
# ============================================================

class BureauMembreMandat(models.Model):
    """
    Composition annuelle d'un bureau.

    Une même personne peut avoir plusieurs mandats annuels.
    """

    bureau = models.ForeignKey(
        Bureau,
        on_delete=models.CASCADE,
        related_name="mandats",
    )

    utilisateur = models.ForeignKey(
        "accounts.Utilisateur",
        on_delete=models.CASCADE,
        related_name="mandats_bureaux",
    )

    annee = models.PositiveIntegerField()

    poste = models.CharField(
        max_length=160,
    )

    objectif_annuel = models.TextField(
        blank=True,
    )

    actif = models.BooleanField(
        default=True,
    )

    date_nomination = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-annee",
            "bureau__nom",
            "poste",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "bureau",
                    "utilisateur",
                    "annee",
                ],
                name="uniq_mandat_bureau_utilisateur_annee",
            )
        ]

    def __str__(self):
        return (
            f"{self.utilisateur} · "
            f"{self.poste} · "
            f"{self.annee}"
        )


# ============================================================
# MEMBRES INDÉPENDANTS
# ============================================================

class BureauMembre(models.Model):
    """
    Membre d'un bureau indépendant d'un compte utilisateur EESAG.

    Cette fiche représente une personne publiée dans la
    composition d'un bureau.

    Elle n'accorde aucun droit de connexion et ne dépend pas
    de accounts.Utilisateur.
    """

    bureau = models.ForeignKey(
        Bureau,
        on_delete=models.CASCADE,
        related_name="membres_independants",
    )

    nom_complet = models.CharField(
        max_length=180,
    )

    photo = models.ImageField(
        upload_to="bureaux/membres/",
        blank=True,
        null=True,
    )

    poste = models.CharField(
        max_length=160,
    )

    annee = models.PositiveIntegerField(
        default=2026,
    )

    actif = models.BooleanField(
        default=True,
    )

    ordre = models.PositiveIntegerField(
        default=0,
    )

    date_ajout = models.DateTimeField(
        auto_now_add=True,
    )

    date_modification = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "ordre",
            "nom_complet",
        ]

        indexes = [
            models.Index(
                fields=[
                    "bureau",
                    "annee",
                    "actif",
                ]
            ),
            models.Index(
                fields=[
                    "nom_complet",
                ]
            ),
        ]

    def __str__(self):
        return (
            f"{self.nom_complet} · "
            f"{self.poste} · "
            f"{self.annee}"
        )