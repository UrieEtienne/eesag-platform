import random

from django.db import models


class Religion(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


def generer_code_eglise():
    return "EGL" + "".join(random.choices("0123456789", k=5))


class Eglise(models.Model):
    """
    Une église locale, recensée selon la hiérarchie région > préfecture > district > commune.
    """
    class Statut(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SUSPENDUE = "SUSPENDUE", "Suspendue"
        FERMEE = "FERMEE", "Fermée"

    code = models.CharField(max_length=10, unique=True, editable=False)
    nom = models.CharField(max_length=200)
    religion = models.ForeignKey(Religion, on_delete=models.PROTECT, related_name="eglises")

    region = models.ForeignKey("geo.Region", on_delete=models.PROTECT, related_name="eglises")
    prefecture = models.ForeignKey("geo.Prefecture", on_delete=models.PROTECT, related_name="eglises")
    district = models.ForeignKey("geo.District", on_delete=models.PROTECT, related_name="eglises")
    commune = models.ForeignKey("geo.Commune", on_delete=models.PROTECT, related_name="eglises",
                                 null=True, blank=True)
    adresse_precise = models.CharField(max_length=255, blank=True)

    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    date_creation = models.DateField(help_text="Date de création/fondation de l'église")
    date_enregistrement_systeme = models.DateTimeField(auto_now_add=True)

    responsable = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="eglises_dont_il_est_responsable",
        help_text="Responsable déjà enregistré dans EESAG (optionnel)."
    )
    responsable_nom = models.CharField(
        max_length=200, blank=True,
        help_text="Nom du responsable si cette personne n'a pas encore de compte EESAG."
    )
    responsable_telephone = models.CharField(
        max_length=20, blank=True,
        help_text="Téléphone du responsable (facultatif)."
    )
    responsable_email = models.EmailField(blank=True, help_text="Email du responsable (facultatif).")
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ACTIVE)
    plateforme_active = models.BooleanField(default=False, help_text="Accès activé uniquement par le Bureau national.")
    date_activation_plateforme = models.DateTimeField(null=True, blank=True)
    activee_par = models.ForeignKey("accounts.Utilisateur", null=True, blank=True, on_delete=models.SET_NULL, related_name="eglises_activees_plateforme")
    logo = models.ImageField(upload_to="logos_eglises/", null=True, blank=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Église"
        verbose_name_plural = "Églises"

    def __str__(self):
        return f"{self.nom} [{self.code}]"

    def save(self, *args, **kwargs):
        if not self.code:
            code = generer_code_eglise()
            while Eglise.objects.filter(code=code).exists():
                code = generer_code_eglise()
            self.code = code
        super().save(*args, **kwargs)

    @property
    def nombre_membres(self):
        return self.utilisateurs.filter(actif=True).count()


class Annexe(models.Model):
    """Implantation/annexe rattachée à une église principale."""
    eglise = models.ForeignKey(Eglise, on_delete=models.CASCADE, related_name="annexes")
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True, editable=False)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    responsable = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="annexes_dirigees"
    )
    active = models.BooleanField(default=True)
    date_creation = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Annexe"
        verbose_name_plural = "Annexes"
        constraints = [models.UniqueConstraint(fields=["eglise", "nom"], name="unique_annexe_nom_par_eglise")]

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"{self.eglise.code}-ANN-{self.eglise.annexes.count() + 1:03d}"
            while Annexe.objects.filter(code=self.code).exists():
                self.code = f"{self.eglise.code}-ANN-{random.randint(1, 999):03d}"
        super().save(*args, **kwargs)


class Departement(models.Model):
    """Département EESAG partagé par toutes les églises.

    Un département est une référence organisationnelle globale : il n'est
    rattaché ni à une église, ni à un responsable.
    """
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Département"
        verbose_name_plural = "Départements"

    def __str__(self):
        return self.nom

    @property
    def nombre_membres(self):
        return self.membres_departement.filter(actif=True).count()


class RoleEglise(models.Model):
    """Rôle/fonction dynamique d'un membre dans son église.

    Ce rôle est distinct du rôle technique du compte EESAG (MEMBRE, PASTEUR,
    ADMIN_LOCAL, etc.). Il peut être créé lorsqu'il n'existe pas encore.
    """
    nom = models.CharField(max_length=100, unique=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Rôle dans l'église"
        verbose_name_plural = "Rôles dans l'église"

    def __str__(self):
        return self.nom
