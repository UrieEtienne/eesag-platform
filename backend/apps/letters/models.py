import uuid

from django.db import models
from django.utils import timezone


class Courrier(models.Model):

    class TypeCourrier(models.TextChoices):
        MISSION = "MISSION", "Lettre de mission"
        RECOMMANDATION = "RECOMMANDATION", "Lettre de recommandation pastorale"
        NOTE = "NOTE", "Note de service"
        NATIONALE = "NATIONALE", "Lettre nationale officielle"

    class TypeDestinataire(models.TextChoices):
        EGLISE = "EGLISE", "Église"
        BUREAU_NATIONAL = "BUREAU_NATIONAL", "Bureau national"
        AUTRE = "AUTRE", "Autre destinataire"

    numero_reference = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
    )

    type_courrier = models.CharField(
        max_length=20,
        choices=TypeCourrier.choices,
    )

    expediteur = models.ForeignKey(
        "accounts.Utilisateur",
        on_delete=models.SET_NULL,
        null=True,
        related_name="courriers_envoyes",
    )

    # L'origine historique est conservée même si le membre change d'église.
    eglise_origine = models.ForeignKey(
        "churches.Eglise",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courriers_origine",
    )

    eglise_destinataire = models.ForeignKey(
        "churches.Eglise",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courriers_recus",
    )

    type_destinataire = models.CharField(
        max_length=20,
        choices=TypeDestinataire.choices,
        default=TypeDestinataire.EGLISE,
    )

    destinataire_nom = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    membre_concerne = models.ForeignKey(
        "accounts.Utilisateur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courriers_le_concernant",
    )

    objet = models.CharField(max_length=255)
    contenu = models.TextField(
        help_text="Corps du texte de la lettre.",
    )
    lieu_emission = models.CharField(
        max_length=100,
        default="Conakry",
    )
    date_emission = models.DateField(auto_now_add=True)

    fichier_pdf = models.FileField(
        upload_to="courriers/",
        null=True,
        blank=True,
    )
    fichier_word = models.FileField(
        upload_to="courriers/word/",
        null=True,
        blank=True,
    )

    signe = models.BooleanField(default=False)
    cachete = models.BooleanField(default=False)
    lu = models.BooleanField(default=False)

    # Traçabilité de la réception officielle.
    receptionne_par = models.ForeignKey(
        "accounts.Utilisateur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courriers_receptionnes",
    )
    date_reception = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-date_emission", "-id"]

    def __str__(self):
        return (
            f"{self.get_type_courrier_display()} "
            f"- {self.numero_reference}"
        )

    def save(self, *args, **kwargs):
        if not self.numero_reference:
            annee = timezone.now().year
            # Identifiant pratiquement unique, sans compteur sujet aux
            # doublons lors de créations simultanées.
            suffixe = uuid.uuid4().hex[:8].upper()
            self.numero_reference = f"{annee}-{suffixe}/DIR-NAT"

        super().save(*args, **kwargs)
