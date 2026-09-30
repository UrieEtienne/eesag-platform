from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class NiveauBureau(models.TextChoices):
    NATIONAL = "NATIONAL", "Bureau national"
    LOCAL = "LOCAL", "Bureau d'église"


class TypeBureau(models.TextChoices):
    HOMMES = "HOMMES", "Bureau national des hommes"
    FEMMES = "FEMMES", "Bureau national des femmes"
    JEUNESSE = "JEUNESSE", "Bureau national des jeunes"
    ENFANTS = "ENFANTS", "Bureau national des enfants"

    # Types conservés pour les futurs espaces spécialisés.
    EVANGELISATION = "EVANGELISATION", "Équipe nationale d'évangélisation"
    COMMUNICATION = "COMMUNICATION", "Bureau de la communication"
    MUSIQUE = "MUSIQUE", "Bureau de la musique / chorale"
    MISSIONS = "MISSIONS", "Bureau des missions"
    AUTRE = "AUTRE", "Autre bureau / commission"

# les constantes de sécurité
TYPES_BUREAUX_NATIONAUX = (
    TypeBureau.HOMMES,
    TypeBureau.FEMMES,
    TypeBureau.JEUNESSE,
    TypeBureau.ENFANTS,
)

TYPE_BUREAU_NATIONAL_PRINCIPAL = TypeBureau.GENERAL
   


class Bureau(models.Model):
    """Espace de gouvernance indépendant : national ou interne à une église."""
    nom = models.CharField(max_length=180)
    code = models.CharField(max_length=40, unique=True, editable=False)
    niveau = models.CharField(max_length=20, choices=NiveauBureau.choices, default=NiveauBureau.NATIONAL)
    type_bureau = models.CharField(max_length=30, choices=TypeBureau.choices, default=TypeBureau.AUTRE)
    eglise = models.ForeignKey(
        "churches.Eglise", null=True, blank=True, on_delete=models.CASCADE, related_name="bureaux"
    )
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # La hiérarchie des bureaux
    bureau_parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bureaux_enfants",
        help_text=(
            "Bureau responsable de cet espace. "
            "Par exemple, le Bureau national des hommes "
            "peut être responsable des autres bureaux nationaux."
        ),
    )

    # La garantie de chaque bureau aura un seul et pour les eglises un seul bureau
    class Meta:
        ordering = ["niveau", "nom"]
        constraints = [
            # Un type de bureau ne peut exister qu'une seule fois
            # au niveau national.
            models.UniqueConstraint(
                fields=["type_bureau"],
                condition=models.Q(
                    niveau=NiveauBureau.NATIONAL,
                    eglise__isnull=True,
                ),
                name="uniq_bureau_national_type",
            ),

            # Dans une église, un même type de bureau ne peut
            # exister qu'une seule fois.
            models.UniqueConstraint(
                fields=["niveau", "type_bureau", "eglise"],
                condition=models.Q(
                    niveau=NiveauBureau.LOCAL,
                    eglise__isnull=False,
                ),
                name="uniq_bureau_local_type_eglise",
            ),
        ]

    def clean(self):
        # --------------------------------------------------------
        # NIVEAU NATIONAL
        # --------------------------------------------------------
        if self.niveau == NiveauBureau.NATIONAL:

            if self.eglise_id:
                raise ValidationError({
                    "eglise": (
                        "Un bureau national ne peut pas être "
                        "rattaché à une église."
                    )
                })

            if self.type_bureau not in TYPES_BUREAUX_NATIONAUX:
                raise ValidationError({
                    "type_bureau": (
                        "Un bureau national doit être l'un des "
                        "quatre bureaux nationaux principaux : "
                        "Hommes, Femmes, Jeunesse ou Enfants."
                    )
                })

        # --------------------------------------------------------
        # NIVEAU LOCAL
        # --------------------------------------------------------
        if self.niveau == NiveauBureau.LOCAL:

            if not self.eglise_id:
                raise ValidationError({
                    "eglise": (
                        "Un bureau local doit être rattaché "
                        "à une église."
                    )
                })

        # --------------------------------------------------------
        # BUREAU PARENT
        # --------------------------------------------------------
        if self.bureau_parent_id:

            if self.bureau_parent_id == self.pk:
                raise ValidationError({
                    "bureau_parent": (
                        "Un bureau ne peut pas être son propre parent."
                    )
                })

            parent = self.bureau_parent

            # Les quatre bureaux nationaux principaux restent
            # au niveau national.
            if self.niveau == NiveauBureau.NATIONAL:
                if parent.niveau != NiveauBureau.NATIONAL:
                    raise ValidationError({
                        "bureau_parent": (
                            "Le parent d'un bureau national doit "
                            "également être un bureau national."
                        )
                    })

                # Seul le Bureau des hommes peut être parent
                # des autres bureaux nationaux.
                if parent.type_bureau != TypeBureau.HOMMES:
                    raise ValidationError({
                        "bureau_parent": (
                            "Le Bureau national des hommes est "
                            "le bureau national principal."
                        )
                    })

            # Un bureau local doit rester dans la même église
            # que son bureau parent.
            if self.niveau == NiveauBureau.LOCAL:
                if parent.niveau == NiveauBureau.LOCAL:
                    if parent.eglise_id != self.eglise_id:
                        raise ValidationError({
                            "bureau_parent": (
                                "Le bureau parent doit appartenir "
                                "à la même église."
                            )
                        })
    # Sauvegarde
    def save(self, *args, **kwargs):
        self.full_clean()

        if not self.code:
            if self.niveau == NiveauBureau.NATIONAL:
                base = f"BN-{self.type_bureau}"
            else:
                base = (
                    f"BL-{self.eglise.code}-"
                    f"{self.type_bureau}"
                )

            code = base[:40]

            if Bureau.objects.exclude(pk=self.pk).filter(
                code=code
            ).exists():

                i = 2

                while Bureau.objects.exclude(pk=self.pk).filter(
                    code=f"{base[:35]}-{i}"[:40]
                ).exists():
                    i += 1

                code = f"{base[:35]}-{i}"[:40]

            self.code = code

        super().save(*args, **kwargs)


