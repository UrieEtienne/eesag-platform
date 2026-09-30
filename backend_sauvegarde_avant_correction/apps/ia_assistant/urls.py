from django.urls import path
from .views import AssistantIAView

urlpatterns = [
    path("assistant/", AssistantIAView.as_view(), name="assistant_ia"),
]
