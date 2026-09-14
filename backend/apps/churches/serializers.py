from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import Utilisateur, Role
from .models import Religion, Eglise, Departement, RoleEglise, Annexe


class ReligionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Religion
        fields = ["id", "nom", "description"]


class DepartementSerializer(serializers.ModelSerializer):
    nombre_membres = serializers.IntegerField(read_only=True)

    class Meta:
        model = Departement
        fields = ["id", "nom", "nombre_membres"]
        read_only_fields = ["id", "nombre_membres"]


class RoleEgliseSerializer(serializers.ModelSerializer):
    nombre_membres = serializers.IntegerField(source="membres.count", read_only=True)

    class Meta:
        model = RoleEglise
        fields = ["id", "nom", "actif", "nombre_membres"]
        read_only_fields = ["id", "nombre_membres"]


class AnnexeSerializer(serializers.ModelSerializer):
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True)
    responsable_nom = serializers.SerializerMethodField()

    class Meta:
        model = Annexe
        fields = ["id", "eglise", "eglise_nom", "nom", "code", "adresse", "telephone", "responsable", "responsable_nom", "active", "date_creation"]
        read_only_fields = ["code", "eglise"]

    def get_responsable_nom(self, obj):
        return f"{obj.responsable.prenom} {obj.responsable.nom}" if obj.responsable else None


class EgliseListSerializer(serializers.ModelSerializer):
    religion_nom = serializers.CharField(source="religion.nom", read_only=True)
    region_nom = serializers.CharField(source="region.nom", read_only=True)
    prefecture_nom = serializers.CharField(source="prefecture.nom", read_only=True)
    district_nom = serializers.CharField(source="district.nom", read_only=True)
    commune_nom = serializers.CharField(source="commune.nom", read_only=True, default=None)
    responsable_nom = serializers.SerializerMethodField()
    responsable_source = serializers.SerializerMethodField()
    nombre_membres = serializers.IntegerField(read_only=True)

    class Meta:
        model = Eglise
        fields = [
            "id", "code", "nom", "religion", "religion_nom",
            "region", "region_nom", "prefecture", "prefecture_nom",
            "district", "district_nom", "commune", "commune_nom",
            "statut", "responsable", "responsable_nom", "responsable_source", "nombre_membres", "logo",
        ]
        read_only_fields = ["code", "responsable", "nombre_membres"]

    def get_responsable_nom(self, obj):
        if obj.responsable:
            return f"{obj.responsable.prenom} {obj.responsable.nom}"
        return obj.responsable_nom or None

    def get_responsable_source(self, obj):
        if obj.responsable:
            return "compte_eesag"
        if obj.responsable_nom:
            return "nom_saisi"
        return None


class EgliseAnnuaireSerializer(serializers.ModelSerializer):
    """Fiche d'annuaire volontairement minimale pour les utilisateurs locaux."""
    religion_nom = serializers.CharField(source="religion.nom", read_only=True)
    region_nom = serializers.CharField(source="region.nom", read_only=True)
    prefecture_nom = serializers.CharField(source="prefecture.nom", read_only=True)
    district_nom = serializers.CharField(source="district.nom", read_only=True)
    commune_nom = serializers.CharField(source="commune.nom", read_only=True, default=None)

    class Meta:
        model = Eglise
        fields = ["id", "code", "nom", "religion_nom", "region_nom", "prefecture_nom", "district_nom", "commune_nom", "statut"]
        read_only_fields = fields


class EgliseDetailSerializer(EgliseListSerializer):
    departements = DepartementSerializer(many=True, read_only=True)
    annexes = AnnexeSerializer(many=True, read_only=True)

    class Meta(EgliseListSerializer.Meta):
        fields = EgliseListSerializer.Meta.fields + [
            "adresse_precise", "telephone", "email", "date_creation",
            "date_enregistrement_systeme", "departements", "annexes",
        ]


