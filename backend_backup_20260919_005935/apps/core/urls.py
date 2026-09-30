from django.urls import path
from .views import (
    AnnoncesView,
    FonctionnaliteToggleView,
    FonctionnalitesView,
    MonetisationView,
    OffresMiseAJourView,
    ProfilDeveloppeurView,
)

urlpatterns = [
    path("fonctionnalites/", FonctionnalitesView.as_view(), name="fonctionnalites"),
    path("fonctionnalites/<slug:code>/toggle/", FonctionnaliteToggleView.as_view(), name="fonctionnalite_toggle"),
    path("annonces/", AnnoncesView.as_view(), name="annonces_systeme"),
    path("developpeurs/", ProfilDeveloppeurView.as_view(), name="profils_developpeurs"),
    path("monetisation/", MonetisationView.as_view(), name="monetisation"),
    path("offres-mise-a-jour/", OffresMiseAJourView.as_view(), name="offres_mise_a_jour"),
]
