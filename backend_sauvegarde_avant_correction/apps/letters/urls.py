from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("courriers", views.CourrierViewSet, basename="courrier")

urlpatterns = router.urls
