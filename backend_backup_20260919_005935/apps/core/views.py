from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.models import Role
from apps.bureaux.models import BureauAdministrateur
from .models import AnnonceSysteme, ConfigurationMonetisation, FonctionnaliteSysteme, ProfilDeveloppeur, ActivationFonctionnalite, OffreMiseAJourSysteme
from .services import ensure_default_features, feature_active


def is_coordinator(user):
    return bool(user and (user.role == Role.COORDINATEUR or user.is_superuser))

def assigned_bureau(user):
    return BureauAdministrateur.objects.filter(utilisateur=user, actif=True).select_related("bureau").first()

def is_bureau_general(user):
    if not user or user.role not in (Role.SUPERADMIN_INTL, Role.SUPERADMIN_NATIONAL):
        return False
    return assigned_bureau(user) is None


class FonctionnalitesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_coordinator(request.user):
            return Response({"detail": "Cette section est réservée au Coordinateur du système."}, status=403)

        ensure_default_features()
        bureau_admin = assigned_bureau(request.user)
        scope = "GLOBAL" if is_coordinator(request.user) else "BUREAU" if bureau_admin else "EGLISE" if request.user.eglise_id else "NATIONAL"
        return Response([
            {
                "code": f.code, "nom": f.nom, "description": f.description, "groupe": f.groupe,
                "actif_global": f.actif_global, "actif": feature_active(f.code, user=request.user),
                "scope": scope,
                "peut_modifier": (
                    is_coordinator(request.user)
                    or (bool(bureau_admin) and f.actif_global)
                    or (request.user.role in (Role.ADMIN_LOCAL, Role.PASTEUR) and bool(request.user.eglise_id) and f.actif_global)
                ),
                "verrouillee_globalement": not f.actif_global,
            } for f in FonctionnaliteSysteme.objects.all()
        ])


class FonctionnaliteToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, code):
        if not is_coordinator(request.user):
            return Response(
                {"detail": "Seul le Coordinateur peut activer ou désactiver une fonctionnalité globale."},
                status=403,
            )

        ensure_default_features()
        feature = FonctionnaliteSysteme.objects.filter(code=code).first()
        if not feature:
            return Response({"detail": "Fonctionnalité inconnue."}, status=404)

        actif = bool(request.data.get("actif", True))
        feature.actif_global = actif
        feature.save(update_fields=["actif_global"])

        return Response({
            "code": code,
            "actif": actif,
            "scope": "GLOBAL",
        })


class AnnoncesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        qs = AnnonceSysteme.objects.filter(actif=True).select_related("fonctionnalite")
        return Response([{
            "id": a.id, "titre": a.titre, "message": a.message, "niveau": a.niveau,
            "fonctionnalite": a.fonctionnalite.code if a.fonctionnalite else None,
            "date": a.publie_le or a.date_creation,
        } for a in qs[:30]])
    def post(self, request):
        if not is_coordinator(request.user):
            return Response({"detail": "Publication réservée au Coordinateur."}, status=403)
        annonce = AnnonceSysteme.objects.create(
            titre=str(request.data.get("titre", "Nouvelle fonctionnalité"))[:180],
            message=str(request.data.get("message", "")),
            niveau=request.data.get("niveau", "NOUVEAUTE"),
            actif=True, publie_le=timezone.now(), cree_par=request.user,
        )
        try:
            from apps.accounts.models import Utilisateur
            from apps.notifications.models import Notification
            users = Utilisateur.objects.filter(actif=True)
            Notification.objects.bulk_create([Notification(destinataire=u, eglise=u.eglise, titre=annonce.titre, message=annonce.message, type_notification="SYSTEME", lien="/informations") for u in users], batch_size=500)
        except Exception:
            pass
        return Response({"id": annonce.id, "titre": annonce.titre}, status=201)


class ProfilDeveloppeurView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response([{
            "id": p.id, "nom": p.nom, "titre": p.titre, "biographie": p.biographie, "parcours": p.parcours,
            "experiences": p.experiences, "competences": p.competences,
            "photo": request.build_absolute_uri(p.photo.url) if p.photo else None,
            "email_public": p.email_public, "lien_public": p.lien_public,
        } for p in ProfilDeveloppeur.objects.filter(actif=True)])


class MonetisationView(APIView):
    permission_classes = [IsAuthenticated]
    def _check(self, request):
        return is_coordinator(request.user)
    def get(self, request):
        if not self._check(request):
            return Response({"detail": "Accès réservé au Coordinateur."}, status=403)
        config = ConfigurationMonetisation.objects.first() or ConfigurationMonetisation.objects.create()
        return Response({"actif": config.actif, "devise": config.devise, "fournisseur": config.fournisseur, "compte_destination": config.compte_destination, "url_paiement": config.url_paiement, "notes": config.notes})
    def post(self, request):
        if not self._check(request):
            return Response({"detail": "Accès réservé au Coordinateur."}, status=403)
        config = ConfigurationMonetisation.objects.first() or ConfigurationMonetisation()
        for field in ("actif", "devise", "fournisseur", "compte_destination", "url_paiement", "notes"):
            if field in request.data: setattr(config, field, request.data[field])
        config.modifie_par = request.user
        config.save()
        return Response({"success": True})


class OffresMiseAJourView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response([{
            "id": o.id, "version": o.version, "titre": o.titre, "description": o.description,
            "prix": str(o.prix), "devise": o.devise, "gratuite": o.gratuite,
            "active": o.active, "fonctionnalite": o.fonctionnalite.code if o.fonctionnalite else None,
            "date": o.publie_le or o.date_creation,
        } for o in OffreMiseAJourSysteme.objects.filter(active=True).select_related("fonctionnalite")[:30]])
    def post(self, request):
        if not is_coordinator(request.user):
            return Response({"detail": "Publication des offres réservée au Coordinateur."}, status=403)
        feature = FonctionnaliteSysteme.objects.filter(code=str(request.data.get("fonctionnalite") or "")).first()
        offre = OffreMiseAJourSysteme.objects.create(
            fonctionnalite=feature, version=str(request.data.get("version", "1.0"))[:40],
            titre=str(request.data.get("titre", "Mise à jour EESAG"))[:180],
            description=str(request.data.get("description", "")), prix=request.data.get("prix", 0) or 0,
            devise=str(request.data.get("devise", "GNF"))[:10], gratuite=bool(request.data.get("gratuite", False)),
            active=True, publie_le=timezone.now(), cree_par=request.user,
        )
        return Response({"id": offre.id, "titre": offre.titre, "version": offre.version}, status=201)
