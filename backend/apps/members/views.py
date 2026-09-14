from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.permissions import EstSuperAdminNationalOuPlus
from apps.accounts.models import ROLES_NATIONAUX, ROLES_BUREAU_NATIONAL, Role, Utilisateur
from apps.bureaux.models import BureauAdministrateur
from .models import Affectation, TransfertMembre
from .serializers import AffectationSerializer
from rest_framework import serializers


class TransfertSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransfertMembre
        fields = ["id", "membre", "eglise_depart", "eglise_arrivee", "courrier", "motif", "date_demande", "date_validation", "valide_par", "statut"]
        read_only_fields = ["eglise_depart", "date_demande", "date_validation", "valide_par", "statut"]


def _est_national_general(user):
    if user.role == Role.COORDINATEUR or user.is_superuser:
        return True
    return user.role in ROLES_BUREAU_NATIONAL and not BureauAdministrateur.objects.filter(utilisateur=user, actif=True).exists()


class AffectationViewSet(viewsets.ModelViewSet):
    """Les affectations pastorales sont gérées au niveau du Coordinateur/Bureau national général."""
    serializer_class = AffectationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["eglise", "utilisateur", "type_affectation", "actif"]

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated()]
        return [EstSuperAdminNationalOuPlus()]

    def get_queryset(self):
        qs = Affectation.objects.select_related("utilisateur", "eglise", "affecte_par")
        user = self.request.user
        if _est_national_general(user):
            return qs
        if user.role == Role.PASTEUR:
            return qs.filter(eglise_id=user.eglise_id)
        return qs.none()

    def perform_create(self, serializer):
        if not _est_national_general(self.request.user):
            raise PermissionError("Seul le Coordinateur ou le Bureau national général peut affecter un pasteur.")
        serializer.save(affecte_par=self.request.user)


class TransfertMembreViewSet(viewsets.ModelViewSet):
    serializer_class = TransfertSerializer

    def get_permissions(self):
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def get_queryset(self):
        u = self.request.user
        qs = TransfertMembre.objects.select_related("membre", "eglise_depart", "eglise_arrivee", "courrier", "demande_par", "valide_par")
        if _est_national_general(u):
            return qs
        if u.role == Role.PASTEUR:
            return qs.filter(eglise_depart_id=u.eglise_id) | qs.filter(eglise_arrivee_id=u.eglise_id)
        return qs.none()

    def create(self, request, *args, **kwargs):
        if request.user.role not in [Role.PASTEUR] and not _est_national_general(request.user):
            return Response({"detail": "Seul le pasteur ou le Bureau national général peut demander un transfert."}, status=403)
        membre = Utilisateur.objects.filter(pk=request.data.get("membre"), eglise_id=request.user.eglise_id).first() if request.user.role == Role.PASTEUR else Utilisateur.objects.filter(pk=request.data.get("membre")).first()
        if not membre:
            return Response({"detail": "Membre introuvable dans votre périmètre."}, status=404)
        from apps.churches.models import Eglise
        eglise_arrivee = Eglise.objects.filter(pk=request.data.get("eglise_arrivee"), statut=Eglise.Statut.ACTIVE).first()
        if not eglise_arrivee or eglise_arrivee.id == membre.eglise_id:
            return Response({"detail": "Église d’arrivée invalide."}, status=400)
        obj = TransfertMembre.objects.create(
            membre=membre,
            eglise_depart_id=membre.eglise_id,
            eglise_arrivee=eglise_arrivee,
            demande_par=request.user,
            motif=request.data.get("motif", ""),
        )
        return Response(self.get_serializer(obj).data, status=201)

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        obj = self.get_object()
        if not (_est_national_general(request.user) or (request.user.role == Role.PASTEUR and request.user.eglise_id == obj.eglise_arrivee_id)):
            return Response({"detail": "Seule l’église d’arrivée ou le Bureau national général peut valider."}, status=403)
        membre = obj.membre
        membre.eglise_id = obj.eglise_arrivee_id
        membre.departement_id = None
        membre.save(update_fields=["eglise", "departement"])
        obj.statut = "VALIDE"
        obj.valide_par = request.user
        obj.date_validation = __import__("django.utils.timezone", fromlist=["now"]).now()
        obj.save(update_fields=["statut", "valide_par", "date_validation"])
        from apps.notifications.models import Notification
        for u in Utilisateur.objects.filter(eglise_id=obj.eglise_arrivee_id, role__in=[Role.PASTEUR, Role.ADMIN_LOCAL], actif=True):
            Notification.objects.create(destinataire=u, eglise_id=obj.eglise_arrivee_id, titre="Nouveau membre transféré", message=f"{membre.prenom} {membre.nom} a rejoint votre église.", type_notification="SYSTEME")
        return Response(self.get_serializer(obj).data)
