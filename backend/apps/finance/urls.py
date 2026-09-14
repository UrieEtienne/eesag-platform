from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("transactions", views.TransactionViewSet, basename="transaction")
router.register("projets", views.ProjetViewSet, basename="projet")

urlpatterns = router.urls
