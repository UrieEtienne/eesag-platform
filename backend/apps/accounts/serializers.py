from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    Utilisateur, Role, ROLES_NATIONAUX, generer_code_secret, Abonnement,
    VerificationTelephone, DelegationEglise, PermissionEglise, MandatBureauNational,
)
from .services_sms import notifier_nouvel_identifiant, normaliser_telephone, envoyer_sms_detail


class LoginSerializer(TokenObtainPairSerializer):
    """Connexion par identifiant + code secret (le champ 'password' = code secret)."""
    username_field = "identifiant"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["nom_complet"] = f"{user.prenom} {user.nom}"
        token["role"] = user.role
        token["eglise_id"] = user.eglise_id
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.actif:
            raise serializers.ValidationError("Votre compte n'est pas encore activé. Confirmez d'abord votre numéro de téléphone.")

        # Une église doit aussi être activée par le Bureau national avant
        # qu'un compte local puisse accéder à la plateforme.
        if (
            self.user.eglise_id
            and self.user.role in {
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
                Role.MEMBRE,
                Role.RESPONSABLE_DEPARTEMENT,
            }
            and not self.user.eglise.plateforme_active
        ):
            raise serializers.ValidationError(
                "La plateforme de votre église n'est pas encore activée par le Bureau national."
            )

        data["utilisateur"] = UtilisateurSerializer(self.user).data
        return data


class UtilisateurSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField()
    role_libelle = serializers.CharField(source="get_role_display", read_only=True)
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True, default=None)
    categorie_age = serializers.CharField(read_only=True)
    departement_nom = serializers.CharField(source="departement.nom", read_only=True, default=None)
    role_eglise_nom = serializers.CharField(source="role_eglise.nom", read_only=True, default=None)

    class Meta:
        model = Utilisateur
        fields = [
            "id", "identifiant", "nom", "prenom", "nom_complet", "sexe", "date_naissance",
            "categorie_age", "telephone", "email", "photo", "nationalite", "date_bapteme_eau", "date_bapteme_saint_esprit", "fonction_eglise", "role", "role_libelle",
            "eglise", "eglise_nom", "departement", "departement_nom", "role_eglise", "role_eglise_nom", "fonction_bureau_national",
            "date_enregistrement", "actif",
        ]
        read_only_fields = ["id", "identifiant", "date_enregistrement"]

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_authenticated and request.user.role not in ROLES_NATIONAUX:
            role = attrs.get("role", self.instance.role if self.instance else Role.MEMBRE)
            eglise = attrs.get("eglise", self.instance.eglise if self.instance else request.user.eglise)
            if role not in [Role.MEMBRE, Role.RESPONSABLE_DEPARTEMENT]:
                raise serializers.ValidationError({"role": "Ce rôle est réservé au bureau national."})
            if eglise and eglise.id != request.user.eglise_id:
                raise serializers.ValidationError({"eglise": "Vous ne pouvez agir que dans votre propre église."})
        return attrs

    def get_nom_complet(self, obj):
        return f"{obj.prenom} {obj.nom}"


