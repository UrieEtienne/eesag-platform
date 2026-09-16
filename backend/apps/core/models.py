from django.conf import settings
from django.db import models


class FonctionnaliteSysteme(models.Model):
    code = models.SlugField(max_length=80, unique=True)
    nom = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    groupe = models.CharField(max_length=80, default="Général")
    actif_global = models.BooleanField(default=True)
    reservable = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["groupe", "ordre", "nom"]
        verbose_name = "Fonctionnalité système"
        verbose_name_plural = "Fonctionnalités système"

    def __str__(self):
        return self.nom


class ActivationFonctionnalite(models.Model):
    fonctionnalite = models.ForeignKey(FonctionnaliteSysteme, on_delete=models.CASCADE, related_name="activations")
    eglise = models.ForeignKey("churches.Eglise", null=True, blank=True, on_delete=models.CASCADE, related_name="fonctionnalites_activees")
    bureau = models.ForeignKey("bureaux.Bureau", null=True, blank=True, on_delete=models.CASCADE, related_name="fonctionnalites_activees")
    actif = models.BooleanField(default=True)
    active_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="activations_fonctionnalites")
    date_activation = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["fonctionnalite", "eglise"], condition=models.Q(eglise__isnull=False, bureau__isnull=True), name="uniq_feature_eglise"),
            models.UniqueConstraint(fields=["fonctionnalite", "bureau"], condition=models.Q(bureau__isnull=False, eglise__isnull=True), name="uniq_feature_bureau"),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if bool(self.eglise_id) == bool(self.bureau_id):
            raise ValidationError("Une activation doit cibler une église ou un bureau, mais pas les deux.")

    def __str__(self):
        return f"{self.fonctionnalite.nom} · {self.eglise or self.bureau or '—'}"


class AnnonceSysteme(models.Model):
    NIVEAU = (("INFO", "Information"), ("NOUVEAUTE", "Nouvelle fonctionnalité"), ("MAINTENANCE", "Maintenance"), ("URGENT", "Urgent"))
    titre = models.CharField(max_length=180)
    message = models.TextField()
    niveau = models.CharField(max_length=20, choices=NIVEAU, default="INFO")
    fonctionnalite = models.ForeignKey(FonctionnaliteSysteme, null=True, blank=True, on_delete=models.SET_NULL, related_name="annonces")
    actif = models.BooleanField(default=True)
    publie_le = models.DateTimeField(null=True, blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="annonces_creees")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return self.titre


class ProfilDeveloppeur(models.Model):
    nom = models.CharField(max_length=160)
    titre = models.CharField(max_length=180, blank=True)
    biographie = models.TextField(blank=True)
    parcours = models.TextField(blank=True)
    experiences = models.TextField(blank=True)
    competences = models.TextField(blank=True)
    photo = models.ImageField(upload_to="developpeur/", blank=True, null=True)
    email_public = models.EmailField(blank=True)
    lien_public = models.URLField(blank=True)
    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom


class ConfigurationMonetisation(models.Model):
    actif = models.BooleanField(default=False)
    devise = models.CharField(max_length=10, default="GNF")
    fournisseur = models.CharField(max_length=80, blank=True)
    compte_destination = models.CharField(max_length=180, blank=True)
    url_paiement = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    derniere_modification = models.DateTimeField(auto_now=True)
    modifie_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="configurations_monetisation")

    def __str__(self):
        return "Monétisation EESAG"


class OffreMiseAJourSysteme(models.Model):
    fonctionnalite = models.ForeignKey(FonctionnaliteSysteme, null=True, blank=True, on_delete=models.SET_NULL, related_name="offres_mise_a_jour")
    version = models.CharField(max_length=40)
    titre = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    devise = models.CharField(max_length=10, default="GNF")
    gratuite = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    publie_le = models.DateTimeField(null=True, blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="offres_mise_a_jour_creees")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.version} · {self.titre}"
