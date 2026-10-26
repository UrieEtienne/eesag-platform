from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    Utilisateur, Role, ROLES_NATIONAUX, generer_code_secret, Abonnement,
    VerificationTelephone, DelegationEglise, PermissionEglise, MandatBureauNational,
)
from .services_sms import notifier_nouvel_identifiant, normaliser_telephone


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
    """
    Utilisé par un administrateur (local ou national) pour enregistrer un nouveau
    membre/pasteur/admin. Génère automatiquement identifiant + code secret et
    déclenche l'envoi du SMS.
    """
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
        # L'administrateur local gère les membres de son église.
        # Les nominations de pasteurs restent nationales ; les admins locaux peuvent
        # être créés uniquement par le pasteur ou un rôle national.
        if demandeur.role == Role.ADMIN_LOCAL and role not in [Role.MEMBRE, Role.RESPONSABLE_DEPARTEMENT]:
            raise serializers.ValidationError({"role": "Vous n'avez pas le droit de créer ce rôle."})
        if demandeur.role == Role.PASTEUR and role not in [Role.MEMBRE, Role.RESPONSABLE_DEPARTEMENT, Role.ADMIN_LOCAL]:
            raise serializers.ValidationError({"role": "Le pasteur peut créer des membres, responsables de département et administrateurs locaux délégués."})
        if demandeur.role == Role.MEMBRE:
            raise serializers.ValidationError({"role": "Un membre ne peut pas créer de compte."})

        # Le Bureau national peut administrer les églises et nommer certains
        # responsables, mais il ne crée jamais les comptes des membres ordinaires
        # d'une église. Ceux-ci sont créés par l'église elle-même.
        if demandeur.role in ROLES_NATIONAUX and role in [Role.MEMBRE, Role.RESPONSABLE_DEPARTEMENT]:
            raise serializers.ValidationError({
                "role": "Seule l'église concernée peut créer les comptes de ses membres et responsables de département."
            })

        eglise_cible = attrs.get("eglise") or getattr(demandeur, "eglise", None)
        if demandeur.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
            if not eglise_cible or eglise_cible.id != demandeur.eglise_id:
                raise serializers.ValidationError({"eglise": "Le membre doit obligatoirement appartenir à votre église."})
        role_eglise = attrs.get("role_eglise")
        if role_eglise and not role_eglise.actif:
            raise serializers.ValidationError({"role_eglise": "Ce rôle dans l'église est désactivé."})
        return attrs

    def validate_role(self, role):
        return role

    @transaction.atomic
    def create(self, validated_data):
        demandeur = self.context["request"].user
        if demandeur.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
            validated_data["eglise"] = demandeur.eglise
        if demandeur.role not in ROLES_NATIONAUX and validated_data.get("eglise") and validated_data["eglise"] != demandeur.eglise:
            raise serializers.ValidationError("Vous ne pouvez agir que dans votre propre église.")

        import secrets
        from datetime import timedelta

        code_secret = generer_code_secret()
        try:
            validated_data["telephone"] = normaliser_telephone(validated_data.get("telephone"))
        except ValueError as exc:
            raise serializers.ValidationError({"telephone": str(exc)})
        if Utilisateur.objects.filter(telephone=validated_data["telephone"]).exists():
            raise serializers.ValidationError({"telephone": "Ce numéro est déjà enregistré."})
        utilisateur = Utilisateur(**validated_data, actif=False)
        utilisateur.code_secret_clair = ""
        utilisateur.set_password(code_secret)
        utilisateur.save()

        VerificationTelephone.objects.filter(utilisateur=utilisateur, utilise=False).update(utilise=True)
        origine = utilisateur.eglise.nom if utilisateur.eglise else "Bureau national EESAG"
        resultats = notifier_nouvel_identifiant(
            utilisateur, code_secret, origine=origine
        )
        erreurs = [item.get("error") for item in resultats if not item.get("ok")]

        from apps.notifications.models import Notification
        Notification.objects.create(
            destinataire=utilisateur,
            eglise=utilisateur.eglise,
            titre="Compte créé – confirmation SMS requise",
            message=(
                f"Votre compte EESAG a été créé par {origine}. "
                f"Identifiant : {utilisateur.identifiant}. "
                + (
                    "Un code de confirmation a été demandé par SMS. Confirmez votre téléphone avant de vous connecter."
                    if not erreurs
                    else "Votre compte reste en attente de confirmation. Demandez un nouveau code lorsque le service SMS est disponible."
                )
            ),
            type_notification="BIENVENUE",
        )
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
    """
    Inscription publique d'un membre déjà créé par son église.

    Le membre ne crée pas une nouvelle fiche Utilisateur.
    Il récupère la fiche existante grâce à son identifiant
    personnel, par exemple : EGL68301-000007.
    """

    identifiant = serializers.CharField(
        max_length=20,
        min_length=14,
        trim_whitespace=True,
    )
    telephone = serializers.CharField(max_length=20)
    password = serializers.CharField(
        write_only=True,
        min_length=6,
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        min_length=6,
    )
    email = serializers.EmailField(
        required=False,
        allow_blank=True,
    )

    def validate_identifiant(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        identifiant = attrs["identifiant"]

        user = (
            Utilisateur.objects
            .select_related("eglise")
            .filter(identifiant__iexact=identifiant)
            .first()
        )

        if not user:
            raise serializers.ValidationError({
                "identifiant": (
                    "Identifiant membre introuvable. "
                    "Utilisez l'identifiant fourni par votre église."
                )
            })

        # L'inscription publique concerne uniquement les membres
        # préalablement créés par l'église.
        if user.role != Role.MEMBRE:
            raise serializers.ValidationError({
                "identifiant": (
                    "Cet identifiant n'est pas celui d'un membre "
                    "autorisé à effectuer cette inscription."
                )
            })

        # Le compte doit être encore en attente d'activation.
        if user.actif:
            raise serializers.ValidationError({
                "identifiant": (
                    "Ce compte est déjà activé. "
                    "Vous pouvez vous connecter directement."
                )
            })

        if not user.eglise:
            raise serializers.ValidationError({
                "identifiant": "Ce compte n'est rattaché à aucune église."
            })

        # L'église doit être active.
        from apps.churches.models import Eglise

        if user.eglise.statut != Eglise.Statut.ACTIVE:
            raise serializers.ValidationError({
                "identifiant": "L'église associée à ce compte n'est pas active."
            })

        # La plateforme de l'église doit avoir été activée
        # par le Bureau national.
        if not user.eglise.plateforme_active:
            raise serializers.ValidationError({
                "identifiant": (
                    "La plateforme de votre église n'est pas encore "
                    "activée par le Bureau national."
                )
            })

        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError({
                "password_confirmation": (
                    "Les mots de passe ne correspondent pas."
                )
            })

        try:
            telephone = normaliser_telephone(attrs["telephone"])
        except ValueError as exc:
            raise serializers.ValidationError({
                "telephone": str(exc)
            })

        # Si le numéro appartient déjà à un AUTRE compte,
        # on refuse l'inscription.
        autre_utilisateur = (
            Utilisateur.objects
            .filter(telephone=telephone)
            .exclude(pk=user.pk)
            .first()
        )

        if autre_utilisateur:
            raise serializers.ValidationError({
                "telephone": "Ce numéro est déjà enregistré."
            })

        attrs["identifiant"] = user.identifiant
        attrs["utilisateur"] = user
        attrs["telephone"] = telephone

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = validated_data["utilisateur"]

        telephone = validated_data["telephone"]
        email = validated_data.get("email", "")
        password = validated_data["password"]

        # On met à jour la fiche créée précédemment
        # par l'administration de l'église.
        user.telephone = telephone
        user.email = email
        user.set_password(password)
        user.actif = False

        # Le rôle, l'église et l'identifiant existants
        # ne sont surtout pas modifiés.
        user.save(
            update_fields=[
                "telephone",
                "email",
                "password",
                "actif",
            ]
        )

        # Un ancien OTP non utilisé ne doit plus être prioritaire.
        VerificationTelephone.objects.filter(
            utilisateur=user,
            utilise=False,
        ).update(utilise=True)

        # Génère/envoyer un nouveau code OTP.
        from .services_sms import envoyer_otp

        result = envoyer_otp(
            user.telephone,
            utilisateur=user,
            creer_utilisateur=True,
            origine=(
                user.eglise.nom
                if user.eglise
                else "Bureau national EESAG"
            ),
        )

        if not result.get("ok"):
            raise serializers.ValidationError({
                "telephone": result.get(
                    "error",
                    "Impossible d'envoyer le code de confirmation."
                )
            })

        return user


class VerificationTelephoneSerializer(serializers.Serializer):
    identifiant = serializers.CharField()
    code = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        from .services_sms import verifier_otp_supabase

        verification = VerificationTelephone.objects.filter(
            utilisateur__identifiant=attrs["identifiant"],
            utilise=False,
            expire_le__gt=timezone.now(),
        ).select_related("utilisateur").order_by("-cree_le").first()

        if not verification or verification.tentatives >= 5:
            raise serializers.ValidationError("Aucun code de confirmation valide n'est disponible pour ce compte.")

        result = verifier_otp_supabase(verification.utilisateur.telephone, attrs["code"])
        if not result.get("ok"):
            verification.tentatives += 1
            verification.save(update_fields=["tentatives"])
            raise serializers.ValidationError(result.get("error", "Code de confirmation incorrect ou expiré."))

        attrs["verification"] = verification
        attrs["supabase_result"] = result
        return attrs


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
