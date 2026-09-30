from rest_framework import serializers

from .models import (
    BureauZone,
    Bureau,
    NiveauBureau,
    TypeBureau,
)


class BureauZoneSerializer(serializers.ModelSerializer):
    region_nom = serializers.CharField(
        source="region.nom",
        read_only=True,
    )

    bureaux_count = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = BureauZone

        fields = [
            "id",
            "nom",
            "code",
            "region",
            "region_nom",
            "description",
            "actif",
            "bureaux_count",
            "date_creation",
        ]

        read_only_fields = [
            "id",
            "code",
            "bureaux_count",
            "date_creation",
        ]


class BureauZonalSerializer(serializers.ModelSerializer):
    zone_nom = serializers.CharField(
        source="zone.nom",
        read_only=True,
    )

    zone_code = serializers.CharField(
        source="zone.code",
        read_only=True,
    )

    bureau_parent_nom = serializers.CharField(
        source="bureau_parent.nom",
        read_only=True,
    )

    bureau_parent_code = serializers.CharField(
        source="bureau_parent.code",
        read_only=True,
    )

    type_bureau_libelle = serializers.CharField(
        source="get_type_bureau_display",
        read_only=True,
    )

    membres_actifs = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = Bureau

        fields = [
            "id",
            "nom",
            "code",
            "niveau",
            "type_bureau",
            "type_bureau_libelle",
            "zone",
            "zone_nom",
            "zone_code",
            "bureau_parent",
            "bureau_parent_nom",
            "bureau_parent_code",
            "description",
            "actif",
            "membres_actifs",
            "date_creation",
        ]

        read_only_fields = [
            "id",
            "code",
            "nom",
            "niveau",
            "type_bureau",
            "bureau_parent_nom",
            "bureau_parent_code",
            "zone_nom",
            "zone_code",
            "membres_actifs",
            "date_creation",
        ]

    def validate(self, attrs):
        zone = attrs.get("zone")
        parent = attrs.get("bureau_parent")

        if not zone:
            raise serializers.ValidationError({
                "zone": "La zone est obligatoire."
            })

        if not parent:
            raise serializers.ValidationError({
                "bureau_parent": (
                    "Le bureau national parent est obligatoire."
                )
            })

        if parent.niveau != NiveauBureau.NATIONAL:
            raise serializers.ValidationError({
                "bureau_parent": (
                    "Le parent doit être un bureau national."
                )
            })

        if parent.type_bureau not in {
            TypeBureau.HOMMES,
            TypeBureau.FEMMES,
            TypeBureau.JEUNESSE,
            TypeBureau.ENFANTS,
        }:
            raise serializers.ValidationError({
                "bureau_parent": (
                    "Ce type de bureau national "
                    "ne possède pas de structure zonale."
                )
            })

        return attrs