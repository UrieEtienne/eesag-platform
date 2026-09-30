from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class NiveauBureau(models.TextChoices):
    NATIONAL = "NATIONAL", "Bureau national"
    ZONAL = "ZONAL", "Bureau zonal"
    LOCAL = "LOCAL", "Bureau d'église"


class TypeBureau(models.TextChoices):
    """
    Types de bureaux nationaux et de leurs déclinaisons zonales/locales.
    """

    # Bureau national principal
    HOMMES = "HOMMES", "Bureau national des hommes"

    # Bureaux nationaux spécialisés
    FEMMES = "FEMMES", "Bureau national des femmes"
    JEUNESSE = "JEUNESSE", "Bureau national de la jeunesse"
    ENFANTS = "ENFANTS", "Bureau national des enfants"

    # Autres structures pouvant être ajoutées plus tard
    EVANGELISATION = (
        "EVANGELISATION",
        "Équipe nationale d'évangélisation",
    )
    COMMUNICATION = (
        "COMMUNICATION",
        "Bureau de la communication",
    )
    MUSIQUE = (
        "MUSIQUE",
        "Bureau de la musique / chorale",
    )
    MISSIONS = (
        "MISSIONS",
        "Bureau des missions",
    )
    AUTRE = (
        "AUTRE",
        "Autre bureau / commission",
    )


TYPES_BUREAUX_NATIONAUX = {
    TypeBureau.HOMMES,
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
    TypeBureau.EVANGELISATION,
    TypeBureau.COMMUNICATION,
    TypeBureau.MUSIQUE,
    TypeBureau.MISSIONS,
    TypeBureau.AUTRE,
}


TYPES_BUREAUX_ZONAUX = {
    TypeBureau.HOMMES,
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
}


class BureauZone(models.Model):
    """
    Zone géographique utilisée par les bureaux nationaux.

    Exemple :

        Conakry
          ├── Bureau zonal des hommes
          ├── Bureau zonal des femmes
          ├── Bureau zonal des jeunes
          └── Bureau zonal des enfants
    """

    nom = models.CharField(
        max_length=150,
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
        ordering = ["region__nom", "nom"]
        verbose_name = "Zone de bureau"
        verbose_name_plural = "Zones de bureaux"

    def save(self, *args, **kwargs):
        self.nom = self.nom.strip()

        if not self.code:
            base = f"ZONE-{self.region.nom}".upper()

            base = (
                base
                .replace(" ", "-")
                .replace("/", "-")
                .replace("'", "")
            )

            code = base[:40]

            if (
                BureauZone.objects
                .exclude(pk=self.pk)
                .filter(code=code)
                .exists()
            ):
                i = 2

                while (
                    BureauZone.objects
                    .exclude(pk=self.pk)
                    .filter(code=f"{base[:35]}-{i}"[:40])
                    .exists()
                ):
                    i += 1

                code = f"{base[:35]}-{i}"[:40]

            self.code = code

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} · {self.region.nom}"


