from django.shortcuts import redirect
from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import include, path
from django.views.static import serve

from apps.core.admin_national import admin_national_site


FRONTEND_DIST = Path(settings.BASE_DIR).parent / "frontend" / "dist"


def api_accueil(request):
    return JsonResponse({
        "application": "EESAG",
        "message": "API EESAG opérationnelle",
        "status": "ok",
    })


def frontend_systeme(request):
    index_file = FRONTEND_DIST / "index.html"

    if not index_file.is_file():
        return HttpResponse(
            "Frontend EESAG introuvable. Exécutez npm run build dans frontend.",
            status=503,
            content_type="text/plain; charset=utf-8",
        )

    return HttpResponse(
        index_file.read_text(encoding="utf-8"),
        content_type="text/html; charset=utf-8",
    )


# Routes API et administrations
urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin-national/", admin_national_site.urls),

    path("api/", include("apps.accounts.urls")),
    path("api/geo/", include("apps.geo.urls")),
    path("api/", include("apps.churches.urls")),
    path("api/", include("apps.members.urls")),
    path("api/", include("apps.letters.urls")),
    path("api/", include("apps.documents.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/finance/", include("apps.finance.urls")),
    path("api/stats/", include("apps.dashboard.urls")),
    path("api/ia/", include("apps.ia_assistant.urls")),
    path("api/", include("apps.meetings.urls")),
    path("api/", include("apps.bureaux.urls")),
    path("api/systeme/", include("apps.core.urls")),

    path("", api_accueil, name="api-accueil"),
]

# Fichiers du frontend React en développement
if settings.DEBUG:
    urlpatterns += [
    path("systeme", lambda request: redirect("/connexion"), name="systeme-retire"),
    path("systeme/", lambda request: redirect("/connexion"), name="systeme-retire-slash"),
        path(
            "assets/<path:path>",
            serve,
            {"document_root": FRONTEND_DIST / "assets"},
            name="frontend-assets",
        ),
        path(
            "favicon.ico",
            serve,
            {"document_root": FRONTEND_DIST, "path": "favicon.ico"},
            name="frontend-favicon",
        ),
    ]

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

# Pages React : après les routes API
urlpatterns += [
    path("connexion", frontend_systeme, name="frontend-connexion"),
    path("connexion/", frontend_systeme, name="frontend-connexion-slash"),
    path("inscription", frontend_systeme, name="frontend-inscription"),
    path("inscription/", frontend_systeme, name="frontend-inscription-slash"),
]
