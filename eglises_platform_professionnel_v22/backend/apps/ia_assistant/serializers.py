from rest_framework import serializers


class AssistantRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["ANALYSE", "BROUILLON", "MISE_A_JOUR", "RAPPORT"])
    sujet = serializers.CharField(required=False, allow_blank=True, max_length=200)
    message = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    contexte = serializers.DictField(required=False)


class JournalIASerializer(serializers.ModelSerializer):
    class Meta:
        from .models import JournalIA
        model = JournalIA
        fields = ["id", "action", "fournisseur", "succes", "cree_le", "resultat"]
