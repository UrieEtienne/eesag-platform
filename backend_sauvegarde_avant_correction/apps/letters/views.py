
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django.utils import timezone

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Role, Utilisateur
from apps.churches.models import Eglise
from .models import Courrier
from .serializers import CourrierSerializer
from .pdf_generator import generer_pdf_courrier, texte_exemple
from .services_word import personaliser_word


class CourrierViewSet(viewsets.ModelViewSet):
    serializer_class = CourrierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "type_courrier",
        "type_destinataire",
        "eglise_destinataire",
        "membre_concerne",
        "lu",
    ]

    def get_queryset(self):
        user = self.request.user

        qs = Courrier.objects.select_related(
            "expediteur",
            "eglise_origine",
            "eglise_destinataire",
            "membre_concerne",
            "membre_concerne__eglise",
            "receptionne_par",
        )

        if user.role == Role.COORDINATEUR or user.is_superuser:
            return qs

        if user.role == Role.PASTEUR and user.eglise_id:
            # eglise_origine est la référence historique.
            # Le fallback garde visibles les anciennes lettres
            # créées avant l'ajout de ce champ.
            return qs.filter(
                Q(expediteur_id=user.id)
                | Q(eglise_origine_id=user.eglise_id)
                | Q(
                    eglise_origine__isnull=True,
                    membre_concerne__eglise_id=user.eglise_id,
                )
                | Q(eglise_destinataire_id=user.eglise_id)
            ).distinct()

        return qs.none()

    def _est_coordinateur(self):
        user = self.request.user
        return (
            user.is_authenticated
            and (
                user.role == Role.COORDINATEUR
                or user.is_superuser
            )
        )

    def _est_pasteur(self):
        user = self.request.user
        return (
            user.is_authenticated
            and user.role == Role.PASTEUR
            and bool(user.eglise_id)
        )

    def _valider_recommandation(self, request, data):
        if not self._est_pasteur():
            raise PermissionDenied(
                "Seul un pasteur rattaché à une église "
                "peut émettre une recommandation pastorale."
            )

        if data.get("type_courrier") != Courrier.TypeCourrier.RECOMMANDATION:
            raise ValidationError({
                "type_courrier": (
                    "Le formulaire pastoral accepte uniquement "
                    "les recommandations pastorales."
                )
            })

        membre_id = data.get("membre_concerne")
        destination_id = data.get("eglise_destinataire")

        membre = Utilisateur.objects.filter(
            pk=getattr(membre_id, "pk", membre_id),
            eglise_id=request.user.eglise_id,
            actif=True,
        ).select_related(
            "eglise",
            "departement",
            "role_eglise",
        ).first()

        destination = Eglise.objects.filter(
            pk=getattr(destination_id, "pk", destination_id),
            statut=Eglise.Statut.ACTIVE,
            plateforme_active=True,
        ).first()

        if not membre:
            raise ValidationError({
                "membre_concerne": (
                    "Le membre doit être actif et appartenir "
                    "à votre église."
                )
            })

        if not destination:
            raise ValidationError({
                "eglise_destinataire": (
                    "L'église destinataire est introuvable, "
                    "inactive ou sa plateforme n'est pas activée."
                )
            })

        if destination.pk == request.user.eglise_id:
            raise ValidationError({
                "eglise_destinataire": (
                    "Choisissez une église différente "
                    "de l'église d'origine."
                )
            })

        return membre, destination

    def _valider_lettre_nationale(self, data):
        if not self._est_coordinateur():
            raise PermissionDenied(
                "Seul le Coordinateur du système peut émettre "
                "une lettre nationale officielle."
            )

        if data.get("type_courrier") != Courrier.TypeCourrier.NATIONALE:
            raise ValidationError({
                "type_courrier": (
                    "Le formulaire national accepte uniquement "
                    "les lettres nationales officielles."
                )
            })

        type_destinataire = (
            data.get("type_destinataire")
            or Courrier.TypeDestinataire.BUREAU_NATIONAL
        )

        if type_destinataire not in Courrier.TypeDestinataire.values:
            raise ValidationError({
                "type_destinataire": "Type de destinataire invalide."
            })

        destination_id = data.get("eglise_destinataire")
        destinataire_nom = (
            data.get("destinataire_nom") or ""
        ).strip()

        destination = None

        if type_destinataire == Courrier.TypeDestinataire.EGLISE:
            destination = Eglise.objects.filter(
                pk=getattr(destination_id, "pk", destination_id),
                statut=Eglise.Statut.ACTIVE,
                plateforme_active=True,
            ).first()

            if not destination:
                raise ValidationError({
                    "eglise_destinataire": (
                        "Sélectionnez une église active "
                        "dont la plateforme est activée."
                    )
                })

            destinataire_nom = destination.nom

        elif type_destinataire == Courrier.TypeDestinataire.BUREAU_NATIONAL:
            destinataire_nom = (
                destinataire_nom or "Bureau national"
            )

        elif not destinataire_nom:
            raise ValidationError({
                "destinataire_nom": (
                    "Indiquez le nom du destinataire."
                )
            })

        return type_destinataire, destination, destinataire_nom

    def create(self, request, *args, **kwargs):
        type_courrier = request.data.get("type_courrier")

        if type_courrier == Courrier.TypeCourrier.RECOMMANDATION:
            if not self._est_pasteur():
                raise PermissionDenied(
                    "Une recommandation pastorale doit être émise "
                    "par le pasteur de l'église d'origine."
                )

        elif type_courrier == Courrier.TypeCourrier.NATIONALE:
            if not self._est_coordinateur():
                raise PermissionDenied(
                    "Seul le Coordinateur peut créer une lettre nationale."
                )

        else:
            raise ValidationError({
                "type_courrier": (
                    "Type non autorisé dans ce formulaire. "
                    "Utilisez RECOMMANDATION pour le pasteur "
                    "ou NATIONALE pour le Coordinateur."
                )
            })

        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        data = serializer.validated_data

        type_courrier = data.get("type_courrier")

        if type_courrier == Courrier.TypeCourrier.RECOMMANDATION:
            membre, destination = self._valider_recommandation(
                self.request,
                {
                    "type_courrier": type_courrier,
                    "membre_concerne": data.get("membre_concerne"),
                    "eglise_destinataire": data.get("eglise_destinataire"),
                },
            )

            courrier = serializer.save(
                expediteur=user,
                type_courrier=Courrier.TypeCourrier.RECOMMANDATION,
                eglise_origine=membre.eglise,
                membre_concerne=membre,
                eglise_destinataire=destination,
                type_destinataire=Courrier.TypeDestinataire.EGLISE,
                destinataire_nom=destination.nom,
            )

            fichier_word = self.request.FILES.get("fichier_word")
            if fichier_word:
                fichier_personnalise = personaliser_word(
                    fichier_word,
                    membre,
                    destination,
                )
                courrier.fichier_word.save(
                    (
                        f"{courrier.numero_reference.replace('/', '-')}-"
                        f"{membre.identifiant}.docx"
                    ),
                    fichier_personnalise,
                    save=False,
                )

            courrier.fichier_pdf = generer_pdf_courrier(courrier)
            courrier.save()

            from apps.notifications.models import Notification

            pasteurs_destinataires = Utilisateur.objects.filter(
                eglise_id=destination.id,
                role=Role.PASTEUR,
                actif=True,
            )

            for pasteur in pasteurs_destinataires:
                Notification.objects.create(
                    destinataire=pasteur,
                    eglise=destination,
                    titre="Nouvelle lettre de recommandation",
                    message=(
                        f"{membre.prenom} {membre.nom} est recommandé(e) "
                        f"par {membre.eglise.nom}. "
                        f"Réf. {courrier.numero_reference}."
                    ),
                    type_notification="COURRIER",
                    lien="/courriers/",
                )

            return

        if type_courrier == Courrier.TypeCourrier.NATIONALE:
            type_destinataire, destination, nom = (
                self._valider_lettre_nationale(
                    {
                        **data,
                        "type_courrier": type_courrier,
                    }
                )
            )

            courrier = serializer.save(
                expediteur=user,
                type_courrier=Courrier.TypeCourrier.NATIONALE,
                eglise_origine=None,
                membre_concerne=None,
                eglise_destinataire=destination,
                type_destinataire=type_destinataire,
                destinataire_nom=nom,
            )

            courrier.fichier_pdf = generer_pdf_courrier(courrier)
            courrier.save()
            return

        raise ValidationError("Type de courrier non pris en charge.")

    @action(detail=False, methods=["post"], url_path="apercu")
    def apercu(self, request):
        type_courrier = request.data.get("type_courrier")

        if type_courrier == Courrier.TypeCourrier.RECOMMANDATION:
            membre, destination = self._valider_recommandation(
                request,
                request.data,
            )

            contenu = (
                request.data.get("contenu")
                or texte_exemple(
                    "RECOMMANDATION",
                    f"{membre.prenom} {membre.nom}",
                )
            )

            return Response({
                "type_courrier": "RECOMMANDATION",
                "objet": request.data.get("objet") or "Lettre de recommandation",
                "membre_id": membre.id,
                "membre_nom": f"{membre.prenom} {membre.nom}".strip(),
                "membre_identifiant": membre.identifiant,
                "telephone": membre.telephone or "",
                "email": membre.email or "",
                "photo": membre.photo.url if membre.photo else None,
                "sexe": membre.get_sexe_display() if membre.sexe else "",
                "date_naissance": (
                    membre.date_naissance.strftime("%d/%m/%Y")
                    if membre.date_naissance else ""
                ),
                "nationalite": (
                    membre.get_nationalite_display()
                    if membre.nationalite else ""
                ),
                "fonction": (
                    membre.get_fonction_eglise_display()
                    if membre.fonction_eglise else ""
                ),
                "role_eglise": (
                    membre.role_eglise.nom
                    if membre.role_eglise else ""
                ),
                "departement": (
                    membre.departement.nom
                    if membre.departement else ""
                ),
                "eglise_origine": membre.eglise.nom,
                "code_origine": membre.eglise.code,
                "adresse_origine": membre.eglise.adresse_precise or "",
                "eglise_destinataire": destination.nom,
                "code_destination": destination.code,
                "contenu": contenu,
                "word_importe": bool(request.FILES.get("fichier_word")),
                "message": (
                    "Aperçu uniquement : aucun courrier n'a encore "
                    "été enregistré."
                ),
            })

        if type_courrier == Courrier.TypeCourrier.NATIONALE:
            type_dest, destination, nom = (
                self._valider_lettre_nationale(request.data)
            )
            contenu = (
                request.data.get("contenu")
                or texte_exemple("NATIONALE")
            )
            return Response({
                "type_courrier": "NATIONALE",
                "objet": request.data.get("objet") or "Courrier officiel",
                "type_destinataire": type_dest,
                "destinataire_nom": nom,
                "eglise_destinataire": (
                    destination.nom if destination else None
                ),
                "contenu": contenu,
                "message": (
                    "Aperçu uniquement : aucun courrier national "
                    "n'a encore été enregistré."
                ),
            })

        raise ValidationError({
            "type_courrier": (
                "Type non pris en charge pour la prévisualisation."
            )
        })

    def update(self, request, *args, **kwargs):
        if not self._est_coordinateur():
            raise PermissionDenied(
                "Seul le Coordinateur peut modifier directement un courrier."
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self._est_coordinateur():
            raise PermissionDenied(
                "Seul le Coordinateur peut modifier directement un courrier."
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._est_coordinateur():
            raise PermissionDenied(
                "Seul le Coordinateur peut supprimer un courrier."
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def regenerer_pdf(self, request, pk=None):
        courrier = self.get_object()

        est_expediteur = courrier.expediteur_id == request.user.id
        if not self._est_coordinateur() and not (
            self._est_pasteur() and est_expediteur
        ):
            raise PermissionDenied(
                "Vous n'êtes pas autorisé à régénérer ce document."
            )

        courrier.contenu = request.data.get(
            "contenu",
            courrier.contenu,
        )
        courrier.fichier_pdf = generer_pdf_courrier(courrier)
        courrier.save(update_fields=["contenu", "fichier_pdf"])

        return Response(CourrierSerializer(courrier).data)

    @action(detail=True, methods=["get"])
    def telecharger(self, request, pk=None):
        courrier = self.get_object()

        if not (
            self._est_coordinateur()
            or (
                self._est_pasteur()
                and (
                    courrier.expediteur_id == request.user.id
                    or courrier.eglise_destinataire_id == request.user.eglise_id
                    or courrier.eglise_origine_id == request.user.eglise_id
                )
            )
        ):
            raise PermissionDenied(
                "Vous n'êtes pas autorisé à télécharger ce courrier."
            )

        if not courrier.fichier_pdf:
            courrier.fichier_pdf = generer_pdf_courrier(courrier)
            courrier.save(update_fields=["fichier_pdf"])

        return FileResponse(
            courrier.fichier_pdf.open("rb"),
            as_attachment=True,
            filename=(
                f"{courrier.numero_reference.replace('/', '-')}.pdf"
            ),
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def marquer_recu(self, request, pk=None):
        courrier = self.get_object()

        if courrier.type_courrier != Courrier.TypeCourrier.RECOMMANDATION:
            raise PermissionDenied(
                "La réception pastorale est réservée aux recommandations."
            )

        if not self._est_pasteur() or (
            request.user.eglise_id != courrier.eglise_destinataire_id
        ):
            raise PermissionDenied(
                "Seul le pasteur de l'église destinataire peut "
                "confirmer cette réception."
            )

        if not courrier.lu:
            courrier.lu = True
            courrier.receptionne_par = request.user
            courrier.date_reception = timezone.now()
            courrier.save(update_fields=[
                "lu",
                "receptionne_par",
                "date_reception",
            ])

        return Response({
            "detail": "Courrier réceptionné par le pasteur.",
            "lu": courrier.lu,
            "date_reception": courrier.date_reception,
            "receptionne_par": (
                f"{request.user.prenom} {request.user.nom}".strip()
            ),
        })
