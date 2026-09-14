from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register("publications", views.PublicationViewSet, basename="publication")

urlpatterns = router.urls + [
    path("notifications/envoyer/", views.EnvoyerNotificationView.as_view(), name="notification_envoyer"),
    path("notifications/diffuser/", views.EnvoyerDiffusionNotificationView.as_view(), name="notification_diffuser"),
]
