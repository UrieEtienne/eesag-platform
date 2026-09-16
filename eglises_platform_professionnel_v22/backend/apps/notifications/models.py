from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        BIENVENUE = "BIENVENUE", "Bienvenue / Enregistrement"
        AFFECTATION = "AFFECTATION", "Affectation"
        COURRIER = "COURRIER", "Courrier reçu"
        DOCUMENT = "DOCUMENT", "Document reçu"
        PUBLICATION = "PUBLICATION", "Publication de l'église"
        SYSTEME = "SYSTEME", "Message système"
    RAPPORT = "RAPPORT", "Rapport"
    SECURITE = "SECURITE", "Sécurité / vérification"

    destinataire = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.CASCADE, related_name="notifications"
    )
    eglise = models.ForeignKey(
        "churches.Eglise", on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications"
    )
    titre = models.CharField(max_length=200)
    message = models.TextField()
    type_notification = models.CharField(max_length=20, choices=Type.choices, default=Type.SYSTEME)
    lien = models.CharField(max_length=255, blank=True)
    lu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.titre} -> {self.destinataire}"


class Publication(models.Model):
    """Message/programme publié par une église pour ses membres (et ses abonnés)."""
    eglise = models.ForeignKey("churches.Eglise", on_delete=models.CASCADE, related_name="publications")
    auteur = models.ForeignKey("accounts.Utilisateur", on_delete=models.SET_NULL, null=True)
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    date_publication = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_publication"]

    def __str__(self):
        return self.titre


class DiffusionNotification(models.Model):
    class Portee(models.TextChoices):
        EGLISE = "EGLISE", "Tous les membres d'une église"
        DEPARTEMENT = "DEPARTEMENT", "Membres d'un département"
        BUREAU = "BUREAU", "Membres d'un bureau"
        NATIONAL = "NATIONAL", "Tout le réseau"

    auteur = models.ForeignKey("accounts.Utilisateur", on_delete=models.SET_NULL, null=True, related_name="diffusions_notifications")
    portee = models.CharField(max_length=20, choices=Portee.choices)
    eglise = models.ForeignKey("churches.Eglise", on_delete=models.CASCADE, null=True, blank=True, related_name="diffusions_notifications")
    departement = models.ForeignKey("churches.Departement", on_delete=models.CASCADE, null=True, blank=True, related_name="diffusions_notifications")
    bureau = models.ForeignKey("bureaux.Bureau", on_delete=models.CASCADE, null=True, blank=True, related_name="diffusions_notifications")
    titre = models.CharField(max_length=200)
    message = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    nombre_destinataires = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.titre} · {self.get_portee_display()}"
