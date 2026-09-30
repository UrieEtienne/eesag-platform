from rest_framework import serializers
from .models import Transaction, Projet


class TransactionSerializer(serializers.ModelSerializer):
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True, default=None)
    bureau_nom = serializers.CharField(source="bureau.nom", read_only=True, default=None)
    enregistre_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id", "eglise", "eglise_nom", "bureau", "bureau_nom", "type_transaction", "montant", "devise",
            "description", "date_transaction", "enregistre_par", "enregistre_par_nom",
            "date_enregistrement",
        ]
        read_only_fields = ["enregistre_par", "date_enregistrement"]

    def validate(self, attrs):
        if attrs.get("eglise") and attrs.get("bureau"):
            raise serializers.ValidationError("Choisissez soit une église, soit un bureau.")
        return attrs

    def get_enregistre_par_nom(self, obj):
        return f"{obj.enregistre_par.prenom} {obj.enregistre_par.nom}" if obj.enregistre_par else None


class ProjetSerializer(serializers.ModelSerializer):
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True, default=None)
    bureau_nom = serializers.CharField(source="bureau.nom", read_only=True, default=None)
    responsable_nom = serializers.SerializerMethodField()
    solde_disponible = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Projet
        fields = [
            "id", "eglise", "eglise_nom", "bureau", "bureau_nom", "nom", "description", "type_projet", "annee", "objectif", "budget_prevu", "budget_utilise",
            "solde_disponible", "statut", "date_debut", "date_fin_prevue", "responsable", "responsable_nom",
        ]

    def validate(self, attrs):
        if attrs.get("eglise") and attrs.get("bureau"):
            raise serializers.ValidationError("Choisissez soit une église, soit un bureau.")
        return attrs

    def get_responsable_nom(self, obj):
        return f"{obj.responsable.prenom} {obj.responsable.nom}" if obj.responsable else None
