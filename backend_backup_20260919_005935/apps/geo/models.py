from django.db import models


class Region(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Prefecture(models.Model):
    nom = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="prefectures")

    class Meta:
        ordering = ["nom"]
        unique_together = ("nom", "region")

    def __str__(self):
        return f"{self.nom} ({self.region.nom})"


class District(models.Model):
    nom = models.CharField(max_length=100)
    prefecture = models.ForeignKey(Prefecture, on_delete=models.CASCADE, related_name="districts")

    class Meta:
        ordering = ["nom"]
        unique_together = ("nom", "prefecture")

    def __str__(self):
        return f"{self.nom} ({self.prefecture.nom})"


class Commune(models.Model):
    """Commune / ville / quartier — plus petite unité géographique."""
    nom = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="communes")

    class Meta:
        ordering = ["nom"]
        unique_together = ("nom", "district")
        verbose_name = "Commune / Ville"
        verbose_name_plural = "Communes / Villes"

    def __str__(self):
        return f"{self.nom} ({self.district.nom})"
