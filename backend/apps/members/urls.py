from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("affectations", views.AffectationViewSet, basename="affectation")
router.register("transferts", views.TransfertMembreViewSet, basename="transfert-membre")

urlpatterns = router.urls
