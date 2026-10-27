from django.contrib.admin import AdminSite

from apps.core.admin_scopes import is_national_general

from apps.churches.models import Eglise, Departement
from apps.churches.admin import EgliseAdmin, DepartementAdmin

from apps.accounts.models import Utilisateur
from apps.accounts.admin import UtilisateurAdmin


class EESAGNationalAdminSite(AdminSite):
    site_header = "EESAG — Administration du Bureau national"
    site_title = "EESAG Bureau national"
    index_title = "Gestion nationale des églises"

    def has_permission(self, request):
        return (
            request.user.is_active
            and request.user.is_staff
            and is_national_general(request.user)
        )


admin_national_site = EESAGNationalAdminSite(
    name="admin_national"
)


# ============================================================
# ENREGISTREMENT DES MODÈLES SUR L'ADMIN NATIONAL
# ============================================================

admin_national_site.register(
    Eglise,
    EgliseAdmin,
)

admin_national_site.register(
    Departement,
    DepartementAdmin,
)

admin_national_site.register(
    Utilisateur,
    UtilisateurAdmin,
)