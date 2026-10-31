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
    """
    Connexion EESAG avec identifiant et mot de passe.
    Aucun code d'église supplémentaire n'est demandé.
    """

    username_field = "identifiant"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["nom_complet"] = f"{user.prenom} {user.nom}"
        token["role"] = user.role
        token["eglise_id"] = user.eglise_id

        if user.eglise_id:
            token["code_eglise"] = user.eglise.code

        return token

    def validate(self, attrs):
        # Vérifier l'identifiant et le mot de passe avec Django.
        attrs = super().validate(attrs)
        user = self.user

        # Un compte inactif ne peut pas se connecter.
        if not user.actif:
            raise serializers.ValidationError({
                "detail": (
                    "Ce compte est inactif. "
                    "Si votre compte vient d'être créé, "
                    "confirmez d'abord votre numéro de téléphone. "
                    "Sinon, contactez l'administration."
                )
            })

        # Les rôles nationaux peuvent ne pas être rattachés à une église.
        roles_nationaux = {
            Role.COORDINATEUR,
            Role.SUPERADMIN_INTL,
            Role.SUPERADMIN_NATIONAL,
        }

        if user.role not in roles_nationaux and not user.eglise_id:
            raise serializers.ValidationError({
                "detail": "Votre compte n'est rattaché à aucune église."
            })

        # Conserver le format de réponse attendu par AuthContext.jsx.
        attrs["utilisateur"] = {
            "id": user.id,
            "identifiant": user.identifiant,
            "nom": user.nom,
            "prenom": user.prenom,
            "nom_complet": f"{user.prenom} {user.nom}",
            "role": user.role,
            "role_libelle": user.get_role_display(),
            "eglise_id": user.eglise_id,
            "eglise": user.eglise.nom if user.eglise else None,
            "code_eglise": user.eglise.code if user.eglise else None,
            "actif": user.actif,
        }

        return attrs


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
            "categorie_age", "telephone",  "photo", "nationalite", "date_bapteme_eau", "date_bapteme_saint_esprit", "fonction_eglise", "role", "role_libelle",
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
    Création administrative d'un compte utilisateur.

    Le compte est créé inactif.
    L'identifiant et le code secret sont générés automatiquement.
    L'envoi SMS est une notification secondaire : une panne SMS
    ne doit jamais empêcher la création du compte.
    """

    class Meta:
        model = Utilisateur
        fields = [
            "nom",
            "prenom",
            "sexe",
            "date_naissance",
            "telephone",
            
            "photo",
            "nationalite",
            "date_bapteme_eau",
            "date_bapteme_saint_esprit",
            "fonction_eglise",
            "role",
            "eglise",
            "departement",
            "role_eglise",
            "fonction_bureau_national",
        ]

    def validate(self, attrs):
        demandeur = self.context["request"].user
        role = attrs.get("role", Role.MEMBRE)

        if not demandeur.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Vous devez être authentifié."}
            )

        # ---------------------------------------------------------
        # MEMBRE
        # ---------------------------------------------------------
        if demandeur.role == Role.MEMBRE:
            raise serializers.ValidationError(
                {"role": "Un membre ne peut pas créer de compte."}
            )

        # ---------------------------------------------------------
        # ADMIN LOCAL
        # ---------------------------------------------------------
        if demandeur.role == Role.ADMIN_LOCAL:
            roles_autorises = {
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
                Role.RESPONSABLE_DEPARTEMENT,
                Role.MEMBRE,
            }

            if role not in roles_autorises:
                raise serializers.ValidationError(
                    {
                        "role": (
                            "Un administrateur local ne peut créer que "
                            "des comptes locaux autorisés."
                        )
                    }
                )

        # ---------------------------------------------------------
        # PASTEUR
        # ---------------------------------------------------------
        elif demandeur.role == Role.PASTEUR:
            roles_autorises = {
                Role.ADMIN_LOCAL,
                Role.RESPONSABLE_DEPARTEMENT,
                Role.MEMBRE,
            }

            if role not in roles_autorises:
                raise serializers.ValidationError(
                    {
                        "role": (
                            "Le pasteur peut créer des membres, "
                            "responsables de département et administrateurs locaux."
                        )
                    }
                )

        # ---------------------------------------------------------
        # COORDINATEUR
        # ---------------------------------------------------------
        elif demandeur.role == Role.COORDINATEUR or demandeur.is_superuser:
            roles_autorises = {
                Role.SUPERADMIN_INTL,
                Role.SUPERADMIN_NATIONAL,
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            }

            if role not in roles_autorises:
                raise serializers.ValidationError(
                    {
                        "role": (
                            "Le Coordinateur peut créer les comptes "
                            "administratifs nationaux et les comptes "
                            "administratifs d'église."
                        )
                    }
                )

        # ---------------------------------------------------------
        # BUREAU NATIONAL
        # ---------------------------------------------------------
        elif demandeur.role in ROLES_NATIONAUX:
            roles_autorises = {
                Role.SUPERADMIN_NATIONAL,
                Role.ADMIN_LOCAL,
                Role.PASTEUR,
            }

            if role not in roles_autorises:
                raise serializers.ValidationError(
                    {
                        "role": (
                            "Ce bureau national ne peut pas créer ce type "
                            "de compte."
                        )
                    }
                )

        else:
            raise serializers.ValidationError(
                {"role": "Vous n'avez pas le droit de créer un compte."}
            )

        # ---------------------------------------------------------
        # ÉGLISE
        # ---------------------------------------------------------
        eglise_cible = attrs.get("eglise")

        if demandeur.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
            if not eglise_cible:
                eglise_cible = demandeur.eglise

            if not eglise_cible:
                raise serializers.ValidationError(
                    {
                        "eglise": (
                            "Une église est obligatoire pour ce type "
                            "de compte."
                        )
                    }
                )

            if eglise_cible.id != demandeur.eglise_id:
                raise serializers.ValidationError(
                    {
                        "eglise": (
                            "Vous ne pouvez créer un compte que "
                            "dans votre propre église."
                        )
                    }
                )

            attrs["eglise"] = eglise_cible

        # Les rôles nationaux n'appartiennent pas à une église.
        if role in {
            Role.SUPERADMIN_INTL,
            Role.SUPERADMIN_NATIONAL,
        }:
            attrs["eglise"] = None
            attrs["departement"] = None
            attrs["role_eglise"] = None

        role_eglise = attrs.get("role_eglise")

        if role_eglise and not role_eglise.actif:
            raise serializers.ValidationError(
                {
                    "role_eglise": (
                        "Ce rôle dans l'église est désactivé."
                    )
                }
            )

        return attrs

    def validate_telephone(self, telephone):
        try:
            numero = normaliser_telephone(telephone)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

        if Utilisateur.objects.filter(telephone=numero).exists():
            raise serializers.ValidationError(
                "Ce numéro est déjà enregistré."
            )

        return numero

    @transaction.atomic
    def create(self, validated_data):
        demandeur = self.context["request"].user

        if demandeur.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
            validated_data["eglise"] = demandeur.eglise

        role = validated_data.get("role", Role.MEMBRE)

        code_secret = generer_code_secret()

        staff_role = role in ROLES_NATIONAUX

        utilisateur = Utilisateur(
            **validated_data,
            actif=False,
            is_staff=staff_role,
        )

        utilisateur.code_secret_clair = ""
        utilisateur.set_password(code_secret)
        utilisateur.save()

        origine = (
            utilisateur.eglise.nom
            if utilisateur.eglise
            else "Bureau national EESAG"
        )

        # ---------------------------------------------------------
        # SMS : NON BLOQUANT
        # ---------------------------------------------------------
        sms_ok = False
        sms_message = ""

        try:
            resultats = notifier_nouvel_identifiant(
                utilisateur,
                code_secret,
                origine=origine,
            )

            otp_result = (
                resultats[0]
                if resultats
                else {"ok": False, "error": "Aucun résultat SMS."}
            )

            sms_ok = bool(otp_result.get("ok"))

            if not sms_ok:
                sms_message = otp_result.get(
                    "error",
                    "Le SMS n'a pas pu être envoyé.",
                )

        except Exception as exc:
            sms_message = str(exc)

        # ---------------------------------------------------------
        # NOTIFICATION INTERNE
        # ---------------------------------------------------------
        try:
            from apps.notifications.models import Notification

            Notification.objects.create(
                destinataire=utilisateur,
                eglise=utilisateur.eglise,
                titre="Compte EESAG créé",
                message=(
                    f"Votre compte EESAG a été créé pour {origine}. "
                    f"Identifiant : {utilisateur.identifiant}. "
                    "Votre compte doit être activé avant connexion."
                ),
                type_notification="BIENVENUE",
            )
        except Exception:
            pass

        # Informations disponibles pour la réponse API.
        utilisateur._creation_sms_ok = sms_ok
        utilisateur._creation_sms_message = sms_message
        utilisateur._creation_code_secret = code_secret

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
    Permet à un membre déjà enregistré par l'administration
    d'activer lui-même son compte avec son identifiant personnel.

    Exemple :
        EGL68301-000007
    """

    identifiant = serializers.CharField(
        max_length=20,
        trim_whitespace=True,
    )

    telephone = serializers.CharField(
        max_length=20,
        trim_whitespace=True,
    )

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

    def validate(self, attrs):
        identifiant = attrs["identifiant"].strip().upper()

        # ---------------------------------------------------------
        # 1. RETROUVER LE COMPTE EXISTANT
        # ---------------------------------------------------------
        try:
            utilisateur = (
                Utilisateur.objects
                .select_related("eglise")
                .get(identifiant=identifiant)
            )
        except Utilisateur.DoesNotExist:
            raise serializers.ValidationError({
                "identifiant": (
                    "Identifiant membre introuvable. "
                    "Utilisez l'identifiant personnel fourni par votre église."
                )
            })

        # ---------------------------------------------------------
        # 2. SEUL UN MEMBRE PEUT UTILISER CETTE INSCRIPTION
        # ---------------------------------------------------------
        if utilisateur.role != Role.MEMBRE:
            raise serializers.ValidationError({
                "identifiant": (
                    "Cet identifiant n'est pas celui d'un membre. "
                    "Utilisez la connexion normale."
                )
            })

        # ---------------------------------------------------------
        # 3. LE COMPTE NE DOIT PAS ÊTRE DÉJÀ ACTIVÉ
        # ---------------------------------------------------------
        if utilisateur.actif:
            raise serializers.ValidationError({
                "identifiant": (
                    "Ce compte est déjà activé. "
                    "Utilisez directement la page de connexion."
                )
            })

        # ---------------------------------------------------------
        # 4. LE MEMBRE DOIT ÊTRE RATTACHÉ À UNE ÉGLISE
        # ---------------------------------------------------------
        if not utilisateur.eglise_id:
            raise serializers.ValidationError({
                "identifiant": (
                    "Ce compte n'est rattaché à aucune église."
                )
            })

        eglise = utilisateur.eglise

        # ---------------------------------------------------------
        # 5. L'ÉGLISE DOIT ÊTRE ACTIVE
        # ---------------------------------------------------------
        if eglise.statut != eglise.Statut.ACTIVE:
            raise serializers.ValidationError({
                "identifiant": (
                    "L'église associée à ce compte n'est pas active."
                )
            })

        # ---------------------------------------------------------
        # 6. LA PLATEFORME DOIT ÊTRE ACTIVÉE
        # ---------------------------------------------------------
        if not eglise.plateforme_active:
            raise serializers.ValidationError({
                "identifiant": (
                    "La plateforme de votre église n'est pas encore "
                    "activée par le Bureau national."
                )
            })

        # ---------------------------------------------------------
        # 7. VÉRIFIER LE MOT DE PASSE
        # ---------------------------------------------------------
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError({
                "password_confirmation": (
                    "Les deux codes secrets ne correspondent pas."
                )
            })

        # ---------------------------------------------------------
        # 8. NORMALISER LE TÉLÉPHONE
        # ---------------------------------------------------------
        try:
            telephone = normaliser_telephone(attrs["telephone"])
        except ValueError as exc:
            raise serializers.ValidationError({
                "telephone": str(exc)
            })

        # ---------------------------------------------------------
        # 9. LE TÉLÉPHONE DOIT ÊTRE CELUI DÉJÀ ENREGISTRÉ
        # ---------------------------------------------------------
        try:
            telephone_compte = normaliser_telephone(
                utilisateur.telephone
            )
        except ValueError:
            telephone_compte = utilisateur.telephone

        if telephone != telephone_compte:
            raise serializers.ValidationError({
                "telephone": (
                    "Le numéro de téléphone ne correspond pas "
                    "à celui enregistré pour cet identifiant membre."
                )
            })

        # ---------------------------------------------------------
        # 10. EMAIL FACULTATIF
        # ---------------------------------------------------------
        email = (attrs.get("email") or "").strip()

        attrs["identifiant"] = identifiant
        attrs["utilisateur"] = utilisateur
        attrs["telephone"] = telephone
        attrs["email"] = email

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        utilisateur = validated_data["utilisateur"]

        password = validated_data["password"]
        email = (validated_data.get("email") or "").strip()

        # ---------------------------------------------------------
        # IMPORTANT :
        # ON MODIFIE LE COMPTE EXISTANT.
        # ON NE CRÉE PAS UN NOUVEL UTILISATEUR.
        # ---------------------------------------------------------

        utilisateur.set_password(password)

        if email:
            utilisateur.email = email

        # Le compte reste inactif jusqu'à confirmation OTP.
        utilisateur.actif = False
        utilisateur.is_staff = False

        # Le téléphone est déjà celui du compte.
        utilisateur.save(
            update_fields=[
                "password",
                "email",
                
                "actif",
                "is_staff",
            ]
        )

        # ---------------------------------------------------------
        # ENVOI DU CODE OTP
        # ---------------------------------------------------------
        from .services_sms import envoyer_otp

        origine = (
            utilisateur.eglise.nom
            if utilisateur.eglise
            else "EESAG"
        )

        result = envoyer_otp(
            utilisateur.telephone,
            utilisateur=utilisateur,
            origine=origine,
        )

        # Si l'envoi SMS échoue, on laisse l'inscription en attente.
        # L'utilisateur pourra demander un nouveau code.
        if not result.get("ok"):
            # On ne bloque pas la création du compte.
            # Le compte reste simplement inactif.
            pass

        return utilisateur

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
        fields = ["id","identifiant","nom","prenom","sexe","date_naissance","telephone","photo","nationalite","date_bapteme_eau","date_bapteme_saint_esprit","fonction_eglise","eglise","eglise_nom","departement","role","nom_complet"]
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
