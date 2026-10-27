from datetime import date, timedelta

from django.db import OperationalError
from django.db.models import Count, Q, Sum
from django.core.exceptions import FieldError
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role, ROLES_BUREAU_NATIONAL, Utilisateur
from apps.bureaux.models import Bureau, BureauAdministrateur
from apps.churches.models import Departement, Eglise, Religion
from apps.finance.models import Projet, Transaction



def _refuser_coordinateur_dashboard(request):
    if request.user.role == Role.COORDINATEUR:
        return Response(
            {
                "detail": (
                    "Le Coordinateur n'a pas accès au tableau de bord "
                    "opérationnel ni aux données financières."
                )
            },
            status=403,
        )
    return None


def _repartition_membres(queryset):
    total = queryset.count()
    hommes = queryset.filter(sexe="H").count()
    femmes = queryset.filter(sexe="F").count()
    today = date.today()
    limite_enfant = today.replace(year=today.year - 12)
    limite_jeune = today.replace(year=today.year - 31)
    enfants = queryset.filter(date_naissance__gt=limite_enfant).count()
    jeunes = queryset.filter(date_naissance__lte=limite_enfant, date_naissance__gt=limite_jeune).count()
    adultes = queryset.filter(date_naissance__lte=limite_jeune).count()
    return {
        "total": total,
        "hommes": hommes,
        "femmes": femmes,
        "enfants": enfants,
        "jeunes": jeunes,
        "adultes": adultes,
        "sans_date_naissance": total - enfants - jeunes - adultes,
    }


def _est_coordinateur(user):
    return user.role == Role.COORDINATEUR or user.is_superuser


def _est_national_general(user):
    return user.role in ROLES_BUREAU_NATIONAL and not BureauAdministrateur.objects.filter(utilisateur=user, actif=True).exists()


def _periode(request):
    periode = request.query_params.get("periode", "annee")
    debut = parse_date(request.query_params.get("debut", ""))
    fin = parse_date(request.query_params.get("fin", ""))
    today = timezone.localdate()
    if periode == "semaine":
        debut, fin = today - timedelta(days=today.weekday()), today
    elif periode == "mois":
        debut, fin = today.replace(day=1), today
    elif periode == "annee":
        debut, fin = today.replace(month=1, day=1), today
    elif periode == "personnalisee":
        if not debut or not fin:
            raise ValueError("Pour une période personnalisée, renseignez le début et la fin.")
    else:
        debut, fin = debut or today.replace(month=1, day=1), fin or today
    if debut > fin:
        raise ValueError("La date de début doit précéder la date de fin.")
    return debut, fin


def _scope_rapport(user):
    if _est_coordinateur(user):
        return {"type": "GLOBAL", "label": "Réseau EESAG"}
    if user.role in [Role.PASTEUR, Role.ADMIN_LOCAL] and user.eglise_id:
        return {"type": "EGLISE", "eglise_id": user.eglise_id, "label": user.eglise.nom}
    admin = BureauAdministrateur.objects.filter(utilisateur=user, actif=True, peut_gerer_rapports=True).select_related("bureau").first()
    if admin:
        return {"type": "BUREAU", "bureau_id": admin.bureau_id, "label": admin.bureau.nom}
    if _est_national_general(user):
        return {"type": "NATIONAL", "label": "Bureau national"}
    return {"type": "NONE", "label": "Aucun périmètre"}


