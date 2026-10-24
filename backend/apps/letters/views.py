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
        "eglise_destinataire",
        "membre_concerne",
        "lu",
    ]

    def _est_coordinateur(self, user=None):
        user = user or self.request.user
        return (
            user.is_authenticated
            and (
                user.role == Role.COORDINATEUR
                or user.is_superuser
            )
        )

    def _est_pasteur(self, user=None):
        user = user or self.request.user
        return (
            user.is_authenticated
            and user.role == Role.PASTEUR
            and bool(user.eglise_id)
        )

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

        if self._est_coordinateur(user):
            return qs

        if self._est_pasteur(user):
            return qs.filter(
                Q(expediteur_id=user.id)
                | Q(eglise_origine_id=user.eglise_id)
                | Q(eglise_destinataire_id=user.eglise_id)
                # Compatibilité avec les anciennes recommandations
                # créées avant l'ajout du champ eglise_origine.
                | Q(
                    eglise_origine__isnull=True,
                    membre_concerne__eglise_id=user.eglise_id,
                )
            ).distinct()

        return qs.none()

    def _valider_recommandation(self, user, data):
        if not self._est_pasteur(user):
            raise PermissionDenied(
                "Seul le pasteur d'une église peut envoyer "
                "une recommandation pastorale."
            )

        if data.get("type_courrier") != Courrier.TypeCourrier.RECOMMANDATION:
            raise PermissionDenied(
                "Le pasteur peut créer uniquement des lettres "
                "de recommandation pastorale."
            )

        membre_value = data.get("membre_concerne")
        destination_value = data.get("eglise_destinataire")

        membre_id = getattr(membre_value, "pk", membre_value)
        destination_id = getattr(destination_value, "pk", destination_value)

        membre = (
            Utilisateur.objects
            .filter(
                pk=membre_id,
                eglise_id=user.eglise_id,
                actif=True,
            )
            .select_related("eglise", "departement", "role_eglise")
            .first()
        )

        destination = Eglise.objects.filter(
            pk=destination_id,
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
                    "L'église de destination est introuvable, "
                    "inactive ou sa plateforme n'est pas activée."
                )
            })

        if destination.pk == user.eglise_id:
            raise ValidationError({
                "eglise_destinataire": (
                    "L'église de destination doit être différente "
                    "de l'église d'origine."
                )
            })

        return membre, destination

    def _valider_lettre_nationale(self, user, data):
        if not self._est_coordinateur(user):
            raise PermissionDenied(
                "Seul le Coordinateur du système peut créer "
                "une lettre nationale officielle."
            )

        if data.get("type_courrier") != Courrier.TypeCourrier.NATIONALE:
            raise PermissionDenied(
                "Le Coordinateur doit utiliser le type "
                "« Lettre nationale officielle »."
            )

        type_destinataire = data.get("type_destinataire") or "EGLISE"
        destinataire_nom = (data.get("destinataire_nom") or "").strip()

        if type_destinataire not in Courrier.TypeDestinataire.values:
            raise ValidationError({
                "type_destinataire": "Type de destinataire invalide."
            })

        destination_value = data.get("eglise_destinataire")
        destination_id = getattr(
            destination_value,
            "pk",
            destination_value,
        )

        destination = None

        if type_destinataire == "EGLISE":
            destination = Eglise.objects.filter(
                pk=destination_id,
                statut=Eglise.Statut.ACTIVE,
                plateforme_active=True,
            ).first()

            if not destination:
                raise ValidationError({
                    "eglise_destinataire": (
                        "Sélectionne une église active dont "
                        "la plateforme est activée."
                    )
                })

            destinataire_nom = destination.nom

        elif type_destinataire == "BUREAU_NATIONAL":
            destination = None
            destinataire_nom = destinataire_nom or "Bureau national"

        elif type_destinataire == "AUTRE":
            destination = None
            if not destinataire_nom:
                raise ValidationError({
                    "destinataire_nom": (
                        "Indique le nom de la personne ou de "
                        "la structure destinataire."
                    )
                })

        return type_destinataire, destination, destinataire_nom

    @action(detail=False, methods=["post"], url_path="apercu")
    def apercu(self, request):
        """Prévisualise une lettre sans enregistrer de courrier."""

        type_courrier = request.data.get("type_courrier")

        if (
            type_courrier == Courrier.TypeCourrier.RECOMMANDATION
            and self._est_pasteur(request.user)
        ):
            membre, destination = self._valider_recommandation(
                request.user,
                request.data,
            )

            contenu = request.data.get("contenu") or texte_exemple(
                "RECOMMANDATION",
                f"{membre.prenom} {membre.nom}",
            )

            localite = []
            for champ in ("commune", "district", "prefecture"):
                relation = getattr(destination, champ, None)
                nom = getattr(relation, "nom", None) if relation else None
                if nom:
                    localite.append(nom)

            return Response({
                "type_courrier": "RECOMMANDATION",
                "type_courrier_libelle": "Lettre de recommandation pastorale",
                "objet": request.data.get("objet") or "Lettre de recommandation",
                "membre_id": membre.pk,
                "membre_nom": f"{membre.prenom} {membre.nom}".strip(),
                "membre_identifiant": membre.identifiant,
                "telephone": membre.telephone or "",
                "email": membre.email or "",
                "sexe": membre.get_sexe_display() if membre.sexe else "",
                "date_naissance": (
                    membre.date_naissance.strftime("%d/%m/%Y")
                    if membre.date_naissance else ""
                ),
                "nationalite": (
                    membre.get_nationalite_display()
                    if getattr(membre, "nationalite", None) else ""
                ),
                "fonction": (
                    membre.get_fonction_eglise_display()
                    if getattr(membre, "fonction_eglise", None) else ""
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
                "localite_destination": ", ".join(localite),
                "contenu": contenu,
                "word_importe": bool(request.FILES.get("fichier_word")),
                "message": (
                    "Aperçu uniquement : aucun courrier n'a été enregistré."
                ),
            })

        if (
            type_courrier == Courrier.TypeCourrier.NATIONALE
            and self._est_coordinateur(request.user)
        ):
            type_destinataire, destination, nom_destinataire = (
                self._valider_lettre_nationale(request.user, request.data)
            )

            contenu = request.data.get("contenu") or texte_exemple("NATIONALE")

            return Response({
                "type_courrier": "NATIONALE",
                "type_courrier_libelle": "Lettre nationale officielle",
                "type_destinataire": type_destinataire,
                "destinataire_nom": nom_destinataire,
                "eglise_destinataire": (
                    destination.nom if destination else None
                ),
                "objet": request.data.get("objet") or "Courrier officiel",
                "contenu": contenu,
                "lieu_emission": (
                    request.data.get("lieu_emission") or "Conakry"
                ),
                "message": (
                    "Aperçu de la lettre nationale : aucun courrier "
                    "n'a été enregistré."
                ),
            })

        raise PermissionDenied(
            "Tu n'es pas autorisé à prévisualiser ce type de courrier."
        )

    def create(self, request, *args, **kwargs):
        type_courrier = request.data.get("type_courrier")

        if (
            self._est_pasteur(request.user)
            and type_courrier == Courrier.TypeCourrier.RECOMMANDATION
        ):
            return super().create(request, *args, **kwargs)

        if (
            self._est_coordinateur(request.user)
            and type_courrier == Courrier.TypeCourrier.NATIONALE
        ):
            return super().create(request, *args, **kwargs)

        raise PermissionDenied(
            "Le pasteur peut envoyer une recommandation pastorale. "
            "Le Coordinateur peut envoyer une lettre nationale officielle."
        )

    @transaction.atomic
    def perform_create(self, serializer):
        user = self.request.user
        data = dict(serializer.validated_data)
        type_courrier = data.get("type_courrier")

        if type_courrier == Courrier.TypeCourrier.RECOMMANDATION:
            membre, destination = self._valider_recommandation(user, data)

            courrier = serializer.save(
                expediteur=user,
                eglise_origine=user.eglise,
                type_courrier=Courrier.TypeCourrier.RECOMMANDATION,
                type_destinataire="EGLISE",
                destinataire_nom=destination.nom,
                membre_concerne=membre,
                eglise_destinataire=destination,
            )

            fichier_word = self.request.FILES.get("fichier_word")
            if fichier_word:
                contenu_word = personaliser_word(
                    fichier_word,
                    membre,
                    destination,
                )
                courrier.fichier_word.save(
                    f"{courrier.numero_reference.replace('/', '-')}-"
                    f"{membre.identifiant}.docx",
                    contenu_word,
                    save=False,
                )

            courrier.fichier_pdf = generer_pdf_courrier(courrier)
            courrier.save()

            self._notifier_pasteurs_destination(courrier, destination)
            return

        if type_courrier == Courrier.TypeCourrier.NATIONALE:
            type_destinataire, destination, nom_destinataire = (
                self._valider_lettre_nationale(user, data)
            )

            courrier = serializer.save(
                expediteur=user,
                eglise_origine=None,
                type_courrier=Courrier.TypeCourrier.NATIONALE,
                type_destinataire=type_destinataire,
                destinataire_nom=nom_destinataire,
                membre_concerne=None,
                eglise_destinataire=destination,
            )

            courrier.fichier_pdf = generer_pdf_courrier(courrier)
            courrier.save()

            if destination:
                self._notifier_pasteurs_destination(courrier, destination)
            return

        raise ValidationError({
            "type_courrier": "Type de courrier non autorisé."
        })

    def _notifier_pasteurs_destination(self, courrier, destination):
        from apps.notifications.models import Notification

        pasteurs = Utilisateur.objects.filter(
            eglise_id=destination.pk,
            role=Role.PASTEUR,
            actif=True,
        )

        for destinataire in pasteurs:
            Notification.objects.create(
                destinataire=destinataire,
                eglise=destination,
                titre=(
                    "Nouvelle lettre nationale"
                    if courrier.type_courrier == Courrier.TypeCourrier.NATIONALE
                    else "Nouvelle lettre de recommandation"
                ),
                message=(
                    f"Un courrier vous a été adressé. "
                    f"Référence : {courrier.numero_reference}."
                ),
                type_notification="COURRIER",
                lien="/courriers/",
            )

    def update(self, request, *args, **kwargs):
        if not self._est_coordinateur(request.user):
            raise PermissionDenied(
                "Seul le Coordinateur peut modifier directement un courrier."
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self._est_coordinateur(request.user):
            raise PermissionDenied(
                "Seul le Coordinateur peut modifier directement un courrier."
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._est_coordinateur(request.user):
            raise PermissionDenied(
                "Seul le Coordinateur peut supprimer un courrier."
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def regenerer_pdf(self, request, pk=None):
        courrier = self.get_object()

        peut_regenerer = self._est_coordinateur(request.user) or (
            self._est_pasteur(request.user)
            and courrier.expediteur_id == request.user.pk
            and courrier.type_courrier == Courrier.TypeCourrier.RECOMMANDATION
        )

        if not peut_regenerer:
            raise PermissionDenied(
                "Tu n'es pas autorisé à régénérer ce document."
            )

        if "contenu" in request.data:
            courrier.contenu = request.data.get("contenu") or ""

        courrier.fichier_pdf = generer_pdf_courrier(courrier)
        courrier.save(update_fields=["contenu", "fichier_pdf"])

        return Response(CourrierSerializer(courrier).data)

    @action(detail=True, methods=["get"])
    def telecharger(self, request, pk=None):
        courrier = self.get_object()

        if not (
            self._est_coordinateur(request.user)
            or (
                self._est_pasteur(request.user)
                and (
                    courrier.expediteur_id == request.user.pk
                    or courrier.eglise_origine_id == request.user.eglise_id
                    or courrier.eglise_destinataire_id == request.user.eglise_id
                    or (
                        courrier.eglise_origine_id is None
                        and courrier.membre_concerne_id
                        and courrier.membre_concerne.eglise_id
                        == request.user.eglise_id
                    )
                )
            )
        ):
            raise PermissionDenied(
                "Tu n'es pas autorisé à télécharger ce courrier."
            )

        if not courrier.fichier_pdf:
            courrier.fichier_pdf = generer_pdf_courrier(courrier)
            courrier.save(update_fields=["fichier_pdf"])

        nom_fichier = (
            f"{courrier.numero_reference.replace('/', '-')}.pdf"
        )
        return FileResponse(
            courrier.fichier_pdf.open("rb"),
            as_attachment=True,
            filename=nom_fichier,
        )

    @action(detail=True, methods=["post"])
    def marquer_recu(self, request, pk=None):
        courrier = self.get_object()
        user = request.user

        if not self._est_pasteur(user):
            raise PermissionDenied(
                "Seul un pasteur peut confirmer la réception."
            )

        if not courrier.eglise_destinataire_id:
            raise PermissionDenied(
                "Ce courrier n'est pas adressé à une église."
            )

        if user.eglise_id != courrier.eglise_destinataire_id:
            raise PermissionDenied(
                "Seul le pasteur de l'église destinataire peut confirmer "
                "la réception de ce courrier."
            )

        if courrier.lu:
            return Response({
                "detail": "Ce courrier a déjà été réceptionné.",
                "lu": True,
                "receptionne_par": courrier.receptionne_par_id,
                "date_reception": courrier.date_reception,
            })

        courrier.lu = True
        courrier.receptionne_par = user
        courrier.date_reception = timezone.now()
        courrier.save(update_fields=[
            "lu",
            "receptionne_par",
            "date_reception",
        ])

        return Response({
            "detail": "Réception du courrier confirmée.",
            "lu": courrier.lu,
            "receptionne_par": user.pk,
            "receptionne_par_nom": (
                f"{user.prenom} {user.nom}".strip()
            ),
            "date_reception": courrier.date_reception,
        })
