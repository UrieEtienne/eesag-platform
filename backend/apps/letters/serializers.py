from rest_framework import serializers

from .models import Courrier
from .pdf_generator import texte_exemple


class CourrierSerializer(serializers.ModelSerializer):
    expediteur_nom = serializers.SerializerMethodField()
    eglise_origine_nom = serializers.SerializerMethodField()
    eglise_destinataire_nom = serializers.SerializerMethodField()
    membre_concerne_nom = serializers.SerializerMethodField()
    receptionne_par_nom = serializers.SerializerMethodField()

    type_courrier_libelle = serializers.CharField(
        source="get_type_courrier_display",
        read_only=True,
    )
    type_destinataire_libelle = serializers.CharField(
        source="get_type_destinataire_display",
        read_only=True,
    )

    class Meta:
        model = Courrier
        fields = [
            "id",
            "numero_reference",
            "type_courrier",
            "type_courrier_libelle",
            "type_destinataire",
            "type_destinataire_libelle",
            "destinataire_nom",
            "expediteur",
            "expediteur_nom",
            "eglise_origine",
            "eglise_origine_nom",
            "eglise_destinataire",
            "eglise_destinataire_nom",
            "membre_concerne",
            "membre_concerne_nom",
            "objet",
            "contenu",
            "lieu_emission",
            "date_emission",
            "fichier_pdf",
            "fichier_word",
            "signe",
            "cachete",
            "lu",
            "receptionne_par",
            "receptionne_par_nom",
            "date_reception",
        ]
        read_only_fields = [
            "id",
            "numero_reference",
            "expediteur",
            "eglise_origine",
            "date_emission",
            "fichier_pdf",
            "lu",
            "receptionne_par",
            "date_reception",
        ]

    def get_expediteur_nom(self, obj):
        if not obj.expediteur:
            return None
        return (
            f"{obj.expediteur.prenom} {obj.expediteur.nom}".strip()
        )

    def get_eglise_origine_nom(self, obj):
        return obj.eglise_origine.nom if obj.eglise_origine else None

    def get_eglise_destinataire_nom(self, obj):
        return (
            obj.eglise_destinataire.nom
            if obj.eglise_destinataire
            else None
        )

    def get_membre_concerne_nom(self, obj):
        if not obj.membre_concerne:
            return None
        return (
            f"{obj.membre_concerne.prenom} "
            f"{obj.membre_concerne.nom}"
        ).strip()

    def get_receptionne_par_nom(self, obj):
        if not obj.receptionne_par:
            return None
        return (
            f"{obj.receptionne_par.prenom} "
            f"{obj.receptionne_par.nom}"
        ).strip()

    def validate(self, attrs):
        type_courrier = attrs.get(
            "type_courrier",
            getattr(self.instance, "type_courrier", None),
        )
        type_destinataire = attrs.get(
            "type_destinataire",
            getattr(self.instance, "type_destinataire", "EGLISE"),
        )
        eglise_destinataire = attrs.get(
            "eglise_destinataire",
            getattr(self.instance, "eglise_destinataire", None),
        )
        destinataire_nom = attrs.get(
            "destinataire_nom",
            getattr(self.instance, "destinataire_nom", ""),
        )

        if type_courrier == Courrier.TypeCourrier.RECOMMANDATION:
            if not attrs.get(
                "membre_concerne",
                getattr(self.instance, "membre_concerne", None),
            ):
                raise serializers.ValidationError({
                    "membre_concerne": (
                        "Un membre est obligatoire pour une "
                        "recommandation pastorale."
                    )
                })

            if not eglise_destinataire:
                raise serializers.ValidationError({
                    "eglise_destinataire": (
                        "L'église destinataire est obligatoire."
                    )
                })

        if type_courrier == Courrier.TypeCourrier.NATIONALE:
            if type_destinataire == "EGLISE" and not eglise_destinataire:
                raise serializers.ValidationError({
                    "eglise_destinataire": (
                        "Sélectionne une église destinataire."
                    )
                })

            if type_destinataire in ("BUREAU_NATIONAL", "AUTRE"):
                if not destinataire_nom and type_destinataire == "AUTRE":
                    raise serializers.ValidationError({
                        "destinataire_nom": (
                            "Indique le nom du destinataire."
                        )
                    })

        return attrs

    def create(self, validated_data):
        if not validated_data.get("contenu"):
            membre = validated_data.get("membre_concerne")
            nom_cible = (
                f"{membre.prenom} {membre.nom}"
                if membre
                else ""
            )
            validated_data["contenu"] = texte_exemple(
                validated_data["type_courrier"],
                nom_cible,
            )

        return super().create(validated_data)