class CreerUtilisateurSerializer(serializers.ModelSerializer):
    """Création d'un compte inactif jusqu'à la validation OTP."""
    class Meta:
        model = Utilisateur
        fields = [
            "nom", "prenom", "sexe", "date_naissance", "telephone", "email", "photo",
            "nationalite", "date_bapteme_eau", "date_bapteme_saint_esprit", "fonction_eglise",
            "role", "eglise", "departement", "role_eglise", "fonction_bureau_national",
        ]

    def validate(self, attrs):
        demandeur = self.context["request"].user
        role = attrs.get("role", Role.MEMBRE)
        if demandeur.role == Role.MEMBRE:
            raise serializers.ValidationError({"role": "Un membre ne peut pas créer de compte."})
        if demandeur.role == Role.ADMIN_LOCAL and role not in [Role.MEMBRE, Role.RESPONSABLE_DEPARTEMENT]:
            raise serializers.ValidationError({"role": "Vous n'avez pas le droit de créer ce rôle."})
        if demandeur.role == Role.PASTEUR and role not in [Role.MEMBRE, Role.RESPONSABLE_DEPARTEMENT, Role.ADMIN_LOCAL]:
            raise serializers.ValidationError({"role": "Le pasteur peut créer des membres, responsables de département et administrateurs locaux délégués."})
        if demandeur.role in ROLES_NATIONAUX and role in [Role.MEMBRE, Role.RESPONSABLE_DEPARTEMENT]:
            raise serializers.ValidationError({"role": "Seule l'église concernée peut créer les comptes de ses membres et responsables de département."})
        eglise_cible = attrs.get("eglise") or getattr(demandeur, "eglise", None)
        if demandeur.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
            if not eglise_cible or eglise_cible.id != demandeur.eglise_id:
                raise serializers.ValidationError({"eglise": "Le membre doit obligatoirement appartenir à votre église."})
            attrs["eglise"] = eglise_cible
        role_eglise = attrs.get("role_eglise")
        if role_eglise and not role_eglise.actif:
            raise serializers.ValidationError({"role_eglise": "Ce rôle dans l'église est désactivé."})
        return attrs

    def validate_telephone(self, telephone):
        try:
            numero = normaliser_telephone(telephone)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        if Utilisateur.objects.filter(telephone=numero).exists():
            raise serializers.ValidationError("Ce numéro est déjà enregistré.")
        return numero

    @transaction.atomic
    def create(self, validated_data):
        demandeur = self.context["request"].user
        if demandeur.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
            validated_data["eglise"] = demandeur.eglise
        if demandeur.role not in ROLES_NATIONAUX and validated_data.get("eglise") and validated_data["eglise"] != demandeur.eglise:
            raise serializers.ValidationError("Vous ne pouvez agir que dans votre propre église.")
        code_secret = generer_code_secret()
        role = validated_data.get("role", Role.MEMBRE)
        staff_role = role in ROLES_NATIONAUX
        utilisateur = Utilisateur(**validated_data, actif=False, is_staff=staff_role)
        utilisateur.code_secret_clair = ""
        utilisateur.set_password(code_secret)
        utilisateur.save()
        origine = utilisateur.eglise.nom if utilisateur.eglise else "Bureau national EESAG"
        resultats = notifier_nouvel_identifiant(utilisateur, code_secret, origine=origine)
        otp_result = resultats[0] if resultats else {"ok": False, "error": "Aucun résultat OTP."}
        if not otp_result.get("ok"):
            raise serializers.ValidationError({"telephone": otp_result.get("error", "Impossible de générer le code de confirmation.")})
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                destinataire=utilisateur,
                eglise=utilisateur.eglise,
                titre="Compte créé – confirmation du téléphone",
                message=(f"Votre compte EESAG a été créé pour {origine}. "
                         f"Identifiant : {utilisateur.identifiant}. "
                         "Confirmez votre numéro pour activer le compte."),
                type_notification="BIENVENUE",
            )
        except Exception:
            pass
        return utilisateur


class ChangerCodeSecretSerializer(serializers.Serializer):
    ancien_code = serializers.CharField()
    nouveau_code = serializers.CharField(min_length=4)

    def validate_ancien_code(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien code secret incorrect.")
        return value


class AbonnementSerializer(serializers.ModelSerializer):
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True)

    class Meta:
        model = Abonnement
        fields = ["id", "eglise", "eglise_nom", "date_abonnement"]


class InscriptionMembreSerializer(serializers.Serializer):
    nom = serializers.CharField(max_length=100)
    prenom = serializers.CharField(max_length=100)
    telephone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirmation = serializers.CharField(write_only=True, min_length=6)
    code_eglise = serializers.CharField(max_length=10)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        from apps.churches.models import Eglise
        eglise = Eglise.objects.filter(code__iexact=attrs["code_eglise"], statut=Eglise.Statut.ACTIVE).first()
        if not eglise:
            raise serializers.ValidationError({"code_eglise": "Code d’église invalide ou église inactive."})
        if not eglise.plateforme_active:
            raise serializers.ValidationError({"code_eglise": "Cette église n’est pas encore activée par le Bureau national."})
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError({"password_confirmation": "Les codes secrets ne correspondent pas."})
        try:
            attrs["telephone"] = normaliser_telephone(attrs["telephone"])
        except ValueError as exc:
            raise serializers.ValidationError({"telephone": str(exc)})
        if Utilisateur.objects.filter(telephone=attrs["telephone"]).exists():
            raise serializers.ValidationError({"telephone": "Ce numéro est déjà enregistré."})
        attrs["eglise"] = eglise
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        password = validated_data.pop("password")
        eglise = validated_data.pop("eglise")
        user = Utilisateur(
            **validated_data, eglise=eglise, role=Role.MEMBRE, actif=False, is_staff=False,
        )
        user.set_password(password)
        user.save()
        from .services_sms import notifier_nouvel_identifiant, normaliser_telephone, envoyer_sms_detail
        resultats = notifier_nouvel_identifiant(
            user, "le mot de passe que vous avez choisi", origine=eglise.nom
        )
        return user


