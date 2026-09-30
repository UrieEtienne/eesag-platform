import random
import string
from datetime import date

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models


class Role(models.TextChoices):
    """Hiérarchie des rôles du système, du plus élevé au plus bas."""
    COORDINATEUR = "COORDINATEUR", "Coordinateur du système"
    SUPERADMIN_INTL = "SUPERADMIN_INTL", "Bureau national (hérité)"
    SUPERADMIN_NATIONAL = "SUPERADMIN_NATIONAL", "Administrateur du Bureau national"
    ADMIN_LOCAL = "ADMIN_LOCAL", "Administrateur Local (église)"
    PASTEUR = "PASTEUR", "Pasteur"
    RESPONSABLE_DEPARTEMENT = "RESPONSABLE_DEPARTEMENT", "Responsable de département"
    MEMBRE = "MEMBRE", "Membre"

# Rôles considérés comme "bureau national"
ROLES_NATIONAUX = [Role.COORDINATEUR, Role.SUPERADMIN_INTL, Role.SUPERADMIN_NATIONAL]
# Comptes appartenant réellement au Bureau national. Le Coordinateur reste propriétaire du système.
ROLES_BUREAU_NATIONAL = [Role.SUPERADMIN_INTL, Role.SUPERADMIN_NATIONAL]
# Rôles ayant accès à la gestion d'une église précise
ROLES_GESTION_EGLISE = [Role.ADMIN_LOCAL, Role.PASTEUR]


class Nationalite(models.TextChoices):
    GUINEE = "GN", "Guinée"
    SENEGAL = "SN", "Sénégal"
    MALI = "ML", "Mali"
    COTE_IVOIRE = "CI", "Côte d’Ivoire"
    LIBERIA = "LR", "Libéria"
    SIERRA_LEONE = "SL", "Sierra Leone"
    GHANA = "GH", "Ghana"
    NIGERIA = "NG", "Nigéria"
    BURKINA = "BF", "Burkina Faso"
    FRANCE = "FR", "France"
    USA = "US", "États-Unis"
    CANADA = "CA", "Canada"
    AUTRE = "OTHER", "Autre"


class FonctionEglise(models.TextChoices):
    MEMBRE = "MEMBRE", "Membre"
    PASTEUR = "PASTEUR", "Pasteur"
    PASTEUR_ASSISTANT = "PASTEUR_ASSISTANT", "Pasteur assistant"
    DIACRE = "DIACRE", "Diacre"
    ANCIEN = "ANCIEN", "Ancien"
    RESPONSABLE_DEPARTEMENT = "RESPONSABLE_DEPARTEMENT", "Responsable de département"
    SECRETAIRE = "SECRETAIRE", "Secrétaire"
    TRESORIER = "TRESORIER", "Trésorier"
    CHANTRE = "CHANTRE", "Chantre"
    MONITEUR = "MONITEUR", "Moniteur / Monitrice"
    MISSIONNAIRE = "MISSIONNAIRE", "Missionnaire"
    AUTRE = "AUTRE", "Autre"


class Sexe(models.TextChoices):
    HOMME = "H", "Homme"
    FEMME = "F", "Femme"


def generer_code_secret(longueur=6):
    return "".join(random.choices(string.digits, k=longueur))


class UtilisateurManager(BaseUserManager):
    def create_user(self, identifiant, password=None, **extra_fields):
        if not identifiant:
            raise ValueError("L'identifiant est obligatoire")
        user = self.model(identifiant=identifiant, **extra_fields)
        user.set_password(password or generer_code_secret())
        user.save(using=self._db)
        return user

    def create_superuser(self, identifiant, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.COORDINATEUR)
        return self.create_user(identifiant, password, **extra_fields)


def valider_taille_photo(image):
    if image and image.size > 5 * 1024 * 1024:
        raise ValidationError("La photo du membre ne doit pas dépasser 5 Mo.")




