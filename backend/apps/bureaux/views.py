from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.models import Role, ROLES_NATIONAUX, ROLES_BUREAU_NATIONAL
from .models import Bureau, BureauAdministrateur, BureauMembreMandat, NiveauBureau
from .serializers import BureauSerializer, BureauAdministrateurSerializer, BureauMembreMandatSerializer


def _est_coordinateur(user):
    return user.role == Role.COORDINATEUR or user.is_superuser


def _est_national_general(user):
    if _est_coordinateur(user):
        return True
    if user.role not in ROLES_BUREAU_NATIONAL:
        return False
    return not BureauAdministrateur.objects.filter(utilisateur=user, actif=True).exists()


def _bureaux_administres(user):
    return Bureau.objects.filter(administrateurs__utilisateur=user, administrateurs__actif=True).distinct()


def a_droit_bureau(user, bureau, droit):
    if _est_coordinateur(user):
        return True
    if not bureau:
        return False
    if _est_national_general(user) and bureau.niveau == NiveauBureau.NATIONAL:
        return True
    if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
        return bureau.niveau == NiveauBureau.LOCAL and bureau.eglise_id == user.eglise_id
    return BureauAdministrateur.objects.filter(
        utilisateur=user,
        bureau=bureau,
        actif=True,
        **{droit: True},
    ).exists()


class BureauViewSet(viewsets.ModelViewSet):
    serializer_class = BureauSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["niveau", "type_bureau", "eglise", "actif"]
    search_fields = ["nom", "code", "eglise__nom"]

    def get_queryset(self):
        user = self.request.user
        qs = Bureau.objects.select_related("eglise").annotate(
            membres_actifs=Count("mandats", filter=Q(mandats__actif=True))
        )
        if _est_coordinateur(user) or _est_national_general(user):
            return qs
        if user.role in ROLES_BUREAU_NATIONAL:
            return qs.filter(administrateurs__utilisateur=user, administrateurs__actif=True).distinct()
        if user.eglise_id and user.role in [Role.ADMIN_LOCAL, Role.PASTEUR]:
            return qs.filter(Q(niveau=NiveauBureau.NATIONAL) | Q(niveau=NiveauBureau.LOCAL, eglise_id=user.eglise_id)).distinct()
        # Un membre simple peut consulter uniquement l'annuaire national.
        return qs.filter(niveau=NiveauBureau.NATIONAL)

    def perform_create(self, serializer):
        user = self.request.user
        if _est_coordinateur(user) or _est_national_general(user):
            serializer.save()
            return
        if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR] and user.eglise_id:
            serializer.save(niveau=NiveauBureau.LOCAL, eglise=user.eglise)
            return
        raise PermissionDenied("Vous ne pouvez pas créer ce bureau.")

    def perform_update(self, serializer):
        bureau = self.get_object()
        if not a_droit_bureau(self.request.user, bureau, "peut_gerer_membres"):
            raise PermissionDenied("Vous ne pouvez pas administrer ce bureau.")
        serializer.save(niveau=bureau.niveau, eglise=bureau.eglise)

    def perform_destroy(self, instance):
        if not _est_coordinateur(self.request.user):
            raise PermissionDenied("Seul le Coordinateur peut supprimer un bureau.")
        instance.delete()

    @action(detail=False, methods=["get"], url_path="mes-bureaux")
    def mes_bureaux(self, request):
        qs = _bureaux_administres(request.user).annotate(
            membres_actifs=Count("mandats", filter=Q(mandats__actif=True))
        )
        return Response(BureauSerializer(qs, many=True, context={"request": request}).data)

    @action(detail=False, methods=["get"], url_path="membres-candidats")
    def membres_candidats(self, request):
        bureau_id = request.query_params.get("bureau")
        bureau = Bureau.objects.filter(pk=bureau_id, actif=True).first()
        if not bureau or not a_droit_bureau(request.user, bureau, "peut_gerer_membres"):
            raise PermissionDenied("Vous n'avez pas accès à ce bureau.")
        from apps.accounts.models import Utilisateur
        current_year = __import__("django.utils.timezone", fromlist=["now"]).now().year
        base = Utilisateur.objects.filter(actif=True).exclude(role=Role.COORDINATEUR)
        if bureau.niveau == NiveauBureau.NATIONAL:
            base = base.filter(eglise__isnull=True)
        else:
            base = base.filter(eglise_id=bureau.eglise_id)
        used_ids = bureau.mandats.filter(annee=current_year, actif=True).values_list("utilisateur_id", flat=True)
        base = base.exclude(id__in=used_ids).order_by("nom", "prenom")
        return Response([
            {
                "id": u.id,
                "identifiant": u.identifiant,
                "nom_complet": f"{u.prenom} {u.nom}",
                "photo": u.photo.url if u.photo else None,
                "telephone": u.telephone,
            }
            for u in base[:500]
        ])


