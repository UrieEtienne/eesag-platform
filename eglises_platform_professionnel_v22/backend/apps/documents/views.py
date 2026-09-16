from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.models import ROLES_NATIONAUX
from apps.accounts.permissions import EstAdminLocalOuPlus
from .models import Document, DocumentDestinataire
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["categorie", "actif"]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [EstAdminLocalOuPlus()]

    def get_queryset(self):
        user = self.request.user
        base = Document.objects.select_related("expediteur", "eglise_expediteur").prefetch_related("liaisons_destinataires__eglise")
        if user.role in ROLES_NATIONAUX:
            return base
        return base.filter(Q(eglise_expediteur_id=user.eglise_id) | Q(destinataires=user.eglise_id)).distinct()

    @action(detail=True, methods=["post"])
    def marquer_recu(self, request, pk=None):
        document = self.get_object()
        if request.user.role in ROLES_NATIONAUX:
            return Response({"detail": "Lecture nationale."})
        liaison = DocumentDestinataire.objects.filter(document=document, eglise_id=request.user.eglise_id).first()
        if not liaison:
            return Response({"detail": "Accès refusé."}, status=status.HTTP_403_FORBIDDEN)
        liaison.lu = True
        liaison.compte_reception = True
        liaison.save(update_fields=["lu", "compte_reception"])
        return Response({"detail": "Document marqué comme reçu."})
