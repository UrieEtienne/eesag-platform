from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import ROLES_NATIONAUX, ROLES_GESTION_EGLISE, ROLES_BUREAU_NATIONAL, Role
from apps.accounts.permissions import EstAdminLocalOuPlus
from apps.bureaux.views import a_droit_bureau
from apps.bureaux.models import BureauAdministrateur
from .models import Notification, Publication, DiffusionNotification
from .serializers import NotificationSerializer, PublicationSerializer


def _est_national_general(user):
    if user.role == Role.COORDINATEUR or user.is_superuser:
        return True
    if user.role not in ROLES_BUREAU_NATIONAL:
        return False
    from apps.bureaux.models import BureauAdministrateur
    return not BureauAdministrateur.objects.filter(utilisateur=user, actif=True).exists()


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Chaque utilisateur voit uniquement SES propres notifications (sa boîte)."""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(destinataire=self.request.user)

    @action(detail=True, methods=["post"])
    def marquer_lu(self, request, pk=None):
        notif = self.get_object()
        notif.lu = True
        notif.save(update_fields=["lu"])
        return Response({"detail": "Notification marquée comme lue."})

    @action(detail=False, methods=["post"])
    def tout_marquer_lu(self, request):
        self.get_queryset().update(lu=True)
        return Response({"detail": "Toutes les notifications ont été marquées comme lues."})


class PublicationViewSet(viewsets.ModelViewSet):
    """
    Une église publie une information (message/programme) visible par ses membres
    et par les personnes abonnées à cette église.
    """
    serializer_class = PublicationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["eglise"]

    def get_queryset(self):
        return Publication.objects.select_related("eglise", "auteur")

    def get_permissions(self):
        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            return [EstAdminLocalOuPlus()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        eglise = serializer.validated_data.get("eglise")
        if user.role not in ROLES_NATIONAUX:
            eglise = user.eglise
        publication = serializer.save(auteur=user, eglise=eglise)

        # Notifier tous les membres de l'église + les abonnés
        from apps.accounts.models import Utilisateur, Abonnement
        destinataires = list(Utilisateur.objects.filter(eglise=eglise))
        abonnes_ids = Abonnement.objects.filter(eglise=eglise).values_list("utilisateur_id", flat=True)
        destinataires += list(Utilisateur.objects.filter(id__in=abonnes_ids))

        for destinataire in set(destinataires):
            Notification.objects.create(
                destinataire=destinataire,
                eglise=eglise,
                titre=f"Publication : {publication.titre}",
                message=publication.contenu[:200],
                type_notification="PUBLICATION",
            )


class EnvoyerNotificationView(generics.GenericAPIView):
    permission_classes = [EstAdminLocalOuPlus]

    def post(self, request):
        from apps.churches.models import Eglise
        from apps.accounts.models import Utilisateur
        eglise_id = request.data.get("eglise")
        titre = (request.data.get("titre") or "").strip()
        message = (request.data.get("message") or "").strip()
        if not titre or not message:
            return Response({"detail": "Titre et message sont obligatoires."}, status=400)
        user = request.user
        if user.role in ROLES_NATIONAUX:
            if not _est_national_general(user):
                return Response({"detail": "Un administrateur de bureau national ne peut notifier toute une église."}, status=403)
            eglise = Eglise.objects.filter(pk=eglise_id, statut=Eglise.Statut.ACTIVE).first()
        else:
            if eglise_id and str(eglise_id) != str(user.eglise_id):
                return Response({"detail": "Vous ne pouvez notifier que votre propre église."}, status=403)
            eglise = user.eglise
        if not eglise:
            return Response({"detail": "Église introuvable."}, status=404)
        destinataires = Utilisateur.objects.filter(eglise=eglise, actif=True)
        notifications = [Notification(destinataire=u, eglise=eglise, titre=titre, message=message, type_notification="SYSTEME") for u in destinataires]
        Notification.objects.bulk_create(notifications)
        return Response({"detail": f"Notification envoyée à {len(notifications)} membre(s)."}, status=status.HTTP_201_CREATED)


class EnvoyerDiffusionNotificationView(generics.GenericAPIView):
    """Diffuse une information au bon périmètre: église, département ou bureau."""
    permission_classes = [EstAdminLocalOuPlus]

    def post(self, request):
        from apps.accounts.models import Utilisateur, ROLES_NATIONAUX
        from apps.churches.models import Eglise, Departement
        from apps.bureaux.models import Bureau

        portee = request.data.get("portee")
        titre = (request.data.get("titre") or "").strip()
        message = (request.data.get("message") or "").strip()
        if not portee or not titre or not message:
            return Response({"detail": "Portée, titre et message sont obligatoires."}, status=400)

        user = request.user
        qs = Utilisateur.objects.filter(actif=True)
        eglise = None
        departement = None
        bureau = None

        if portee == "DEPARTEMENT":
            departement = Departement.objects.filter(pk=request.data.get("departement")).select_related("eglise").first()
            if not departement:
                return Response({"detail": "Département introuvable."}, status=404)
            if user.role in ROLES_NATIONAUX:
                # Un administrateur d'un bureau thématique ne diffuse pas vers un département d'une église arbitraire.
                if BureauAdministrateur.objects.filter(utilisateur=user, actif=True).exists():
                    return Response({"detail": "Un administrateur de bureau national ne peut pas diffuser vers un département d'église."}, status=403)
            elif departement.eglise_id != user.eglise_id:
                return Response({"detail": "Département hors de votre église."}, status=403)
            qs = qs.filter(eglise_id=departement.eglise_id, departement_id=departement.id)
            eglise = departement.eglise
        elif portee == "BUREAU":
            bureau = Bureau.objects.filter(pk=request.data.get("bureau"), actif=True).select_related("eglise").first()
            if not bureau:
                return Response({"detail": "Bureau introuvable."}, status=404)
            if user.role in ROLES_NATIONAUX and not _est_national_general(user):
                if not a_droit_bureau(user, bureau, "peut_envoyer_notifications"):
                    return Response({"detail": "Vous n'avez pas le droit de publier pour ce bureau."}, status=403)
            elif user.role not in ROLES_NATIONAUX and bureau.eglise_id != user.eglise_id:
                return Response({"detail": "Bureau hors de votre église."}, status=403)
            qs = qs.filter(id__in=bureau.mandats.filter(actif=True).values_list("utilisateur_id", flat=True))
            eglise = bureau.eglise
        elif portee == "EGLISE":
            eglise_id = request.data.get("eglise") or user.eglise_id
            if not eglise_id:
                return Response({"detail": "Une église est obligatoire."}, status=400)
            if user.role in ROLES_NATIONAUX and BureauAdministrateur.objects.filter(utilisateur=user, actif=True).exists() and user.role != "COORDINATEUR":
                return Response({"detail": "Un administrateur de bureau national ne peut pas diffuser à toute une église."}, status=403)
            if user.role not in ROLES_NATIONAUX and str(eglise_id) != str(user.eglise_id):
                return Response({"detail": "Vous ne pouvez notifier que votre église."}, status=403)
            eglise = Eglise.objects.filter(pk=eglise_id).first()
            if not eglise:
                return Response({"detail": "Église introuvable."}, status=404)
            qs = qs.filter(eglise_id=eglise.id)
        elif portee == "NATIONAL":
            # Seul le Coordinateur ou un administrateur national général (sans bureau thématique assigné)
            # peut envoyer une diffusion à l'ensemble du réseau.
            if user.role not in ROLES_NATIONAUX:
                return Response({"detail": "Seul le Bureau national peut diffuser au réseau."}, status=403)
            if not _est_national_general(user):
                return Response({"detail": "Votre compte est limité à son bureau national."}, status=403)
        else:
            return Response({"detail": "Portée inconnue."}, status=400)

        dest_ids = list(qs.values_list("id", flat=True).distinct())
        diffusion = DiffusionNotification.objects.create(
            auteur=user, portee=portee, eglise=eglise, departement=departement, bureau=bureau,
            titre=titre, message=message, nombre_destinataires=len(dest_ids)
        )
        Notification.objects.bulk_create([
            Notification(destinataire_id=uid, eglise=eglise, titre=titre, message=message, type_notification="SYSTEME")
            for uid in dest_ids
        ])
        return Response({"id": diffusion.id, "nombre_destinataires": len(dest_ids), "detail": "Diffusion créée."}, status=status.HTTP_201_CREATED)
