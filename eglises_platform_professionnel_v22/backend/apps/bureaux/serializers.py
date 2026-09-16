from rest_framework import serializers
from .models import Bureau, BureauAdministrateur, BureauMembreMandat


class BureauSerializer(serializers.ModelSerializer):
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True, default=None)
    type_bureau_libelle = serializers.CharField(source="get_type_bureau_display", read_only=True)
    niveau_libelle = serializers.CharField(source="get_niveau_display", read_only=True)
    membres_actifs = serializers.IntegerField(read_only=True)
    mes_droits = serializers.SerializerMethodField()

    class Meta:
        model = Bureau
        fields = [
            "id", "nom", "code", "niveau", "niveau_libelle", "type_bureau",
            "type_bureau_libelle", "eglise", "eglise_nom", "description", "actif",
            "membres_actifs", "date_creation", "mes_droits",
        ]
        read_only_fields = ["id", "code", "date_creation", "membres_actifs", "mes_droits"]

    def get_mes_droits(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return {}
        user = request.user
        if user.role == "COORDINATEUR" or user.is_superuser:
            return {k: True for k in ["peut_gerer_membres", "peut_gerer_finances", "peut_gerer_projets", "peut_envoyer_notifications", "peut_gerer_rapports"]}
        if user.role in ["SUPERADMIN_INTL", "SUPERADMIN_NATIONAL"] and obj.niveau == "NATIONAL":
            from .models import BureauAdministrateur
            if not BureauAdministrateur.objects.filter(utilisateur=user, actif=True).exists():
                return {k: True for k in ["peut_gerer_membres", "peut_gerer_finances", "peut_gerer_projets", "peut_envoyer_notifications", "peut_gerer_rapports"]}
        if user.role in ["PASTEUR", "ADMIN_LOCAL"] and obj.niveau == "LOCAL" and obj.eglise_id == user.eglise_id:
            return {k: True for k in ["peut_gerer_membres", "peut_gerer_finances", "peut_gerer_projets", "peut_envoyer_notifications", "peut_gerer_rapports"]}
        admin = BureauAdministrateur.objects.filter(bureau=obj, utilisateur=user, actif=True).first()
        if not admin:
            return {k: False for k in ["peut_gerer_membres", "peut_gerer_finances", "peut_gerer_projets", "peut_envoyer_notifications", "peut_gerer_rapports"]}
        return {
            "peut_gerer_membres": admin.peut_gerer_membres,
            "peut_gerer_finances": admin.peut_gerer_finances,
            "peut_gerer_projets": admin.peut_gerer_projets,
            "peut_envoyer_notifications": admin.peut_envoyer_notifications,
            "peut_gerer_rapports": admin.peut_gerer_rapports,
        }


class BureauMembreMandatSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField()
    photo = serializers.ImageField(source="utilisateur.photo", read_only=True)
    identifiant = serializers.CharField(source="utilisateur.identifiant", read_only=True)
    bureau_nom = serializers.CharField(source="bureau.nom", read_only=True)

    class Meta:
        model = BureauMembreMandat
        fields = ["id", "bureau", "bureau_nom", "utilisateur", "identifiant", "nom_complet", "photo", "annee", "poste", "objectif_annuel", "actif", "date_nomination"]
        read_only_fields = ["date_nomination"]

    def validate(self, attrs):
        bureau = attrs.get("bureau", getattr(self.instance, "bureau", None))
        utilisateur = attrs.get("utilisateur", getattr(self.instance, "utilisateur", None))
        if bureau and utilisateur:
            if utilisateur.role == "COORDINATEUR":
                raise serializers.ValidationError({"utilisateur": "Le Coordinateur est propriétaire du système et ne peut pas être membre d'un bureau."})
            if bureau.niveau == "NATIONAL" and utilisateur.eglise_id:
                raise serializers.ValidationError({"utilisateur": "Un membre d'un bureau national ne doit pas être rattaché à une église."})
            if bureau.niveau == "LOCAL" and utilisateur.eglise_id != bureau.eglise_id:
                raise serializers.ValidationError({"utilisateur": "Le membre doit appartenir à la même église que le bureau local."})
        return attrs

    def validate_annee(self, value):
        if value < 2000 or value > 2100:
            raise serializers.ValidationError("Année de mandat invalide.")
        return value

    def get_nom_complet(self, obj):
        return f"{obj.utilisateur.prenom} {obj.utilisateur.nom}"


class BureauAdministrateurSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField(read_only=True)
    bureau_nom = serializers.CharField(source="bureau.nom", read_only=True)

    class Meta:
        model = BureauAdministrateur
        fields = [
            "id", "bureau", "bureau_nom", "utilisateur", "nom_complet",
            "peut_gerer_membres", "peut_gerer_finances", "peut_gerer_projets",
            "peut_envoyer_notifications", "peut_gerer_rapports", "actif", "date_attribution",
        ]
        read_only_fields = ["date_attribution"]

    def validate(self, attrs):
        bureau = attrs.get("bureau", getattr(self.instance, "bureau", None))
        user = attrs.get("utilisateur", getattr(self.instance, "utilisateur", None))
        if bureau and user:
            if user.role == "COORDINATEUR":
                raise serializers.ValidationError("Le Coordinateur ne doit pas être administrateur d'un bureau.")
            if bureau.niveau == "NATIONAL" and user.eglise_id:
                raise serializers.ValidationError("Un administrateur d'un bureau national ne doit pas être rattaché à une église.")
            if bureau.niveau == "LOCAL" and user.eglise_id != bureau.eglise_id:
                raise serializers.ValidationError("L'administrateur local doit appartenir à la même église.")
        return attrs

    def get_nom_complet(self, obj):
        return f"{obj.utilisateur.prenom} {obj.utilisateur.nom}"
