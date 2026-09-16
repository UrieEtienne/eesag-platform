from django.db import models


class JournalIA(models.Model):
    class Action(models.TextChoices):
        ANALYSE = "ANALYSE", "Analyse"
        BROUILLON = "BROUILLON", "Brouillon"
        MISE_A_JOUR = "MISE_A_JOUR", "Suggestions de mise à jour"
        RAPPORT = "RAPPORT", "Synthèse de rapport"

    utilisateur = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="journaux_ia"
    )
    eglise = models.ForeignKey(
        "churches.Eglise", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="journaux_ia"
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    entree = models.TextField(blank=True)
    resultat = models.TextField(blank=True)
    fournisseur = models.CharField(max_length=40, default="local")
    succes = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cree_le"]
        verbose_name = "Journal IA"
        verbose_name_plural = "Journaux IA"
