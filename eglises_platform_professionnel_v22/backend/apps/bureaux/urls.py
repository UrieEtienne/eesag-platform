from rest_framework.routers import DefaultRouter
from .views import BureauViewSet, BureauMembreMandatViewSet, BureauAdministrateurViewSet, BureauMembreIndependantViewSet

router = DefaultRouter()
router.register(r"bureaux", BureauViewSet, basename="bureaux")
router.register(r"bureau-membres", BureauMembreMandatViewSet, basename="bureau-membres")
router.register(r"bureau-administrateurs", BureauAdministrateurViewSet, basename="bureau-administrateurs")
router.register(r"bureau-membres-independants", BureauMembreIndependantViewSet, basename="bureau-membres-independants")

urlpatterns = router.urls
