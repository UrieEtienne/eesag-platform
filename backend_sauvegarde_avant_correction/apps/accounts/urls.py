from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register("utilisateurs", views.UtilisateurViewSet, basename="utilisateur")
router.register("abonnements", views.AbonnementViewSet, basename="abonnement")
router.register("delegations-eglise", views.DelegationEgliseViewSet, basename="delegation-eglise")
router.register("mandats-bureau-national", views.MandatBureauNationalViewSet, basename="mandat-bureau-national")

urlpatterns = [
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/moi/", views.MoiView.as_view(), name="moi"),
    path("auth/changer-code-secret/", views.ChangerCodeSecretView.as_view(), name="changer_code_secret"),
    path("auth/inscription/", views.InscriptionMembreView.as_view(), name="inscription"),
    path("auth/verification-telephone/", views.VerificationTelephoneView.as_view(), name="verification_telephone"),
    path("auth/renvoyer-code-telephone/", views.RenvoyerCodeTelephoneView.as_view(), name="renvoyer_code_telephone"),
    path("auth/profil/", views.ProfilView.as_view(), name="profil"),
    path("auth/diagnostic-sms/", views.DiagnosticSMSView.as_view(), name="diagnostic_sms"),
    path("permissions-eglise/", views.PermissionEgliseView.as_view(), name="permissions_eglise"),
    path("membres/recherche/", views.RechercheMembreView.as_view(), name="recherche_membre"),
    path("bureau-national/", views.BureauNationalView.as_view(), name="bureau_national"),
    path("", include(router.urls)),
]