class VerificationTelephoneSerializer(serializers.Serializer):
    identifiant = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        identifiant = attrs["identifiant"].strip()
        code = str(attrs["code"] or "").strip()
        if not code.isdigit() or len(code) != 6:
            raise serializers.ValidationError({"code": "Le code doit contenir exactement 6 chiffres."})
        try:
            utilisateur = Utilisateur.objects.get(identifiant=identifiant)
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError({"identifiant": "Identifiant de compte invalide."})
        if utilisateur.actif:
            raise serializers.ValidationError({"code": "Ce compte est déjà activé."})
        verification = VerificationTelephone.objects.filter(
            utilisateur=utilisateur, utilise=False, expire_le__gt=timezone.now()
        ).order_by("-cree_le").first()
        if not verification:
            raise serializers.ValidationError({"code": "Aucun code de confirmation valide n'est disponible. Demandez un nouveau code."})
        if verification.tentatives >= 5:
            raise serializers.ValidationError({"code": "Nombre maximal de tentatives atteint. Demandez un nouveau code."})
        if verification.code != code:
            verification.tentatives += 1
            verification.save(update_fields=["tentatives"])
            raise serializers.ValidationError({"code": "Code de confirmation incorrect."})
        attrs["utilisateur"] = utilisateur
        attrs["verification"] = verification
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        utilisateur = self.validated_data["utilisateur"]
        verification = self.validated_data["verification"]
        verification.utilise = True
        verification.save(update_fields=["utilise"])
        utilisateur.actif = True
        utilisateur.is_staff = (
            utilisateur.role in ROLES_NATIONAUX
            or (
                utilisateur.role in {Role.ADMIN_LOCAL, Role.PASTEUR}
                and bool(utilisateur.eglise_id and utilisateur.eglise.plateforme_active)
            )
        )
        utilisateur.save(update_fields=["actif", "is_staff"])
        origine = utilisateur.eglise.nom if utilisateur.eglise else "Bureau national EESAG"
        envoyer_sms_detail(
            utilisateur.telephone,
            ("Merci pour votre inscription. Votre compte EESAG a été créé avec succès. "
             f"Identifiant : {utilisateur.identifiant}."),
            type_message="BIENVENUE",
            utilisateur=utilisateur,
            origine=origine,
        )
        return utilisateur


class PermissionEgliseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionEglise
        fields = ["id", "code", "libelle", "description"]


class DelegationEgliseSerializer(serializers.ModelSerializer):
    permissions_detail = PermissionEgliseSerializer(source="permissions", many=True, read_only=True)
    def validate_utilisateur(self, value):
        if value.role != Role.ADMIN_LOCAL:
            raise serializers.ValidationError("Une délégation ne peut être attribuée qu'à un administrateur local.")
        return value
    class Meta:
        model = DelegationEglise
        fields = ["id", "utilisateur", "permissions", "permissions_detail", "cree_par", "date_creation", "actif"]
        read_only_fields = ["cree_par", "date_creation"]


class ProfilSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField(read_only=True)
    eglise_nom = serializers.CharField(source="eglise.nom", read_only=True, default=None)
    class Meta:
        model = Utilisateur
        fields = ["id","identifiant","nom","prenom","sexe","date_naissance","telephone","email","photo","nationalite","date_bapteme_eau","date_bapteme_saint_esprit","fonction_eglise","eglise","eglise_nom","departement","role","nom_complet"]
        read_only_fields = ["id","identifiant","eglise","departement","role","nom_complet"]
    def get_nom_complet(self,obj): return f"{obj.prenom} {obj.nom}"


class MandatBureauNationalSerializer(serializers.ModelSerializer):
    nom_complet = serializers.SerializerMethodField(read_only=True)
    photo = serializers.ImageField(source="utilisateur.photo", read_only=True)
    class Meta:
        model = MandatBureauNational
        fields = ["id","annee","utilisateur","nom_complet","photo","poste","actif","date_nomination"]
        read_only_fields = ["date_nomination"]
    def get_nom_complet(self,obj): return f"{obj.utilisateur.prenom} {obj.utilisateur.nom}"
