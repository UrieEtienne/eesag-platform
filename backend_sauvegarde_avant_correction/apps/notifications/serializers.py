from rest_framework import serializers
from .models import Notification, Publication, DiffusionNotification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "titre", "message", "type_notification", "lien", "lu", "date_creation", "eglise"]
        read_only_fields = fields


class PublicationSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.SerializerMethodField()
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True)

    class Meta:
        model = Publication
        fields = ["id", "eglise", "eglise_nom", "auteur", "auteur_nom", "titre", "contenu", "date_publication"]
        read_only_fields = ["auteur", "date_publication"]

    def get_auteur_nom(self, obj):
        return f"{obj.auteur.prenom} {obj.auteur.nom}" if obj.auteur else None


class DiffusionNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiffusionNotification
        fields = ["id", "portee", "eglise", "departement", "bureau", "titre", "message", "date_creation", "nombre_destinataires"]
        read_only_fields = ["id", "date_creation", "nombre_destinataires"]