def _data_rapport(user, debut, fin, inclure_membres, inclure_finances, inclure_projets, forced_scope=None):
    scope = forced_scope or _scope_rapport(user)
    if scope["type"] == "NONE":
        raise PermissionError("Aucun périmètre de rapport autorisé.")

    if scope["type"] in ("EGLISE",):
        membres = Utilisateur.objects.filter(eglise_id=scope["eglise_id"], actif=True)
        operations = Transaction.objects.filter(eglise_id=scope["eglise_id"], date_transaction__range=(debut, fin))
        projets = Projet.objects.filter(eglise_id=scope["eglise_id"])
        meta = Eglise.objects.select_related("region", "prefecture", "district", "commune", "responsable").get(pk=scope["eglise_id"])
        label = meta.nom
    elif scope["type"] == "BUREAU":
        membres = Utilisateur.objects.filter(actif=True, mandats_bureaux__bureau_id=scope["bureau_id"], mandats_bureaux__actif=True).distinct()
        operations = Transaction.objects.filter(bureau_id=scope["bureau_id"], date_transaction__range=(debut, fin))
        projets = Projet.objects.filter(bureau_id=scope["bureau_id"])
        meta = Bureau.objects.get(pk=scope["bureau_id"])
        label = meta.nom
    elif scope["type"] == "NATIONAL":
        membres = Utilisateur.objects.filter(actif=True, eglise__isnull=True).exclude(role=Role.COORDINATEUR)
        operations = Transaction.objects.filter(eglise__isnull=True, bureau__isnull=True, date_transaction__range=(debut, fin))
        projets = Projet.objects.filter(eglise__isnull=True, bureau__isnull=True)
        meta = None
        label = "Bureau national"
    else:  # GLOBAL, réservé au Coordinateur
        membres = Utilisateur.objects.filter(actif=True).exclude(role=Role.COORDINATEUR)
        operations = Transaction.objects.filter(date_transaction__range=(debut, fin))
        projets = Projet.objects.all()
        meta = None
        label = "Réseau EESAG"

    entrees = operations.exclude(type_transaction="SORTIE").aggregate(v=Sum("montant"))["v"] or 0
    sorties = operations.filter(type_transaction="SORTIE").aggregate(v=Sum("montant"))["v"] or 0
    data = {
        "scope": scope,
        "label": label,
        "periode": {"debut": str(debut), "fin": str(fin)},
        "membres": _repartition_membres(membres) if inclure_membres else None,
        "finances": {
            "operations": operations.count(),
            "entrees": entrees,
            "sorties": sorties,
            "solde": entrees - sorties,
        } if inclure_finances else None,
        "projets": {
            "nombre": projets.count(),
            "budget_prevu": sum((p.budget_prevu for p in projets), 0),
            "budget_utilise": sum((p.budget_utilise for p in projets), 0),
        } if inclure_projets else None,
    }
    if meta and scope["type"] == "EGLISE":
        data["identite"] = {
            "nom": meta.nom,
            "code": meta.code,
            "religion": meta.religion.nom if meta.religion else "",
            "adresse": getattr(meta, "adresse_precise", "") or "",
            "telephone": getattr(meta, "telephone", "") or "",
            "email": getattr(meta, "email", "") or "",
        }
    return data


def _rapport_pdf(data):
    response = HttpResponse(content_type="application/pdf")
    safe_label = data["label"].replace(" ", "-").replace("/", "-")
    response["Content-Disposition"] = f'attachment; filename="rapport-{safe_label}-{data["periode"]["debut"]}-{data["periode"]["fin"]}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("EESAG", styles["Title"]),
        Paragraph(data["label"], styles["Heading2"]),
        Paragraph(f"Période : {data['periode']['debut']} → {data['periode']['fin']}", styles["Normal"]),
        Spacer(1, 12),
    ]
    if data.get("identite"):
        i = data["identite"]
        story += [Paragraph(f"Code : {i['code']} · {i['religion']}", styles["Normal"]), Paragraph(f"{i['adresse']} · {i['telephone']} · {i['email']}", styles["Normal"]), Spacer(1, 12)]
    rows = [["Rubrique", "Valeur"]]
    if data.get("membres") is not None:
        m = data["membres"]
        rows += [["Membres actifs", str(m["total"])], ["Hommes", str(m["hommes"])], ["Femmes", str(m["femmes"])], ["Enfants", str(m["enfants"])], ["Jeunes", str(m["jeunes"])], ["Adultes", str(m["adultes"])]]
    if data.get("finances") is not None:
        f = data["finances"]
        rows += [["Opérations", str(f["operations"])], ["Entrées", f"{f['entrees']:,.0f} GNF"], ["Sorties", f"{f['sorties']:,.0f} GNF"], ["Solde", f"{f['solde']:,.0f} GNF"]]
    if data.get("projets") is not None:
        p = data["projets"]
        rows += [["Projets", str(p["nombre"])], ["Budget prévu", f"{p['budget_prevu']:,.0f} GNF"], ["Budget utilisé", f"{p['budget_utilise']:,.0f} GNF"]]
    table = Table(rows, colWidths=[310, 155])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10263d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#d6dde5")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [table, Spacer(1, 14), Paragraph("Rapport généré par EESAG.", styles["Italic"])]
    doc.build(story)
    return response


def _safe_documents_count():
    try:
        from django.apps import apps
        from apps.documents.models import Document
        return Document.objects.filter(
            Q(eglise_expediteur__isnull=False) | Q(destinataires__isnull=False)
        ).distinct().count()
    except (LookupError, AttributeError, TypeError, FieldError, OperationalError):
        return 0


def _safe_count_model(app_label, model_name, **filters):
    try:
        from django.apps import apps
        model = apps.get_model(app_label, model_name)
        return model.objects.filter(**filters).count()
    except (LookupError, AttributeError, TypeError, FieldError, OperationalError):
        return 0


class StatistiquesNationalesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Le Coordinateur ne doit accéder à aucun tableau de bord.
        refus = _refuser_coordinateur_dashboard(request)
        if refus:
            return refu

    def get(self, request):
        if not _est_coordinateur(request.user) and not _est_national_general(request.user):
            return Response({
                "detail": "Les statistiques nationales sont réservées au Coordinateur ou au Bureau national général."
            }, status=403)

        eglises = Eglise.objects.all()
        membres_eglises = Utilisateur.objects.filter(actif=True, eglise__isnull=False)
        comptes_admin_eglises = Utilisateur.objects.filter(
            role__in=[Role.ADMIN_LOCAL, Role.PASTEUR],
            eglise__isnull=False,
        )
        operations = (
            Transaction.objects.all()
            if _est_coordinateur(request.user)
            else Transaction.objects.filter(eglise__isnull=True, bureau__isnull=True)
        )
        entrees = operations.exclude(type_transaction="SORTIE").aggregate(s=Sum("montant"))["s"] or 0
        sorties = operations.filter(type_transaction="SORTIE").aggregate(s=Sum("montant"))["s"] or 0

        # Six derniers mois, y compris les mois à zéro.
        today = timezone.localdate()
        first_month = today.replace(day=1)
        month_keys = []
        year, month = first_month.year, first_month.month
        for _ in range(5, -1, -1):
            m = month - _
            y = year
            while m <= 0:
                m += 12
                y -= 1
            month_keys.append((y, m))

        monthly_qs = (
            eglises.annotate(mois=TruncMonth("date_enregistrement_systeme"))
            .values("mois")
            .annotate(
                total=Count("id"),
                actives=Count("id", filter=Q(plateforme_active=True)),
            )
            .order_by("mois")
        )
        monthly_map = {
            (row["mois"].year, row["mois"].month): row
            for row in monthly_qs
            if row.get("mois")
        }
        evolution_eglises = []
        for y, m in month_keys:
            row = monthly_map.get((y, m), {})
            label = date(y, m, 1).strftime("%b")
            evolution_eglises.append({
                "mois": f"{y}-{m:02d}",
                "mois_label": label,
                "total": row.get("total", 0),
                "actives": row.get("actives", 0),
            })

        top_eglises = list(
            eglises.filter(utilisateurs__actif=True)
            .values("id", "nom")
            .annotate(nb=Count("utilisateurs", filter=Q(utilisateurs__actif=True)))
            .order_by("-nb", "nom")[:20]
        )
        # Garder la forme historique attendue par le frontend.
        membres_par_eglise_top20 = [
            {"eglise__nom": row["nom"], "nb": row["nb"]} for row in top_eglises
        ]

        bureau_national = list(
            Utilisateur.objects.filter(
                role__in=ROLES_BUREAU_NATIONAL,
                eglise__isnull=True,
            ).order_by("nom", "prenom").values(
                "id", "nom", "prenom", "fonction_bureau_national", "role", "actif"
            )[:20]
        )
        role_labels = dict(Role.choices)
        for item in bureau_national:
            item["role_libelle"] = role_labels.get(item["role"], item["role"])

        return Response({
            "scope": "GLOBAL" if _est_coordinateur(request.user) else "NATIONAL",
            "nombre_eglises": eglises.count(),
            "nombre_eglises_actives": eglises.filter(statut="ACTIVE", plateforme_active=True).count(),
            "eglises_a_activer": eglises.filter(plateforme_active=False).count(),
            "nombre_religions": Religion.objects.count(),
            "repartition_membres": _repartition_membres(membres_eglises),
            "eglises_par_region": list(
                eglises.values("region__nom").annotate(nb_eglises=Count("id")).order_by("-nb_eglises")
            ),
            "membres_par_eglise_top20": membres_par_eglise_top20,
            "evolution_eglises": evolution_eglises,
            "comptes_admin_eglises": comptes_admin_eglises.count(),
            "comptes_en_attente": comptes_admin_eglises.filter(actif=False).count(),
            "departements": Departement.objects.count(),
            "annexes": sum(eglise.annexes.count() for eglise in eglises),
            # Document est lié à une église via eglise_expediteur (pas eglise).
            # On compte aussi les documents reçus par au moins une église.
            "documents": _safe_documents_count(),
            "bureau_national_total": Utilisateur.objects.filter(
                role__in=ROLES_BUREAU_NATIONAL, eglise__isnull=True
            ).count(),
            "bureau_national": bureau_national,
            "notifications": _safe_count_model("notifications", "Notification", destinataire=request.user),
            "finance": {
                "entrees": entrees,
                "sorties": sorties,
                "solde": entrees - sorties,
                "transactions": operations.count(),
            },
        })


