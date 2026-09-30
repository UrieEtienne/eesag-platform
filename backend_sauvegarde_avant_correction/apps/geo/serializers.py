from rest_framework import serializers
from .models import Region, Prefecture, District, Commune


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "nom"]


class PrefectureSerializer(serializers.ModelSerializer):
    region_nom = serializers.CharField(source="region.nom", read_only=True)

    class Meta:
        model = Prefecture
        fields = ["id", "nom", "region", "region_nom"]


class DistrictSerializer(serializers.ModelSerializer):
    prefecture_nom = serializers.CharField(source="prefecture.nom", read_only=True)

    class Meta:
        model = District
        fields = ["id", "nom", "prefecture", "prefecture_nom"]


class CommuneSerializer(serializers.ModelSerializer):
    district_nom = serializers.CharField(source="district.nom", read_only=True)

    class Meta:
        model = Commune
        fields = ["id", "nom", "district", "district_nom"]
