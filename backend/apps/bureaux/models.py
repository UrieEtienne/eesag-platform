from django.core.exceptions import ValidationError
from django.db import models


class NiveauBureau(models.TextChoices):
    NATIONAL = "NATIONAL", "Bureau national"
    LOCAL = "LOCAL", "Bureau d'église"


class TypeBureau(models.TextChoices):
    FEMMES = "FEMMES", "Bureau national des femmes"
    JEUNESSE = "JEUNESSE", "Bureau national de la jeunesse"
    ENFANTS = "ENFANTS", "Bureau national des enfants"
    EVANGELISATION = "EVANGELISATION", "Équipe nationale d'évangélisation"
    HOMMES = "HOMMES", "Bureau national des hommes"
    FAMILLES = "FAMILLES", "Bureau national des familles"
    COMMUNICATION = "COMMUNICATION", "Bureau de la communication"
    MUSIQUE = "MUSIQUE", "Bureau de la musique / chorale"
    MISSIONS = "MISSIONS", "Bureau des missions"
    AUTRE = "AUTRE", "Autre bureau / commission"


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

    class Meta:
        ordering = ["niveau", "nom"]
        constraints = [
            models.UniqueConstraint(
                fields=["niveau", "type_bureau", "eglise"],
                name="uniq_bureau_type_niveau_eglise",
            )
        ]

    def clean(self):
        if self.niveau == NiveauBureau.NATIONAL and self.eglise_id:
            raise ValidationError({"eglise": "Un bureau national ne peut pas être lié à une église."})
        if self.niveau == NiveauBureau.LOCAL and not self.eglise_id:
            raise ValidationError({"eglise": "Un bureau local doit être rattaché à une église."})

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.code:
            base = f"BN-{self.type_bureau}" if self.niveau == NiveauBureau.NATIONAL else f"BL-{self.eglise.code}-{self.type_bureau}"
            code = base[:40]
            if Bureau.objects.exclude(pk=self.pk).filter(code=code).exists():
                i = 2
                while Bureau.objects.exclude(pk=self.pk).filter(code=f"{base[:35]}-{i}"[:40]).exists():
                    i += 1
                code = f"{base[:35]}-{i}"[:40]
            self.code = code
        super().save(*args, **kwargs)

    def __str__(self):
        if self.niveau == NiveauBureau.LOCAL and self.eglise:
            return f"{self.nom} · {self.eglise.nom}"
        return self.nom


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

    class Meta:
        ordering = ["ordre", "nom_complet"]
        indexes = [
            models.Index(fields=["bureau", "annee", "actif"]),
            models.Index(fields=["nom_complet"]),
        ]

    def __str__(self):
        return f"{self.nom_complet} · {self.poste} · {self.annee}"
