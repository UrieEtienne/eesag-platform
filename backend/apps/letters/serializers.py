from rest_framework import serializers
from .models import Courrier
from .pdf_generator import texte_exemple


class CourrierSerializer(serializers.ModelSerializer):
    expediteur_nom = serializers.SerializerMethodField()
    eglise_destinataire_nom = serializers.CharField(source="eglise_destinataire.nom", read_only=True, default=None)
    membre_concerne_nom = serializers.SerializerMethodField()

    class Meta:
        model = Courrier
        fields = [
            "id", "numero_reference", "type_courrier", "expediteur", "expediteur_nom",
            "eglise_destinataire", "eglise_destinataire_nom", "membre_concerne", "membre_concerne_nom",
            "objet", "contenu", "lieu_emission", "date_emission", "fichier_pdf", "fichier_word", "signe", "cachete", "lu",
        ]
        read_only_fields = ["numero_reference", "date_emission", "fichier_pdf", "lu"]

    def get_expediteur_nom(self, obj):
        return f"{obj.expediteur.prenom} {obj.expediteur.nom}" if obj.expediteur else None

    def get_membre_concerne_nom(self, obj):
        return f"{obj.membre_concerne.prenom} {obj.membre_concerne.nom}" if obj.membre_concerne else None

    def create(self, validated_data):
        # Pré-remplit un exemple de texte si le contenu est vide (l'utilisateur le modifiera ensuite)
        if not validated_data.get("contenu"):
            cible = validated_data.get("membre_concerne")
            nom_cible = f"{cible.prenom} {cible.nom}" if cible else ""
            validated_data["contenu"] = texte_exemple(validated_data["type_courrier"], nom_cible)
        return super().create(validated_data)