class Bureau(models.Model):
    """
    Espace de gouvernance EESAG.

    NATIONAL :
        Bureau national des hommes
        Bureau national des femmes
        Bureau national des jeunes
        Bureau national des enfants

    ZONAL :
        Déclinaison d'un bureau national dans une zone.

    LOCAL :
        Bureau rattaché à une église.
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
        default=TypeBureau.HOMMES,
    )

    eglise = models.ForeignKey(
        "churches.Eglise",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="bureaux",
    )

    zone = models.ForeignKey(
        BureauZone,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="bureaux",
    )

    # IMPORTANT :
    # un bureau zonal appartient à un bureau national.
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
        ordering = ["niveau", "nom"]

        constraints = [
            # Un seul bureau d'un même type par église.
            models.UniqueConstraint(
                fields=[
                    "niveau",
                    "type_bureau",
                    "eglise",
                ],
                name="uniq_bureau_type_niveau_eglise",
            ),

            # Un seul bureau zonal d'un type donné
            # dans une zone.
            models.UniqueConstraint(
                fields=[
                    "niveau",
                    "type_bureau",
                    "zone",
                ],
                condition=models.Q(
                    niveau=NiveauBureau.ZONAL,
                    zone__isnull=False,
                ),
                name="uniq_bureau_zonal_type_zone",
            ),
        ]

    def clean(self):
        """
        Vérifie la cohérence entre niveau, église, zone
        et bureau parent.
        """

        # ========================================================
        # BUREAU NATIONAL
        # ========================================================

        if self.niveau == NiveauBureau.NATIONAL:

            if self.eglise_id:
                raise ValidationError({
                    "eglise": (
                        "Un bureau national ne peut pas être "
                        "rattaché à une église."
                    )
                })

            if self.zone_id:
                raise ValidationError({
                    "zone": (
                        "Un bureau national ne peut pas être "
                        "rattaché à une zone."
                    )
                })

            if self.bureau_parent_id:
                raise ValidationError({
                    "bureau_parent": (
                        "Un bureau national ne peut pas avoir "
                        "de bureau parent."
                    )
                })

            if self.type_bureau not in TYPES_BUREAUX_NATIONAUX:
                raise ValidationError({
                    "type_bureau": (
                        "Type de bureau national invalide."
                    )
                })

        # ========================================================
        # BUREAU ZONAL
        # ========================================================

        elif self.niveau == NiveauBureau.ZONAL:

            if not self.zone_id:
                raise ValidationError({
                    "zone": (
                        "Un bureau zonal doit obligatoirement "
                        "être rattaché à une zone."
                    )
                })

            if self.eglise_id:
                raise ValidationError({
                    "eglise": (
                        "Un bureau zonal ne peut pas être "
                        "rattaché directement à une église."
                    )
                })

            if not self.bureau_parent_id:
                raise ValidationError({
                    "bureau_parent": (
                        "Un bureau zonal doit avoir un "
                        "bureau national parent."
                    )
                })

            parent = self.bureau_parent

            if parent.niveau != NiveauBureau.NATIONAL:
                raise ValidationError({
                    "bureau_parent": (
                        "Le bureau parent doit être "
                        "un bureau national."
                    )
                })

            if parent.type_bureau != self.type_bureau:
                raise ValidationError({
                    "bureau_parent": (
                        "Le bureau zonal doit appartenir "
                        "au même type que son bureau national."
                    )
                })

            if self.type_bureau not in TYPES_BUREAUX_ZONAUX:
                raise ValidationError({
                    "type_bureau": (
                        "Ce type de bureau ne possède pas "
                        "de structure zonale."
                    )
                })

        # ========================================================
        # BUREAU LOCAL
        # ========================================================

        elif self.niveau == NiveauBureau.LOCAL:

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
                        "Un bureau local ne doit pas être "
                        "rattaché directement à une zone."
                    )
                })

            if self.bureau_parent_id:
                raise ValidationError({
                    "bureau_parent": (
                        "Un bureau local ne doit pas avoir "
                        "de bureau national parent."
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.code:

            if self.niveau == NiveauBureau.NATIONAL:
                base = f"BN-{self.type_bureau}"

            elif self.niveau == NiveauBureau.ZONAL:
                zone_code = self.zone.code if self.zone_id else "ZONE"
                base = f"BZ-{self.type_bureau}-{zone_code}"

            else:
                eglise_code = (
                    self.eglise.code
                    if self.eglise_id
                    else "EGL"
                )
                base = (
                    f"BL-{eglise_code}-"
                    f"{self.type_bureau}"
                )

            code = base[:40]

            if (
                Bureau.objects
                .exclude(pk=self.pk)
                .filter(code=code)
                .exists()
            ):
                i = 2

                while (
                    Bureau.objects
                    .exclude(pk=self.pk)
                    .filter(
                        code=f"{base[:35]}-{i}"[:40]
                    )
                    .exists()
                ):
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


class BureauAdministrateur(models.Model):
    """
    Compte utilisateur ayant des droits de gestion dans un bureau.

    IMPORTANT :
    être administrateur ne signifie pas être le Coordinateur.
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

    # NOUVEAU :
    # permet au bureau national spécialisé
    # de gérer ses bureaux zonaux.
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
        return f"{self.utilisateur} · {self.bureau.nom}"


class BureauMembreMandat(models.Model):
    """
    Composition annuelle liée à un compte utilisateur EESAG.

    Ce modèle est utilisé lorsqu'une personne dispose
    réellement d'un compte utilisateur.
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
            f"{self.poste} · {self.annee}"
        )


class BureauMembre(models.Model):
    """
    Personne affichée dans la composition publique d'un bureau.

    Elle NE possède pas obligatoirement de compte EESAG.

    Donc :

        BureauMembre
            = fiche publique

        Utilisateur
            = compte de connexion

        BureauAdministrateur
            = droits de gestion

    Une même personne peut donc être membre affiché
    sans avoir de compte utilisateur.
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
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "jpg",
                    "jpeg",
                    "png",
                ]
            )
        ],
    )

    poste = models.CharField(
        max_length=160,
    )

    annee = models.PositiveIntegerField(
        default=timezone.now().year,
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
            f"{self.poste} · {self.annee}"
        )