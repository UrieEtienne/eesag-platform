from rest_framework import serializers

from .models import Document, DocumentDestinataire
from apps.churches.models import Eglise


class DocumentDestinataireSerializer(serializers.ModelSerializer):
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True)

    class Meta:
        model = DocumentDestinataire
        fields = ["id", "eglise", "eglise_nom", "lu", "compte_reception", "date_reception"]
        read_only_fields = ["lu", "date_reception"]


class DocumentSerializer(serializers.ModelSerializer):
    expediteur_nom = serializers.SerializerMethodField()
    eglise_expediteur_nom = serializers.CharField(source="eglise_expediteur.nom", read_only=True)
    destinataires = serializers.PrimaryKeyRelatedField(many=True, queryset=Eglise.objects.all(), write_only=True)
    destinataires_resume = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id", "titre", "description", "categorie", "fichier", "est_word", "expediteur", "expediteur_nom",
            "eglise_expediteur", "eglise_expediteur_nom", "destinataires", "destinataires_resume",
            "date_envoi", "actif",
        ]
        read_only_fields = ["expediteur", "eglise_expediteur", "date_envoi"]

    def get_expediteur_nom(self, obj):
        return f"{obj.expediteur.prenom} {obj.expediteur.nom}" if obj.expediteur else "Compte supprimé"

    def get_destinataires_resume(self, obj):
        return DocumentDestinataireSerializer(obj.liaisons_destinataires.select_related("eglise"), many=True).data

    def validate_destinataires(self, value):
        if not value:
            raise serializers.ValidationError("Sélectionnez au moins une église destinataire.")
        return value

    def create(self, validated_data):
        destinataires = validated_data.pop("destinataires", [])
        request = self.context["request"]
        user = request.user
        document = Document.objects.create(
            **validated_data,
            expediteur=user,
            eglise_expediteur=user.eglise,
        )
        DocumentDestinataire.objects.bulk_create([
            DocumentDestinataire(document=document, eglise=eglise) for eglise in destinataires
        ])
        from apps.accounts.models import Utilisateur
        from apps.notifications.models import Notification
        recipients = Utilisateur.objects.filter(eglise__in=destinataires, actif=True).select_related("eglise")
        Notification.objects.bulk_create([
            Notification(
                destinataire=u, eglise=u.eglise,
                titre=f"Nouveau document : {document.titre}",
                message=f"Document reçu de {document.eglise_expediteur.nom if document.eglise_expediteur else 'la plateforme nationale'}.",
                type_notification="DOCUMENT",
                lien=f"/documents/{document.id}/",
            ) for u in recipients
        ])
        return document
