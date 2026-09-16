from django.db import models


class Reunion(models.Model):
    class Plateforme(models.TextChoices):
        JITSI = "JITSI", "Jitsi Meet"
        ZOOM = "ZOOM", "Zoom"
        MEET = "MEET", "Google Meet"
        AUTRE = "AUTRE", "Autre"

    titre = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    eglise = models.ForeignKey("churches.Eglise", null=True, blank=True, on_delete=models.CASCADE, related_name="reunions")
    plateforme = models.CharField(max_length=20, choices=Plateforme.choices, default=Plateforme.JITSI)
    lien = models.URLField(max_length=500)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    organisateur = models.ForeignKey("accounts.Utilisateur", null=True, blank=True, on_delete=models.SET_NULL, related_name="reunions_organisees")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_debut"]
        verbose_name = "Réunion"
        verbose_name_plural = "Réunions"

    def __str__(self):
        return self.titre
