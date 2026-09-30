from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Reunion
from .serializers import ReunionSerializer
from apps.accounts.models import ROLES_NATIONAUX, Role

class ReunionViewSet(viewsets.ModelViewSet):
    serializer_class = ReunionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        qs = Reunion.objects.select_related("eglise", "organisateur")
        if u.role in ROLES_NATIONAUX:
            return qs
        return qs.filter(eglise_id=u.eglise_id)

    def perform_create(self, serializer):
        u = self.request.user
        eglise = serializer.validated_data.get("eglise")
        if u.eglise_id:
            eglise = u.eglise
        serializer.save(organisateur=u, eglise=eglise)

    def get_permissions(self):
        return [IsAuthenticated()]