class EgliseCreateSerializer(serializers.ModelSerializer):
    """Création atomique d'une église, de son responsable et de son administrateur local."""
    creer_compte_admin = serializers.BooleanField(default=True, write_only=True)
    admin_nom = serializers.CharField(max_length=100, write_only=True, required=False)
    admin_prenom = serializers.CharField(max_length=100, write_only=True, required=False)
    admin_telephone = serializers.CharField(max_length=20, write_only=True, required=False)
    admin_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    admin_mot_de_passe = serializers.CharField(write_only=True, required=False, min_length=6)
    admin_confirmation = serializers.CharField(write_only=True, required=False)

    responsable_utilisateur = serializers.PrimaryKeyRelatedField(
        source="responsable",
        queryset=Utilisateur.objects.exclude(role=Role.COORDINATEUR).filter(actif=True),
        write_only=True, required=False, allow_null=True,
    )
    responsable_nom = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=200)
    responsable_telephone = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=20)
    responsable_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    compte_admin = serializers.SerializerMethodField(read_only=True)
    sms = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Eglise
        fields = [
            "id", "code", "nom", "religion", "region", "prefecture", "district", "commune",
            "adresse_precise", "telephone", "email", "date_creation", "statut", "logo",
            "responsable_utilisateur", "responsable_nom", "responsable_telephone", "responsable_email",
            "creer_compte_admin", "admin_nom", "admin_prenom", "admin_telephone", "admin_email",
            "admin_mot_de_passe", "admin_confirmation", "compte_admin", "sms",
        ]
        read_only_fields = ["id", "code", "statut"]

    def validate(self, attrs):
        creer = attrs.get("creer_compte_admin", True)
        champs = [attrs.get("admin_nom"), attrs.get("admin_prenom"), attrs.get("admin_telephone"), attrs.get("admin_mot_de_passe"), attrs.get("admin_confirmation")]
        if creer and any(not value for value in champs):
            raise serializers.ValidationError("Les informations de l'administrateur local sont obligatoires.")
        if creer and attrs.get("admin_mot_de_passe") != attrs.get("admin_confirmation"):
            raise serializers.ValidationError({"admin_confirmation": "Les mots de passe ne correspondent pas."})
        if creer:
            validate_password(attrs["admin_mot_de_passe"])
            if Utilisateur.objects.filter(telephone=attrs["admin_telephone"]).exists():
                raise serializers.ValidationError({"admin_telephone": "Ce numéro est déjà utilisé."})
        responsable = attrs.get("responsable")
        responsable_nom = attrs.get("responsable_nom", "").strip()
        if not responsable and not responsable_nom:
            raise serializers.ValidationError({"responsable_nom": "Saisissez le nom du responsable si aucun compte EESAG n'existe encore."})
        if responsable and responsable.role == Role.COORDINATEUR:
            raise serializers.ValidationError({"responsable_utilisateur": "Le propriétaire du système ne peut pas être responsable d'une église."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        demandeur = self.context.get("request").user if self.context.get("request") else None
        creer = validated_data.pop("creer_compte_admin", True)
        admin_nom = validated_data.pop("admin_nom", "")
        admin_prenom = validated_data.pop("admin_prenom", "")
        admin_telephone = validated_data.pop("admin_telephone", "")
        admin_email = validated_data.pop("admin_email", "")
        admin_password = validated_data.pop("admin_mot_de_passe", "")
        validated_data.pop("admin_confirmation", None)
        # Champs responsables manuels déjà intégrés au modèle.
        eglise = Eglise.objects.create(**validated_data)
        compte = None
        sms_resultats = []

        if creer:
            compte = Utilisateur(
                nom=admin_nom, prenom=admin_prenom, telephone=admin_telephone,
                email=admin_email, role=Role.ADMIN_LOCAL, eglise=eglise, is_staff=False, actif=False,
            )
            compte.set_password(admin_password)
            compte.code_secret_clair = ""
            compte.save()

            from apps.accounts.models import VerificationTelephone
            from datetime import timedelta
            VerificationTelephone.objects.create(
                utilisateur=compte, code="000000", expire_le=timezone.now() + timedelta(minutes=10)
            )
            from apps.accounts.services_sms import notifier_nouvel_identifiant
            origine = eglise.nom
            sms_resultats = notifier_nouvel_identifiant(
                compte, admin_password, origine=origine
            )
            if not all(item.get("ok") for item in sms_resultats):
                raise serializers.ValidationError({
                    "admin_telephone": "Le compte administrateur a été refusé car les SMS n'ont pas pu être envoyés.",
                    "sms": [item.get("error") for item in sms_resultats if not item.get("ok")],
                })

            from apps.notifications.models import Notification
            Notification.objects.create(
                destinataire=compte, eglise=eglise, titre="Compte administrateur créé",
                message=f"Votre compte administrateur de {eglise.nom} est créé par le Bureau national. Confirmez votre téléphone avec le code reçu par SMS.",
                type_notification="BIENVENUE",
            )
        eglise._compte_admin_cree = compte
        eglise._sms_resultats = sms_resultats
        # Si aucun responsable utilisateur n'existe, le nom saisi reste la référence officielle provisoire.
        return eglise

    def get_compte_admin(self, obj):
        compte = getattr(obj, "_compte_admin_cree", None)
        if not compte:
            return None
        return {
            "identifiant": compte.identifiant,
            "nom_complet": f"{compte.prenom} {compte.nom}",
            "role": compte.role,
            "actif": compte.actif,
        }

    def get_sms(self, obj):
        resultats = getattr(obj, "_sms_resultats", None) or []
        if not resultats:
            return {"statut": "AUCUN"}
        return {
            "statut": "ENVOYE" if all(item.get("ok") for item in resultats) else "ECHEC",
            "messages": [{"type": i, "provider": r.get("provider"), "sid": r.get("sid")} for i, r in zip(("OTP", "BIENVENUE"), resultats)],
        }

