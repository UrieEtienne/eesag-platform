from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("religions", views.ReligionViewSet, basename="religion")
router.register("eglises", views.EgliseViewSet, basename="eglise")
router.register("departements", views.DepartementViewSet, basename="departement")
router.register("roles-eglise", views.RoleEgliseViewSet, basename="role-eglise")
router.register("annexes", views.AnnexeViewSet, basename="annexe")

urlpatterns = router.urls
