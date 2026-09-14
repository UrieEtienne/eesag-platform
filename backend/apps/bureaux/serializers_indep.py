from django.utils import timezone
from rest_framework import serializers
from .models import Bureau, BureauMembre
from .views import a_droit_bureau


class BureauMembreIndependantSerializer(serializers.ModelSerializer):
    bureau_nom = serializers.CharField(source="bureau.nom", read_only=True)
    photo_url = serializers.ImageField(source="photo", read_only=True)

    class Meta:
        model = BureauMembre
        fields = [
            "id", "bureau", "bureau_nom", "nom_complet", "photo", "photo_url",
            "poste", "annee", "actif", "ordre", "date_ajout", "date_modification",
        ]
        read_only_fields = ["date_ajout", "date_modification", "photo_url"]

    def validate_annee(self, value):
        if value < 2000 or value > 2100:
            raise serializers.ValidationError("Année invalide.")
        return value

    def validate(self, attrs):
        bureau = attrs.get("bureau", getattr(self.instance, "bureau", None))
        if bureau:
            request = self.context.get("request")
            if request and not a_droit_bureau(request.user, bureau, "peut_gerer_membres") and self.instance is None:
                raise serializers.ValidationError("Vous n'êtes pas autorisé à gérer ce bureau.")
        return attrs
