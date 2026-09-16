from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import Utilisateur, Role
from .models import Religion, Eglise, Departement, RoleEglise, Annexe
from apps.accounts.services_sms import normaliser_telephone


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
            "statut", "plateforme_active", "responsable", "responsable_nom", "responsable_source", "nombre_membres", "logo",
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
        fields = ["id", "code", "nom", "religion_nom", "region_nom", "prefecture_nom", "district_nom", "commune_nom", "statut", "plateforme_active"]
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
    admin_identifiant = serializers.SerializerMethodField(read_only=True)
    admin_code_secret_initial = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Eglise
        fields = [
            "id", "code", "nom", "religion", "region", "prefecture", "district", "commune",
            "adresse_precise", "telephone", "email", "date_creation", "statut", "plateforme_active", "logo",
            "responsable_utilisateur", "responsable_nom", "responsable_telephone", "responsable_email",
            "creer_compte_admin", "admin_nom", "admin_prenom", "admin_telephone", "admin_email",
            "admin_mot_de_passe", "admin_confirmation", "compte_admin", "sms",
            "admin_identifiant", "admin_code_secret_initial",
        ]
        read_only_fields = ["id", "code", "statut", "plateforme_active"]

    def validate(self, attrs):
        creer = attrs.get("creer_compte_admin", True)
        champs = [attrs.get("admin_nom"), attrs.get("admin_prenom"), attrs.get("admin_telephone"), attrs.get("admin_mot_de_passe"), attrs.get("admin_confirmation")]
        if creer and any(not value for value in champs):
            raise serializers.ValidationError("Les informations de l'administrateur local sont obligatoires.")
        if creer and attrs.get("admin_mot_de_passe") != attrs.get("admin_confirmation"):
            raise serializers.ValidationError({"admin_confirmation": "Les mots de passe ne correspondent pas."})
        if creer:
            validate_password(attrs["admin_mot_de_passe"])
            try:
                numero_admin = normaliser_telephone(attrs["admin_telephone"])
            except ValueError as exc:
                raise serializers.ValidationError({"admin_telephone": str(exc)})
            attrs["admin_telephone"] = numero_admin
            if Utilisateur.objects.filter(telephone=numero_admin).exists():
                raise serializers.ValidationError({"admin_telephone": "Ce numéro est déjà utilisé."})
        responsable = attrs.get("responsable")
        responsable_nom = attrs.get("responsable_nom", "").strip()

        # Pour simplifier la création : si un administrateur local est créé
        # en même temps que l'église, ses informations servent aussi de
        # responsable provisoire. L'utilisateur n'a donc pas à saisir deux fois
        # les mêmes informations.
        if creer and not responsable and not responsable_nom:
            responsable_nom = f"{attrs.get('admin_prenom', '')} {attrs.get('admin_nom', '')}".strip()
            attrs["responsable_nom"] = responsable_nom
            attrs["responsable_telephone"] = attrs.get("admin_telephone", "")
            attrs["responsable_email"] = attrs.get("admin_email", "")

        if not responsable and not responsable_nom:
            raise serializers.ValidationError({"responsable_nom": "Saisissez le nom du responsable ou créez le compte administrateur local en même temps."})

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
        # Une création d'église ne peut jamais activer la plateforme.
        # L'activation est une opération exclusivement administrative du Bureau national.
        eglise.plateforme_active = False
        eglise.date_activation_plateforme = None
        eglise.activee_par = None
        eglise.save(update_fields=["plateforme_active", "date_activation_plateforme", "activee_par"])
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
            # Mot de passe transmis une seule fois dans la réponse de création.
            # Il n'est jamais enregistré en clair dans la base de données.
            compte._code_secret_initial = admin_password

            from apps.accounts.services_sms import notifier_nouvel_identifiant
            origine = eglise.nom
            sms_resultats = notifier_nouvel_identifiant(
                compte, admin_password, origine=origine
            )

            # Le compte est bien créé, mais reste inactif tant que le téléphone
            # n'est pas confirmé. Une panne temporaire du fournisseur SMS ne
            # doit pas supprimer l'église ni le compte administrateur.
            erreurs_sms = [item.get("error") for item in sms_resultats if not item.get("ok")]

            from apps.notifications.models import Notification
            Notification.objects.create(
                destinataire=compte, eglise=eglise, titre="Compte administrateur créé",
                message=(
                    f"Votre compte administrateur de {eglise.nom} a été créé par le Bureau national. "
                    + (
                        "Un code de confirmation a été demandé par SMS. Confirmez votre téléphone avant de vous connecter."
                        if not erreurs_sms
                        else "Le compte est en attente de confirmation téléphonique. Un nouveau code pourra être demandé depuis l'écran de confirmation."
                    )
                ),
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
            "code_secret_initial": getattr(compte, "_code_secret_initial", None),
        }

    def get_admin_identifiant(self, obj):
        compte = getattr(obj, "_compte_admin_cree", None)
        return compte.identifiant if compte else None

    def get_admin_code_secret_initial(self, obj):
        compte = getattr(obj, "_compte_admin_cree", None)
        return getattr(compte, "_code_secret_initial", None) if compte else None

    def get_sms(self, obj):
        resultats = getattr(obj, "_sms_resultats", None) or []
        if not resultats:
            return {"statut": "AUCUN"}
        return {
            "statut": "ENVOYE" if all(item.get("ok") for item in resultats) else "EN_ATTENTE",
            "messages": [
                {
                    "type": "OTP",
                    "provider": r.get("provider"),
                    "sid": r.get("message_sid") or r.get("sid") or r.get("supabase_user_id"),
                    "to": r.get("to"),
                    "test_code": r.get("test_code"),
                    "error": r.get("error"),
                }
                for r in resultats
            ],
        }

