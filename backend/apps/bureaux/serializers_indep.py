from rest_framework import serializers

from .models import BureauMembre
from .access import a_droit_bureau


class BureauMembreIndependantSerializer(serializers.ModelSerializer):
    bureau_nom = serializers.CharField(
        source="bureau.nom",
        read_only=True,
    )

    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = BureauMembre
        fields = [
            "id",
            "bureau",
            "bureau_nom",
            "nom_complet",
            "photo",
            "photo_url",
            "poste",
            "annee",
            "actif",
            "ordre",
            "date_ajout",
            "date_modification",
        ]

        read_only_fields = [
            "id",
            "date_ajout",
            "date_modification",
            "photo_url",
        ]

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if not obj.photo:
            return None

        url = obj.photo.url

        if request:
            return request.build_absolute_uri(url)

        return url

    def validate_annee(self, value):
        if value < 2000 or value > 2100:
            raise serializers.ValidationError(
                "Année de mandat invalide."
            )
        return value

    def validate(self, attrs):
        bureau = attrs.get(
            "bureau",
            getattr(self.instance, "bureau", None),
        )

        request = self.context.get("request")

        if bureau and request:
            if not a_droit_bureau(
                request.user,
                bureau,
                "peut_gerer_membres",
            ):
                raise serializers.ValidationError({
                    "bureau": (
                        "Vous n'êtes pas autorisé à gérer "
                        "les membres de ce bureau."
                    )
                })

        return attrs