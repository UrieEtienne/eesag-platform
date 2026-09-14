from django.urls import path
from . import views

urlpatterns = [
    path("national/", views.StatistiquesNationalesView.as_view(), name="stats_nationales"),
    path("eglise/<int:eglise_id>/", views.StatistiquesEgliseView.as_view(), name="stats_eglise"),
    path("rapport-apercu/", views.RapportApercuView.as_view(), name="rapport_apercu"),
    path("rapport/<int:eglise_id>/", views.RapportEgliseView.as_view(), name="rapport_eglise"),
    path("rapport-national/", views.RapportNationalView.as_view(), name="rapport_national"),
    path("rapport-bureau/<int:bureau_id>/", views.RapportBureauView.as_view(), name="rapport_bureau"),
]
