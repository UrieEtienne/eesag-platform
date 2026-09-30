from django.db import models


class Transaction(models.Model):
    class TypeTransaction(models.TextChoices):
        DIME = "DIME", "Dîme"
        OFFRANDE = "OFFRANDE", "Offrande"
        DON = "DON", "Don"
        AUTRE_ENTREE = "AUTRE_ENTREE", "Autre entrée"
        SORTIE = "SORTIE", "Sortie / Dépense"

    eglise = models.ForeignKey(
        "churches.Eglise", on_delete=models.CASCADE, related_name="transactions",
        null=True, blank=True, help_text="Transaction de cette église locale."
    )
    bureau = models.ForeignKey(
        "bureaux.Bureau", on_delete=models.CASCADE, related_name="transactions",
        null=True, blank=True, help_text="Transaction d’un bureau national ou local. Laisser vide pour le socle financier national historique."
    )
    type_transaction = models.CharField(max_length=20, choices=TypeTransaction.choices)
    montant = models.DecimalField(max_digits=14, decimal_places=2)
    devise = models.CharField(max_length=10, default="GNF")
    description = models.CharField(max_length=255, blank=True)
    date_transaction = models.DateField()
    enregistre_par = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.SET_NULL, null=True, related_name="transactions_enregistrees"
    )
    date_enregistrement = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.eglise_id and self.bureau_id:
            from django.core.exceptions import ValidationError
            raise ValidationError("Une transaction ne peut pas être rattachée à la fois à une église et à un bureau.")

    class Meta:
        ordering = ["-date_transaction"]

    def __str__(self):
        return f"{self.get_type_transaction_display()} - {self.montant} {self.devise}"

    @property
    def est_une_entree(self):
        return self.type_transaction != self.TypeTransaction.SORTIE


class Projet(models.Model):
    class Statut(models.TextChoices):
        PLANIFIE = "PLANIFIE", "Planifié"
        EN_COURS = "EN_COURS", "En cours"
        TERMINE = "TERMINE", "Terminé"
        SUSPENDU = "SUSPENDU", "Suspendu"

    eglise = models.ForeignKey(
        "churches.Eglise", on_delete=models.CASCADE, related_name="projets",
        null=True, blank=True, help_text="Projet porté directement par une église."
    )
    bureau = models.ForeignKey(
        "bureaux.Bureau", on_delete=models.CASCADE, related_name="projets",
        null=True, blank=True, help_text="Projet porté par un bureau national ou local."
    )
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    type_projet = models.CharField(max_length=120, blank=True)
    annee = models.PositiveIntegerField(null=True, blank=True)
    objectif = models.TextField(blank=True)
    budget_prevu = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    budget_utilise = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PLANIFIE)
    date_debut = models.DateField(null=True, blank=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    responsable = models.ForeignKey(
        "accounts.Utilisateur", on_delete=models.SET_NULL, null=True, blank=True, related_name="projets_diriges"
    )

    def clean(self):
        if self.eglise_id and self.bureau_id:
            from django.core.exceptions import ValidationError
            raise ValidationError("Un projet ne peut pas être rattaché à la fois à une église et à un bureau.")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.nom

    @property
    def solde_disponible(self):
        return self.budget_prevu - self.budget_utilise
