from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_accueil(request):
    return JsonResponse({
        "application": "EESAG",
        "message": "API EESAG opérationnelle",
        "status": "ok",
    })

urlpatterns = [
    path("admin/", admin.site.urls),
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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
