from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("regions", views.RegionViewSet, basename="region")
router.register("prefectures", views.PrefectureViewSet, basename="prefecture")
router.register("districts", views.DistrictViewSet, basename="district")
router.register("communes", views.CommuneViewSet, basename="commune")

urlpatterns = router.urls
