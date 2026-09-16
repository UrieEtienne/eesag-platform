from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ROLES_NATIONAUX
from apps.churches.models import Eglise, Departement
from apps.accounts.models import Utilisateur
from apps.notifications.models import Notification
from .models import JournalIA
from .serializers import AssistantRequestSerializer
from .services import generer_assistance


class AssistantIAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role not in ROLES_NATIONAUX and not request.user.eglise_id:
            return Response({"detail": "L'assistant IA est réservé au bureau national et aux gestionnaires rattachés à une église."}, status=403)

        serializer = AssistantRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        extra = serializer.validated_data.get("contexte") or {}

        if request.user.role in ROLES_NATIONAUX:
            scope = Eglise.objects.all()
            stats = {
                "eglises_actives": scope.filter(statut=Eglise.Statut.ACTIVE).count(),
                "membres": Utilisateur.objects.filter(actif=True, eglise__isnull=False).count(),
                "departements": Departement.objects.count(),
                "notifications": Notification.objects.count(),
            }
        else:
            eglise_id = request.user.eglise_id
            stats = {
                "eglises_actives": 1,
                "membres": Utilisateur.objects.filter(actif=True, eglise_id=eglise_id).count(),
                "departements": Departement.objects.filter(eglise_id=eglise_id).count(),
                "notifications": Notification.objects.filter(eglise_id=eglise_id).count(),
            }

        context = {"stats": stats, **extra}
        if "sujet" in serializer.validated_data:
            context["sujet"] = serializer.validated_data.get("sujet")
        if "message" in serializer.validated_data:
            context["message"] = serializer.validated_data.get("message")

        resultat, fournisseur, succes = generer_assistance(action, context)
        JournalIA.objects.create(
            utilisateur=request.user,
            eglise_id=None if request.user.role in ROLES_NATIONAUX else request.user.eglise_id,
            action=action,
            entree=str(context),
            resultat=resultat,
            fournisseur=fournisseur,
            succes=succes,
        )
        return Response({"action": action, "resultat": resultat, "fournisseur": fournisseur, "succes": succes})
