from django.utils import timezone
from rest_framework import serializers
from .models import Reunion

class ReunionSerializer(serializers.ModelSerializer):
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True, default="Bureau national")
    organisateur_nom = serializers.SerializerMethodField()
    class Meta:
        model = Reunion
        fields = ["id","titre","description","eglise","eglise_nom","plateforme","lien","date_debut","date_fin","organisateur","organisateur_nom","active","created_at"]
        read_only_fields = ["organisateur","created_at"]
    def get_organisateur_nom(self, obj):
        if not obj.organisateur: return None
        return f"{obj.organisateur.prenom} {obj.organisateur.nom}"
    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.method not in ("GET","HEAD","OPTIONS"):
            eglise = attrs.get("eglise")
            if request.user.eglise_id and eglise and eglise.id != request.user.eglise_id:
                raise serializers.ValidationError({"eglise": "Cette réunion doit rester dans votre église."})
            if request.user.eglise_id and eglise is None:
                raise serializers.ValidationError({"eglise": "Une réunion locale doit être rattachée à votre église."})
        return attrs
