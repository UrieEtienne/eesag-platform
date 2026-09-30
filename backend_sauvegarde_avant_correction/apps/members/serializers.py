from rest_framework import serializers
from .models import Affectation


class AffectationSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.SerializerMethodField()
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True, default=None)
    affecte_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = Affectation
        fields = [
            "id", "utilisateur", "utilisateur_nom", "eglise", "eglise_nom",
            "type_affectation", "date_affectation", "affecte_par", "affecte_par_nom", "actif",
        ]
        read_only_fields = ["date_affectation", "affecte_par"]

    def get_utilisateur_nom(self, obj):
        return f"{obj.utilisateur.prenom} {obj.utilisateur.nom}"

    def get_affecte_par_nom(self, obj):
        return f"{obj.affecte_par.prenom} {obj.affecte_par.nom}" if obj.affecte_par else None
