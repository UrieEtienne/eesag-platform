from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.models import Role
from .models import Courrier
from .serializers import CourrierSerializer
from .pdf_generator import generer_pdf_courrier, texte_exemple
from .services_word import personaliser_word


class CourrierViewSet(viewsets.ModelViewSet):
    serializer_class = CourrierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["type_courrier", "eglise_destinataire", "membre_concerne", "lu"]

    def get_queryset(self):
        user = self.request.user
        qs = Courrier.objects.select_related("expediteur", "eglise_destinataire", "membre_concerne", "membre_concerne__eglise")
        if user.role == Role.COORDINATEUR or user.is_superuser:
            return qs
        if user.role == Role.PASTEUR and user.eglise_id:
            return qs.filter(Q(expediteur_id=user.id) | Q(membre_concerne__eglise_id=user.eglise_id) | Q(eglise_destinataire_id=user.eglise_id)).distinct()
        return qs.none()

    def _valider_recommandation(self, request, data):
        if request.user.role != Role.PASTEUR or not request.user.eglise_id:
            raise PermissionDenied("Seul le pasteur d'une église peut envoyer et réceptionner les lettres de recommandation.")
        if data.get("type_courrier") != Courrier.TypeCourrier.RECOMMANDATION:
            raise PermissionDenied("Le pasteur utilise ce module uniquement pour les lettres de recommandation.")
        membre_id = data.get("membre_concerne")
        destination_id = data.get("eglise_destinataire")
        from apps.accounts.models import Utilisateur
        from apps.churches.models import Eglise
        membre = Utilisateur.objects.filter(pk=membre_id, eglise_id=request.user.eglise_id, actif=True).select_related("eglise").first()
        destination = Eglise.objects.filter(
            pk=destination_id,
            statut=Eglise.Statut.ACTIVE,
            plateforme_active=True,
        ).first()
        if not membre:
            raise PermissionDenied("Le fidèle doit appartenir à votre église.")
        if not destination:
            raise PermissionDenied("L'église de destination est introuvable.")
        if destination.id == request.user.eglise_id:
            raise PermissionDenied("L'église de destination doit être différente de l'église d'origine.")
        return membre, destination

    @action(detail=False, methods=["post"], url_path="apercu")
    def apercu(self, request):
        membre, destination = self._valider_recommandation(request, request.data)
        contenu = request.data.get("contenu") or texte_exemple("RECOMMANDATION", f"{membre.prenom} {membre.nom}")
        return Response({
            "type_courrier": "RECOMMANDATION",
            "objet": request.data.get("objet") or "Recommandation de déplacement",
            "membre_nom": f"{membre.prenom} {membre.nom}",
            "membre_identifiant": membre.identifiant,
            "telephone": membre.telephone,
            "email": membre.email or "",
            "sexe": membre.get_sexe_display(),
            "date_naissance": membre.date_naissance.strftime("%d/%m/%Y") if membre.date_naissance else "",
            "nationalite": membre.get_nationalite_display() if membre.nationalite else "",
            "fonction": membre.get_fonction_eglise_display(),
            "role_eglise": membre.role_eglise.nom if getattr(membre, "role_eglise", None) else "",
            "departement": membre.departement.nom if getattr(membre, "departement", None) else "",
            "eglise_origine": membre.eglise.nom,
            "code_origine": membre.eglise.code,
            "adresse_origine": membre.eglise.adresse_precise or "",
            "eglise_destinataire": destination.nom,
            "code_destination": destination.code,
            "localite_destination": ", ".join(
                str(v) for v in [
                    getattr(destination.commune, "nom", None) if destination.commune_id else None,
                    getattr(destination.district, "nom", None) if destination.district_id else None,
                    getattr(destination.prefecture, "nom", None) if destination.prefecture_id else None,
                ] if v
            ),
            "contenu": contenu,
            "word_importe": bool(request.FILES.get("fichier_word")),
            "message": "Aperçu généré : les données personnelles sont remplies automatiquement. Aucun enregistrement n'est effectué avant validation.",
        })

    def create(self, request, *args, **kwargs):
        # Une création de courrier opérationnel est strictement réservée au pasteur.
        if request.user.role != Role.PASTEUR:
            raise PermissionDenied("Seul le pasteur peut créer et envoyer une lettre de recommandation.")
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        data = {**serializer.validated_data}
        membre, destination = self._valider_recommandation(self.request, {
            "type_courrier": data.get("type_courrier"),
            "membre_concerne": data.get("membre_concerne").id if data.get("membre_concerne") else None,
            "eglise_destinataire": data.get("eglise_destinataire").id if data.get("eglise_destinataire") else None,
        })
        courrier = serializer.save(
            expediteur=user,
            type_courrier=Courrier.TypeCourrier.RECOMMANDATION,
            membre_concerne=membre,
            eglise_destinataire=destination,
        )
        if self.request.FILES.get("fichier_word"):
            courrier.fichier_word.save(
                f"{courrier.numero_reference.replace('/', '-')}-{membre.identifiant}.docx",
                personaliser_word(self.request.FILES["fichier_word"], membre, destination),
                save=False,
            )
        courrier.fichier_pdf = generer_pdf_courrier(courrier)
        courrier.save()

        from apps.notifications.models import Notification
        from apps.accounts.models import Utilisateur
        for destinataire in Utilisateur.objects.filter(eglise_id=destination.id, role=Role.PASTEUR, actif=True):
            Notification.objects.create(
                destinataire=destinataire,
                eglise=destination,
                titre="Nouvelle lettre de recommandation",
                message=f"{membre.prenom} {membre.nom} est recommandé(e) par {membre.eglise.nom}. Réf. {courrier.numero_reference}.",
                type_notification="COURRIER",
                lien="/courriers/",
            )

    @action(detail=True, methods=["post"])
    def regenerer_pdf(self, request, pk=None):
        courrier = self.get_object()
        if request.user.role != Role.PASTEUR:
            raise PermissionDenied("Seul le pasteur peut modifier le document.")
        if courrier.expediteur_id != request.user.id and courrier.eglise_destinataire_id != request.user.eglise_id:
            raise PermissionDenied("Ce courrier est hors de votre église.")
        courrier.contenu = request.data.get("contenu", courrier.contenu)
        courrier.fichier_pdf = generer_pdf_courrier(courrier)
        courrier.save(update_fields=["contenu", "fichier_pdf"])
        return Response(CourrierSerializer(courrier).data)

    @action(detail=True, methods=["get"])
    def telecharger(self, request, pk=None):
        courrier = self.get_object()
        if request.user.role != Role.PASTEUR and not (request.user.role == Role.COORDINATEUR or request.user.is_superuser):
            raise PermissionDenied("Seul le pasteur peut consulter les courriers opérationnels.")
        if not courrier.fichier_pdf:
            courrier.fichier_pdf = generer_pdf_courrier(courrier)
            courrier.save(update_fields=["fichier_pdf"])
        return FileResponse(courrier.fichier_pdf.open("rb"), as_attachment=True, filename=f"{courrier.numero_reference.replace('/', '-')}.pdf")

    @action(detail=True, methods=["post"])
    def marquer_recu(self, request, pk=None):
        courrier = self.get_object()
        if request.user.role != Role.PASTEUR or request.user.eglise_id != courrier.eglise_destinataire_id:
            raise PermissionDenied("Seul le pasteur de l'église destinataire peut réceptionner ce courrier.")
        courrier.lu = True
        courrier.save(update_fields=["lu"])
        return Response({"detail": "Courrier réceptionné par le pasteur."})