class BureauMembreMandatViewSet(viewsets.ModelViewSet):
    serializer_class = BureauMembreMandatSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["bureau", "annee", "actif", "utilisateur"]
    search_fields = ["utilisateur__identifiant", "utilisateur__nom", "utilisateur__prenom", "poste"]

    def get_queryset(self):
        user = self.request.user
        qs = BureauMembreMandat.objects.select_related("bureau", "bureau__eglise", "utilisateur").filter(actif=True)
        if _est_coordinateur(user) or _est_national_general(user):
            return qs
        if user.role in ROLES_BUREAU_NATIONAL:
            return qs.filter(bureau__administrateurs__utilisateur=user, bureau__administrateurs__actif=True).distinct()
        if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR] and user.eglise_id:
            return qs.filter(Q(bureau__niveau=NiveauBureau.NATIONAL) | Q(bureau__niveau=NiveauBureau.LOCAL, bureau__eglise_id=user.eglise_id)).distinct()
        # Membre simple : annuaire national uniquement.
        return qs.filter(bureau__niveau=NiveauBureau.NATIONAL)

    def perform_create(self, serializer):
        bureau = serializer.validated_data["bureau"]
        if not a_droit_bureau(self.request.user, bureau, "peut_gerer_membres"):
            raise PermissionDenied("Vous n'avez pas le droit de gérer la composition de ce bureau.")
        serializer.save()

    def perform_update(self, serializer):
        bureau = self.get_object().bureau
        if not a_droit_bureau(self.request.user, bureau, "peut_gerer_membres"):
            raise PermissionDenied("Vous n'avez pas le droit de modifier ce mandat.")
        serializer.save()

    def perform_destroy(self, instance):
        if not a_droit_bureau(self.request.user, instance.bureau, "peut_gerer_membres"):
            raise PermissionDenied("Vous n'avez pas le droit de supprimer ce mandat.")
        instance.delete()


class BureauAdministrateurViewSet(viewsets.ModelViewSet):
    serializer_class = BureauAdministrateurSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["bureau", "actif"]

    def get_queryset(self):
        user = self.request.user
        qs = BureauAdministrateur.objects.select_related("bureau", "bureau__eglise", "utilisateur")
        if _est_coordinateur(user):
            return qs
        if _est_national_general(user):
            return qs.filter(bureau__niveau=NiveauBureau.NATIONAL)
        if user.role in ROLES_BUREAU_NATIONAL:
            return qs.filter(bureau__administrateurs__utilisateur=user, bureau__administrateurs__actif=True).distinct()
        if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR] and user.eglise_id:
            return qs.filter(bureau__niveau=NiveauBureau.LOCAL, bureau__eglise_id=user.eglise_id)
        return qs.none()

    def perform_create(self, serializer):
        bureau = serializer.validated_data["bureau"]
        if not a_droit_bureau(self.request.user, bureau, "peut_gerer_membres"):
            raise PermissionDenied("Seul un gestionnaire habilité peut créer un administrateur de bureau.")
        serializer.save()

# --- Membres indépendants des bureaux (aucun compte utilisateur) ---
from .models import BureauMembre
from .serializers_indep import BureauMembreIndependantSerializer


class BureauMembreIndependantViewSet(viewsets.ModelViewSet):
    serializer_class = BureauMembreIndependantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["bureau", "annee", "actif"]

    def get_queryset(self):
        user = self.request.user
        qs = BureauMembre.objects.select_related("bureau", "bureau__eglise")
        if _est_coordinateur(user) or _est_national_general(user):
            return qs
        if user.role in ROLES_BUREAU_NATIONAL:
            return qs.filter(bureau__administrateurs__utilisateur=user, bureau__administrateurs__actif=True).distinct()
        if user.role in [Role.ADMIN_LOCAL, Role.PASTEUR] and user.eglise_id:
            return qs.filter(bureau__niveau=NiveauBureau.LOCAL, bureau__eglise_id=user.eglise_id)
        # Membre simple : annuaire public des compositions nationales uniquement.
        return qs.filter(bureau__niveau=NiveauBureau.NATIONAL, actif=True)

    def perform_create(self, serializer):
        bureau = serializer.validated_data["bureau"]
        if not a_droit_bureau(self.request.user, bureau, "peut_gerer_membres"):
            raise PermissionDenied("Vous n'avez pas le droit d'ajouter un membre à ce bureau.")
        serializer.save()

    def perform_update(self, serializer):
        bureau = self.get_object().bureau
        if not a_droit_bureau(self.request.user, bureau, "peut_gerer_membres"):
            raise PermissionDenied("Vous n'avez pas le droit de modifier ce membre.")
        serializer.save()

    def perform_destroy(self, instance):
        if not a_droit_bureau(self.request.user, instance.bureau, "peut_gerer_membres"):
            raise PermissionDenied("Vous n'avez pas le droit de supprimer ce membre.")
        instance.delete()