class BureauAdministrateur(models.Model):
    """Droits d'un compte à l'intérieur d'un bureau spécifique."""
    bureau = models.ForeignKey(Bureau, on_delete=models.CASCADE, related_name="administrateurs")
    utilisateur = models.ForeignKey("accounts.Utilisateur", on_delete=models.CASCADE, related_name="bureaux_administres")
    peut_gerer_membres = models.BooleanField(default=True)
    peut_gerer_finances = models.BooleanField(default=False)
    peut_gerer_projets = models.BooleanField(default=True)
    peut_envoyer_notifications = models.BooleanField(default=True)
    peut_gerer_rapports = models.BooleanField(default=True)
    actif = models.BooleanField(default=True)
    date_attribution = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["bureau", "utilisateur"], name="uniq_admin_bureau_utilisateur")]
        ordering = ["bureau__nom", "utilisateur__nom", "utilisateur__prenom"]

    def __str__(self):
        return f"{self.utilisateur} · {self.bureau.nom}"

    @classmethod
    def national_general(cls):
        return cls.objects.filter(
            niveau=NiveauBureau.NATIONAL,
            type_bureau=TypeBureau.GENERAL,
            actif=True,
        ).first()


class BureauMembreMandat(models.Model):
    """Composition annuelle d'un bureau. Une même personne peut avoir plusieurs mandats annuels."""
    bureau = models.ForeignKey(Bureau, on_delete=models.CASCADE, related_name="mandats")
    utilisateur = models.ForeignKey("accounts.Utilisateur", on_delete=models.CASCADE, related_name="mandats_bureaux")
    annee = models.PositiveIntegerField()
    poste = models.CharField(max_length=160)
    objectif_annuel = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    date_nomination = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-annee", "bureau__nom", "poste"]
        constraints = [
            models.UniqueConstraint(fields=["bureau", "utilisateur", "annee"], name="uniq_mandat_bureau_utilisateur_annee")
        ]

    def __str__(self):
        return f"{self.utilisateur} · {self.poste} · {self.annee}"


class BureauMembre(models.Model):
    """Membre d'un bureau indépendant d'un compte utilisateur EESAG.

    Cette fiche représente une personne publiée dans la composition d'un bureau.
    Elle n'accorde aucun droit de connexion et ne dépend pas de accounts.Utilisateur.
    """
    bureau = models.ForeignKey(Bureau, on_delete=models.CASCADE, related_name="membres_independants")
    nom_complet = models.CharField(max_length=180)
    photo = models.ImageField(upload_to="bureaux/membres/", blank=True, null=True)
    poste = models.CharField(max_length=160)
    annee = models.PositiveIntegerField(default=2026)
    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=0)
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # Un compte utilisateur n'est pas automatiquement un membre du bureau.
    utilisateur = models.ForeignKey(
        "accounts.Utilisateur",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fiches_membres_bureaux",
        help_text=(
            "Compte utilisateur correspondant à cette personne, "
            "si elle possède un compte EESAG."
        ),
    )

    class Meta:
        ordering = ["ordre", "nom_complet"]
        indexes = [
            models.Index(fields=["bureau", "annee", "actif"]),
            models.Index(fields=["nom_complet"]),
        ]

    def __str__(self):
        return f"{self.nom_complet} · {self.poste} · {self.annee}"
