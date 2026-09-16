from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, generics, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Utilisateur, Role, ROLES_NATIONAUX, Abonnement, MandatBureauNational,
    VerificationTelephone, PermissionEglise, DelegationEglise,
)
from .permissions import EstAdminLocalOuPlus, EstSuperAdminNationalOuPlus
from .serializers import (
    LoginSerializer, UtilisateurSerializer, CreerUtilisateurSerializer,
    ChangerCodeSecretSerializer, AbonnementSerializer, InscriptionMembreSerializer, VerificationTelephoneSerializer, DelegationEgliseSerializer, PermissionEgliseSerializer, ProfilSerializer, MandatBureauNationalSerializer,
)


class LoginView(TokenObtainPairView):
    """POST { identifiant, password } -> access, refresh, utilisateur."""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]


class MoiView(generics.RetrieveAPIView):
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangerCodeSecretView(generics.GenericAPIView):
    serializer_class = ChangerCodeSecretSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["nouveau_code"])
        request.user.code_secret_clair = ""
        request.user.save()
        return Response({"detail": "Code secret mis à jour."})


class UtilisateurViewSet(viewsets.ModelViewSet):
    """
    CRUD des utilisateurs (membres, pasteurs, admins...).
    - Un ADMIN_LOCAL / PASTEUR ne voit et ne gère que les membres de SA propre église.
    - Les rôles nationaux voient/gèrent tout le monde.
    - Un simple MEMBRE ne peut que se consulter lui-même (lecture seule via /moi/).
    """
    serializer_class = UtilisateurSerializer
    permission_classes = [EstAdminLocalOuPlus]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["role", "eglise", "departement", "sexe", "actif"]
    search_fields = ["nom", "prenom", "identifiant", "telephone"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreerUtilisateurSerializer
        return UtilisateurSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Utilisateur.objects.select_related("eglise", "departement", "role_eglise")
        if user.role == Role.COORDINATEUR or user.is_superuser:
            return qs.exclude(role=Role.COORDINATEUR)
        if user.role in [Role.SUPERADMIN_INTL, Role.SUPERADMIN_NATIONAL]:
            from apps.bureaux.models import BureauAdministrateur
            assigned = BureauAdministrateur.objects.filter(utilisateur=user, actif=True).values_list("bureau_id", flat=True)
            if assigned.exists():
                # Un bureau national spécialisé n'utilise pas la gestion des comptes d'église.
                return qs.none()
            # Le Bureau national général ne gère que les comptes locaux d'églises.
            return qs.filter(role__in=[Role.ADMIN_LOCAL, Role.PASTEUR]).exclude(role=Role.COORDINATEUR)
        return qs.filter(eglise_id=user.eglise_id).exclude(role=Role.COORDINATEUR)


class RechercheMembreView(generics.ListAPIView):
    """
    Page principale de recherche d'un membre par identifiant ou par nom,
    accessible à tout utilisateur connecté (résultats limités aux infos publiques).
    """
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        terme = self.request.query_params.get("q", "").strip()
        qs = Utilisateur.objects.select_related("eglise")
        if not terme:
            return qs.none()
        user = self.request.user
        if user.role == Role.COORDINATEUR or user.is_superuser:
            scope = qs.exclude(role=Role.COORDINATEUR)
        elif user.role in [Role.SUPERADMIN_INTL, Role.SUPERADMIN_NATIONAL]:
            from apps.bureaux.models import BureauAdministrateur
            assigned = BureauAdministrateur.objects.filter(utilisateur=user, actif=True).values_list("bureau_id", flat=True)
            if assigned.exists():
                scope = qs.filter(mandats_bureaux__bureau_id__in=assigned, mandats_bureaux__actif=True).exclude(role=Role.COORDINATEUR).distinct()
            else:
                scope = qs.exclude(role=Role.COORDINATEUR)
        else:
            scope = qs.filter(eglise_id=user.eglise_id).exclude(role=Role.COORDINATEUR)
        return scope.filter(
            Q(identifiant__icontains=terme) | Q(nom__icontains=terme) | Q(prenom__icontains=terme)
        )[:30]


class BureauNationalView(generics.ListAPIView):
    """Liste publique (à tout utilisateur connecté) du bureau national avec photo/nom/fonction."""
    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Utilisateur.objects.filter(role__in=ROLES_BUREAU_NATIONAL, eglise__isnull=True, actif=True).order_by("fonction_bureau_national", "nom", "prenom")


class AbonnementViewSet(viewsets.ModelViewSet):
    serializer_class = AbonnementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Abonnement.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class InscriptionMembreView(generics.CreateAPIView):
    serializer_class = InscriptionMembreSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = {"detail": "Compte créé. Confirmez votre numéro pour terminer l'inscription.", "identifiant": user.identifiant, "eglise": user.eglise.nom}
        from django.conf import settings
        if not getattr(settings, "SMS_ENABLED", False):
            verification = user.verifications_telephone.filter(utilise=False).order_by("-cree_le").first()
            if verification:
                data.update({"test_mode": True, "test_code": verification.code, "sms": "Mode test : aucun SMS réel n'est envoyé. Utilisez le code affiché pour continuer."})
        else:
            data["sms"] = "Un code de confirmation a été envoyé par SMS."
        return Response(data, status=status.HTTP_201_CREATED)


class VerificationTelephoneView(generics.GenericAPIView):
    serializer_class = VerificationTelephoneSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        data = {"detail": "Compte confirmé et activé.", "access": str(refresh.access_token), "refresh": str(refresh), "utilisateur": UtilisateurSerializer(user).data}
        from django.conf import settings
        if not getattr(settings, "SMS_ENABLED", False):
            data["test_mode"] = True
            data["sms"] = "Mode test : l'envoi SMS réel est désactivé."
        return Response(data)


class RenvoyerCodeTelephoneView(generics.GenericAPIView):
    """Régénère et renvoie un OTP SMS pour un compte non encore activé."""
    permission_classes = [AllowAny]

    def post(self, request):
        identifiant = str(request.data.get("identifiant", "")).strip()
        if not identifiant:
            return Response({"detail": "L'identifiant est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)

        user = Utilisateur.objects.filter(identifiant__iexact=identifiant).select_related("eglise").first()
        # Réponse générique pour ne pas révéler si un compte existe.
        if not user or user.actif:
            return Response({"detail": "Si ce compte doit encore être confirmé, un nouveau code a été envoyé."})

        from .services_sms import envoyer_otp

        result = envoyer_otp(
            user.telephone,
            utilisateur=user,
            creer_utilisateur=True,
            origine=(user.eglise.nom if user.eglise else "Bureau national EESAG"),
        )
        if not result.get("ok"):
            return Response({"detail": result.get("error", "Impossible d'envoyer le code de confirmation.")}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        from django.conf import settings
        data = {"detail": "Un nouveau code de confirmation a été généré."}
        if not getattr(settings, "SMS_ENABLED", False):
            data.update({"test_mode": True, "test_code": result.get("test_code"), "sms": "Mode test : aucun SMS réel n'est envoyé."})
        else:
            data["detail"] = "Un nouveau code de confirmation SMS a été envoyé."
        return Response(data)


class DiagnosticSMSView(generics.GenericAPIView):
    """Diagnostic sécurisé de la configuration SMS OTP."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != Role.COORDINATEUR:
            return Response({"detail": "Seul le Coordinateur peut consulter le diagnostic SMS."}, status=403)
        from django.conf import settings
        from .services_sms import diagnostic_sms
        data = diagnostic_sms()
        data["ready"] = bool(data["sms_api_url_present"] and data["sms_api_key_present"])
        data["note"] = "Les secrets Twilio sont détenus uniquement par le microservice FastAPI SMS."
        return Response(data)


class ProfilView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfilSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user


class PermissionEgliseView(generics.ListAPIView):
    serializer_class = PermissionEgliseSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return PermissionEglise.objects.all().order_by("libelle")


class DelegationEgliseViewSet(viewsets.ModelViewSet):
    serializer_class = DelegationEgliseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        if u.role in ROLES_NATIONAUX:
            if _est_bureau_specifique(u):
                return DelegationEglise.objects.none()
            return DelegationEglise.objects.select_related("utilisateur", "cree_par").prefetch_related("permissions")
        return DelegationEglise.objects.filter(utilisateur__eglise_id=u.eglise_id).select_related("utilisateur", "cree_par").prefetch_related("permissions")

    def _allowed(self):
        u = self.request.user
        if u.role in ROLES_NATIONAUX:
            return not _est_bureau_specifique(u)
        if u.role == Role.PASTEUR:
            return True
        if u.role == Role.ADMIN_LOCAL:
            return u.delegation_eglise.permissions.filter(code="GESTION_ADMINISTRATEURS").exists() if hasattr(u, "delegation_eglise") else False
        return False

    def get_permissions(self):
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        if not self._allowed():
            return Response({"detail": "Vous n’avez pas la permission de créer un administrateur."}, status=403)
        data = request.data.copy()
        target_id = data.get("utilisateur")
        target = Utilisateur.objects.filter(pk=target_id, role=Role.ADMIN_LOCAL).first()
        if not target or (request.user.role not in ROLES_NATIONAUX and target.eglise_id != request.user.eglise_id):
            return Response({"detail":"L'administrateur choisi n'appartient pas à votre périmètre."}, status=403)
        if request.user.role not in ROLES_NATIONAUX:
            data["cree_par"] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(cree_par=request.user)
        return Response(self.get_serializer(obj).data, status=201)

    def perform_update(self, serializer):
        if not self._allowed():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous n’avez pas la permission de modifier les droits.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        if not self._allowed():
            return Response({"detail": "Accès refusé."}, status=403)
        return super().destroy(request, *args, **kwargs)


class MandatBureauNationalViewSet(viewsets.ModelViewSet):
    serializer_class = MandatBureauNationalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["annee", "actif"]
    def get_queryset(self):
        return MandatBureauNational.objects.select_related("utilisateur").filter(utilisateur__role__in=ROLES_BUREAU_NATIONAL, utilisateur__eglise__isnull=True)
    def get_permissions(self):
        if self.request.method in ("GET","HEAD","OPTIONS"):
            return [IsAuthenticated()]
        return [EstSuperAdminNationalOuPlus()]
