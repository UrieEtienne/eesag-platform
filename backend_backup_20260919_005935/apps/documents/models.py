from django.db import models


class Document(models.Model):
    class Categorie(models.TextChoices):
        OFFICIEL = "OFFICIEL", "Document officiel"
        ADMINISTRATIF = "ADMINISTRATIF", "Administratif"
        RAPPORT = "RAPPORT", "Rapport"
        PROJET = "PROJET", "Projet"
        AUTRE = "AUTRE", "Autre"

    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    categorie = models.CharField(max_length=20, choices=Categorie.choices, default=Categorie.OFFICIEL)
    fichier = models.FileField(upload_to="documents/%Y/%m/")
    est_word = models.BooleanField(default=False)
    expediteur = models.ForeignKey("accounts.Utilisateur", on_delete=models.SET_NULL, null=True, related_name="documents_envoyes")
    eglise_expediteur = models.ForeignKey("churches.Eglise", on_delete=models.SET_NULL, null=True, blank=True, related_name="documents_envoyes")
    destinataires = models.ManyToManyField("churches.Eglise", through="DocumentDestinataire", related_name="documents_recus")
    date_envoi = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["-date_envoi"]

    def __str__(self):
        return self.titre


class DocumentDestinataire(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="liaisons_destinataires")
    eglise = models.ForeignKey("churches.Eglise", on_delete=models.CASCADE, related_name="documents_destines")
    lu = models.BooleanField(default=False)
    compte_reception = models.BooleanField(default=False)
    date_reception = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "eglise"], name="unique_document_eglise_destinataire")
        ]
