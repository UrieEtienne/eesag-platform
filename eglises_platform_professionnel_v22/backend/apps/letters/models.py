from django.db import models


class Courrier(models.Model):
    class TypeCourrier(models.TextChoices):
        MISSION = "MISSION", "Lettre de mission"
        RECOMMANDATION = "RECOMMANDATION", "Lettre de recommandation"
        NOTE = "NOTE", "Note de service"

    numero_reference = models.CharField(max_length=30, unique=True, editable=False)
    type_courrier = models.CharField(max_length=20, choices=TypeCourrier.choices)

    expediteur = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.SET_NULL, null=True,
        related_name="courriers_envoyes"
    )
    # Pour une lettre de mission : l'église destinataire (nouvelle affectation)
    eglise_destinataire = models.ForeignKey(
        "churches.Eglise", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="courriers_recus"
    )
    # Pour une lettre de recommandation : le membre concerné + l'église qui le reçoit
    membre_concerne = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="courriers_le_concernant"
    )

    objet = models.CharField(max_length=255)
    contenu = models.TextField(help_text="Corps du texte de la lettre (exemple à personnaliser).")
    lieu_emission = models.CharField(max_length=100, default="Conakry")
    date_emission = models.DateField(auto_now_add=True)

    fichier_pdf = models.FileField(upload_to="courriers/", null=True, blank=True)
    fichier_word = models.FileField(upload_to="courriers/word/", null=True, blank=True)
    signe = models.BooleanField(default=False)
    cachete = models.BooleanField(default=False)
    lu = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_emission", "-id"]

    def __str__(self):
        return f"{self.get_type_courrier_display()} - {self.numero_reference}"

    def save(self, *args, **kwargs):
        if not self.numero_reference:
            from django.utils import timezone
            annee = timezone.now().year
            compteur = Courrier.objects.filter(date_emission__year=annee).count() + 1
            self.numero_reference = f"{compteur:04d}/{annee}/DIR-NAT"
        super().save(*args, **kwargs)
