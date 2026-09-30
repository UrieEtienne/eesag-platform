from django.db import models


class Affectation(models.Model):
    class TypeAffectation(models.TextChoices):
        PASTEUR = "PASTEUR", "Pasteur / Responsable d'église"
        ADMIN_LOCAL = "ADMIN_LOCAL", "Administrateur local"
        MISSIONNAIRE = "MISSIONNAIRE", "Missionnaire"
        RESPONSABLE_DEPT = "RESPONSABLE_DEPT", "Responsable de département"

    utilisateur = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.CASCADE, related_name="affectations"
    )
    eglise = models.ForeignKey(
        "churches.Eglise", on_delete=models.CASCADE, related_name="affectations", null=True, blank=True
    )
    type_affectation = models.CharField(max_length=20, choices=TypeAffectation.choices)
    date_affectation = models.DateTimeField(auto_now_add=True)
    affecte_par = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.SET_NULL, null=True,
        related_name="affectations_realisees"
    )
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["-date_affectation"]

    def __str__(self):
        return f"{self.utilisateur} -> {self.eglise} ({self.type_affectation})"


class TransfertMembre(models.Model):
    """Mobilité d'un membre d'une église vers une autre, validée par courrier."""
    membre = models.ForeignKey("accounts.Utilisateur", on_delete=models.PROTECT, related_name="historique_transferts")
    eglise_depart = models.ForeignKey("churches.Eglise", on_delete=models.PROTECT, related_name="transferts_sortants")
    eglise_arrivee = models.ForeignKey("churches.Eglise", on_delete=models.PROTECT, related_name="transferts_entrants")
    courrier = models.ForeignKey("letters.Courrier", on_delete=models.SET_NULL, null=True, blank=True, related_name="transferts")
    demande_par = models.ForeignKey("accounts.Utilisateur", on_delete=models.SET_NULL, null=True, related_name="transferts_demandes")
    valide_par = models.ForeignKey("accounts.Utilisateur", on_delete=models.SET_NULL, null=True, blank=True, related_name="transferts_valides")
    motif = models.TextField(blank=True)
    date_demande = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=20, default="EN_ATTENTE", choices=[("EN_ATTENTE","En attente"),("VALIDE","Validé"),("REFUSE","Refusé")])

    class Meta:
        ordering = ["-date_demande"]