class Utilisateur(AbstractBaseUser, PermissionsMixin):
    """
    Représente TOUTE personne du système : membre du bureau national,
    pasteur, administrateur local, responsable de département ou simple fidèle.
    Chaque personne possède un identifiant unique + un code secret (mot de passe).
    """
    identifiant = models.CharField(max_length=20, unique=True, editable=False)
    code_secret_clair = models.CharField(
        max_length=10, blank=True,
        help_text="Conservé UNE fois en clair pour l'envoi SMS initial (à ne pas afficher ensuite)."
    )

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=Sexe.choices, default=Sexe.HOMME)
    date_naissance = models.DateField(null=True, blank=True)
    telephone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    photo = models.ImageField(upload_to="photos_utilisateurs/", null=True, blank=True, validators=[valider_taille_photo])
    nationalite = models.CharField(max_length=20, choices=Nationalite.choices, default=Nationalite.GUINEE)
    date_bapteme_eau = models.DateField(null=True, blank=True)
    date_bapteme_saint_esprit = models.DateField(null=True, blank=True)
    fonction_eglise = models.CharField(max_length=40, choices=FonctionEglise.choices, default=FonctionEglise.MEMBRE, blank=True)

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.MEMBRE)
    eglise = models.ForeignKey(
        "churches.Eglise", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="utilisateurs",
        help_text="Église de rattachement (vide pour les rôles nationaux)."
    )
    departement = models.ForeignKey(
        "churches.Departement", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="membres_departement"
    )
    role_eglise = models.ForeignKey(
        "churches.RoleEglise", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="membres",
        help_text="Rôle/fonction du membre dans son église, distinct du rôle technique du compte."
    )
    fonction_bureau_national = models.CharField(
        max_length=150, blank=True,
        help_text="Ex: Président, Secrétaire Général... (si membre du bureau national)"
    )

    date_enregistrement = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UtilisateurManager()

    def has_module_perms(self, app_label):
        """Le Bureau national utilise l’admin sans devenir propriétaire du système."""
        if self.role in ROLES_BUREAU_NATIONAL:
            return True
        return super().has_module_perms(app_label)

    def has_perm(self, perm, obj=None):
        """Accès métier large au Bureau; les Admins filtrent ensuite objets et opérations sensibles."""
        if self.role in ROLES_BUREAU_NATIONAL:
            return True
        return super().has_perm(perm, obj)

    USERNAME_FIELD = "identifiant"
    REQUIRED_FIELDS = ["nom", "prenom", "telephone"]

    class Meta:
        ordering = ["nom", "prenom"]

    @property
    def is_active(self):
        return self.actif

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.identifiant})"

    @property
    def est_national(self):
        return self.role in ROLES_NATIONAUX

    @property
    def categorie_age(self):
        """Retourne enfant / jeune / adulte selon la date de naissance."""
        if not self.date_naissance:
            return "inconnue"
        age = (date.today() - self.date_naissance).days // 365
        if age < 12:
            return "enfant"
        if age < 31:
            return "jeune"
        return "adulte"

    def generer_identifiant(self):
        """Génère un identifiant unique du type EGL-<codeeglise>-000123 ou NAT-000123."""
        prefixe = self.eglise.code if self.eglise_id and self.eglise else "NAT"
        base = f"{prefixe}-{Utilisateur.objects.count() + 1:06d}"
        while Utilisateur.objects.filter(identifiant=base).exists():
            base = f"{prefixe}-{random.randint(100000, 999999)}"
        return base

    def save(self, *args, **kwargs):
        if not self.identifiant:
            self.identifiant = self.generer_identifiant()
        super().save(*args, **kwargs)


class Abonnement(models.Model):
    """Permet à un membre de s'abonner aux notifications publiques d'une autre église."""
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="abonnements")
    eglise = models.ForeignKey("churches.Eglise", on_delete=models.CASCADE, related_name="abonnes")
    date_abonnement = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("utilisateur", "eglise")


class VerificationTelephone(models.Model):
    """Code OTP court pour activer un compte créé par son titulaire."""
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="verifications_telephone")
    code = models.CharField(max_length=6)
    cree_le = models.DateTimeField(auto_now_add=True)
    expire_le = models.DateTimeField()
    utilise = models.BooleanField(default=False)
    tentatives = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-cree_le"]




class JournalSMS(models.Model):
    """Historique des SMS/OTP pour diagnostiquer les problèmes de livraison."""
    class Statut(models.TextChoices):
        ENVOYE = "ENVOYE", "Envoyé"
        ECHEC = "ECHEC", "Échec"
        SIMULE = "SIMULE", "Simulé"

    utilisateur = models.ForeignKey(
        Utilisateur, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="journaux_sms"
    )
    telephone = models.CharField(max_length=30)
    type_message = models.CharField(max_length=40, default="INFORMATION")
    fournisseur = models.CharField(max_length=30, default="console")
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.SIMULE)
    message = models.TextField()
    provider_sid = models.CharField(max_length=80, blank=True)
    erreur = models.TextField(blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cree_le"]
        verbose_name = "Journal SMS"
        verbose_name_plural = "Journal SMS"

    def __str__(self):
        return f"{self.telephone} · {self.type_message} · {self.statut}"


class PermissionEglise(models.Model):
    """Droits fonctionnels délégables par le pasteur/administrateur principal."""
    code = models.CharField(max_length=60, unique=True)
    libelle = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.libelle


class DelegationEglise(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name="delegation_eglise")
    permissions = models.ManyToManyField(PermissionEglise, blank=True, related_name="delegations")
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True, related_name="delegations_creees")
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Délégation de droits"
        verbose_name_plural = "Délégations de droits"


class MandatBureauNational(models.Model):
    annee = models.PositiveIntegerField()
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="mandats_bureau_national")
    poste = models.CharField(max_length=150)
    actif = models.BooleanField(default=True)
    date_nomination = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["-annee", "poste"]
        constraints = [models.UniqueConstraint(fields=["annee", "utilisateur"], name="unique_mandat_utilisateur_annee")]
        verbose_name = "Mandat du Bureau national"
        verbose_name_plural = "Mandats du Bureau national"