class StatistiquesEgliseView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, eglise_id):
        if not _est_coordinateur(request.user) and request.user.eglise_id != eglise_id:
            return Response({"detail": "Accès refusé : cette église ne fait pas partie de votre espace."}, status=403)
        eglise = Eglise.objects.filter(pk=eglise_id).first()
        if not eglise:
            return Response({"detail": "Église introuvable."}, status=404)
        membres = Utilisateur.objects.filter(eglise=eglise, actif=True)
        # Les départements sont actuellement un référentiel partagé. Pour
        # l'espace d'une église, on compte uniquement ceux effectivement
        # utilisés par les membres de cette église. Cela évite l'ancien appel
        # eglise.departements qui n'existe pas dans le modèle actuel.
        nombre_departements = (
            membres.exclude(departement_id__isnull=True)
            .values("departement_id")
            .distinct()
            .count()
        )
        return Response({
            "eglise": {"id": eglise.id, "nom": eglise.nom, "code": eglise.code},
            "repartition_membres": _repartition_membres(membres),
            "nombre_departements": nombre_departements,
        })


class RapportApercuView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            debut, fin = _periode(request)
            data = _data_rapport(
                request.user, debut, fin,
                request.query_params.get("membres", "1") == "1",
                request.query_params.get("finances", "1") == "1",
                request.query_params.get("projets", "1") == "1",
            )
        except (ValueError, PermissionError) as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(data)


class RapportEgliseView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, eglise_id):
        if not (_est_coordinateur(request.user) or (request.user.role in [Role.PASTEUR, Role.ADMIN_LOCAL] and request.user.eglise_id == eglise_id)):
            return Response({"detail": "Une église ne peut produire que son propre rapport."}, status=403)
        eglise = Eglise.objects.get(pk=eglise_id)
        debut, fin = _periode(request)
        data = _data_rapport(request.user, debut, fin, request.query_params.get("membres", "1") == "1", request.query_params.get("finances", "1") == "1", request.query_params.get("projets", "1") == "1", forced_scope={"type": "EGLISE", "eglise_id": eglise_id, "label": eglise.nom})
        if data["scope"]["type"] == "GLOBAL":
            # Le Coordinateur peut demander un rapport précis d'une église en lecture supervisée.
            membres = Utilisateur.objects.filter(eglise_id=eglise_id, actif=True)
            operations = Transaction.objects.filter(eglise_id=eglise_id, date_transaction__range=(debut, fin))
            projets = Projet.objects.filter(eglise_id=eglise_id)
            entrees = operations.exclude(type_transaction="SORTIE").aggregate(v=Sum("montant"))["v"] or 0
            sorties = operations.filter(type_transaction="SORTIE").aggregate(v=Sum("montant"))["v"] or 0
            data["label"] = eglise.nom; data["membres"] = _repartition_membres(membres) if request.query_params.get("membres", "1") == "1" else None
            data["finances"] = {"operations": operations.count(), "entrees": entrees, "sorties": sorties, "solde": entrees-sorties} if request.query_params.get("finances", "1") == "1" else None
            data["projets"] = {"nombre": projets.count(), "budget_prevu": sum((p.budget_prevu for p in projets), 0), "budget_utilise": sum((p.budget_utilise for p in projets), 0)} if request.query_params.get("projets", "1") == "1" else None
        return _rapport_pdf(data)


class RapportNationalView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not (_est_coordinateur(request.user) or _est_national_general(request.user)):
            return Response({"detail": "Le rapport national général est réservé au Coordinateur ou au Bureau national général."}, status=403)
        try:
            debut, fin = _periode(request)
            return _rapport_pdf(_data_rapport(request.user, debut, fin, request.query_params.get("membres", "1") == "1", request.query_params.get("finances", "1") == "1", request.query_params.get("projets", "1") == "1"))
        except (ValueError, PermissionError) as exc:
            return Response({"detail": str(exc)}, status=400)


class RapportBureauView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, bureau_id):
        bureau = Bureau.objects.filter(pk=bureau_id, actif=True).first()
        if not bureau:
            return Response({"detail": "Bureau introuvable."}, status=404)
        if not (_est_coordinateur(request.user) or BureauAdministrateur.objects.filter(utilisateur=request.user, bureau=bureau, actif=True, peut_gerer_rapports=True).exists()):
            return Response({"detail": "Vous ne pouvez produire que le rapport de votre propre bureau."}, status=403)
        try:
            debut, fin = _periode(request)
            return _rapport_pdf(_data_rapport(request.user, debut, fin, request.query_params.get("membres", "1") == "1", request.query_params.get("finances", "1") == "1", request.query_params.get("projets", "1") == "1", forced_scope={"type": "BUREAU", "bureau_id": bureau_id, "label": bureau.nom}))
        except (ValueError, PermissionError) as exc:
            return Response({"detail": str(exc)}, status=400)
