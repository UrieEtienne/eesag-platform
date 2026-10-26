from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views
from .geolocation_views import RechercheEgliseView, ItineraireView


router = DefaultRouter()
router.register("regions", views.RegionViewSet, basename="region")
router.register("prefectures", views.PrefectureViewSet, basename="prefecture")
router.register("districts", views.DistrictViewSet, basename="district")
router.register("communes", views.CommuneViewSet, basename="commune")


urlpatterns = [
    path(
        "recherche-eglise/",
        RechercheEgliseView.as_view(),
        name="recherche-eglise",
    ),
    path(
        "itineraire/",
        ItineraireView.as_view(),
        name="geographie-itineraire",
    ),
] + router.urls
